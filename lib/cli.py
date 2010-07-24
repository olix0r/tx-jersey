"""Command-Line Interface library"""

import os, sys

from twisted.application import app
from twisted.application.service import Application, MultiService, Service
from twisted.internet import reactor
from twisted.internet.defer import (Deferred, succeed, fail,
        inlineCallbacks, returnValue, maybeDeferred, gatherResults)
from twisted.plugin import getPlugins
from twisted.python import usage
from twisted.python.failure import Failure

from zope.interface import Attribute, Interface, implements

from jersey import log
from jersey.inet import IP


UsageError = usage.error



class ICommand(Interface):

    config = Attribute("Command options.")

    exit = Attribute("A Deferred called with the result of execute().")

    def execute():
        """Command execution method."""


class ICommandFactory(Interface):

    name = Attribute("Long command name")
    shortcut = Attribute("Short command name")
    description = Attribute("Command description")

    options = Attribute("Subclass of usage.Options")

    def buildCommand(config):
        """Build a Command."""



class Command(MultiService):
    """Abstract Command implementation.

    Subclasses must implement execute()
    """
    implements(ICommand)

    def __init__(self, config):
        MultiService.__init__(self)
        self.config = config
        self.exit = Deferred()

    @inlineCallbacks
    def startService(self):
        """Initiate execution."""
        Service.startService(self)
        ds = []
        for svc in self:
            log.debug("{0} starting service: {1}".format(self, svc))
            d = maybeDeferred(svc.startService)
            ds.append(d)
        yield gatherResults(ds)
        yield self._execute()

    def _execute(self):
        """Ensure that exit is called with the result of execute."""
        return maybeDeferred(self.execute).chainDeferred(self.exit)

    def execute(self):
        """Execute the command."""
        raise NotImplementedError("execute() must be implemented by subclass.")



class CommandFactory(object):
    """Abstract CommandFactory implementation.

    Plugin implementations can subclass this, providing only class-attribute
    values, to satisfy the ICommandFactory interface.
    """
    implements(ICommandFactory)

    command = None
    options = None

    name = None
    shortcut = None
    description = None

    def buildCommand(self, config, *args, **kw):
        assert self.command is not None
        return self.command(config, *args, **kw)



class Options(usage.Options):

    @staticmethod
    def parseIP(addr):
        """Wraps IP() to throw usage.error instead of ValueError."""
        try:
            return IP(str(addr))

        except ValueError:
            raise usage.error("Not an IP address", addr)

    
    def __init__(self, program=None):
        """Construct Options.
        
        Arguments:
          program --  The name of the program (used for printing usage).  If not
                      specified, sys.argv[0] is used.
        """
        usage.Options.__init__(self)
        self._program = program


    @property
    def program(self):
        """The name of the program."""
        return self._program or os.path.basename(sys.argv[0])


    def getSynopsis(self):
        """Use self.program to build the synopsis."""
        if self.parent is None:
            synopsis = "Usage: " + self.program
        else:
            synopsis = self.parent.getSynopsis() + " " + self.parent.subCommand

        if self.longOpt:
            synopsis += " [options]"

        return synopsis.rstrip()



class Logger(app.AppLogger):
    """CLI-oriented logger factory."""

    observerFactory = log.CLILogObserver

    def __init__(self, config):
        self.config = config

    def _getLogObserver(self):
        return self.observerFactory(self.config)

    def _initialLog(self):
        if hasattr(self.config, "program"):
            log.debug("Starting logging for {0.config.program}".format(self))

    def stop(self):
        if self._observer is not None:
            log.removeObserver(self._observer)
            self._observer = None



class AbstractCommandRunner(app.ApplicationRunner):
    """Configures an application"""

    loggerFactory = Logger

    def __init__(self, name, config):
        app.ApplicationRunner.__init__(self, config)
        self.name = name
        self.exitValue = os.EX_OK


    def createOrGetApplication(self):
        """Build the CLI by delegating control to a subcommand."""
        app = Application(self.name)

        cmd = self.buildCommand()
        cmd.setServiceParent(app)

        cmd.exit.addCallbacks(self.cb_setExitValue, self.eb_setExitValue)
        cmd.exit.addBoth(self._completed)

        return app


    def _completed(self, value):
        """Called when command execution is complete.  Stops the reactor.

        Attributes:
            value --  The return value of command.execute, or a Failure.
        Returns:
            value
        """
        log.debug("Completed execution: {0}".format(value))
        log.debug("Exit value: {0}".format(self.exitValue))
        self.stopReactor()
        return value


    def cb_setExitValue(self, value):
        self.exitValue = value or self.exitValue
        log.debug("Setting exit value to {0}".format(self.exitValue))
        return value

    def eb_setExitValue(self, reason):
        if reason.check(SystemExit):
            self.exitValue = reason.value.code
        else:
            self.exitValue = os.EX_SOFTWARE

        log.debug("Setting exit value to {0} from {1}".format(
                self.exitValue, reason.getErrorMessage()))
        return reason


    def preApplication(self):
        """No pre-application steps are required."""
        pass


    def buildCommand(self):
        """Build a command to execute.

        Must be overridden by a subclass.
        """
        raise NotImplementedError()


    def postApplication(self):
        """Run the application."""
        self.startApplication()
        self.startReactor()

    def startApplication(self):
        """Start the application and setup shutdown hooks."""
        app.startApplication(self.application, False)


    def startReactor(self):
        """Start Twisted's event loop without complex setup."""
        reactor.run()

    def stopReactor(self):
        """Stop the Twisted reactor."""
        reactor.stop()


class CommandRunner(AbstractCommandRunner):
    """Run a command specified at construction-time."""

    def __init__(self, name, config, command):
        AbstractCommandRunner.__init__(self, name, config)
        self._command = command

    def buildCommand(self):
        return self._command



class PluggableOptions(Options):
    """Options handler supporting pluggable subcommands.

    Members:
        commandInterface --  The Interface class that command plugins implement
        commandPackage --  The Python package where commands are loaded from.
    """

    commandInterface = ICommandFactory
    commandPackage = None

    def __init__(self, *args, **kw):
        Options.__init__(self, *args, **kw)
        self._commands = dict()


    @property
    def subCommands(self):
        """Supported sub-commands."""
        for cmd in self._cacheCommands():
            yield (cmd.name, cmd.shortcut, cmd.options, cmd.description)

    def getCommand(self, name):
        """Get a given command, or raise a KeyError."""
        self._cacheCommands()
        return self._commands[name]

    def _cacheCommands(self):
        """Populate self._commands by loading plugins."""
        if len(self._commands) == 0:
            cmdIface, cmdPkg = self.commandInterface, self.commandPackage
            if cmdIface and cmdPkg:
                for cmd in getPlugins(cmdIface, cmdPkg):
                    log.msg("Loaded command: {0!r}".format(cmd))
                    self._commands[cmd.name] = cmd

        return self._commands.itervalues()



class PluggableCommandRunner(AbstractCommandRunner):
    """Run a a pluggable command as loaded by an instance of PluggableOptions."""

    def buildCommand(self):
        """Build the command based on PluggableOptions."""
        plg = self.config.getCommand(self.config.subCommand)
        return plg.buildCommand(self.config.subOptions)



