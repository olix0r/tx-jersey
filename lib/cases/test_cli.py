import os, sys

from twisted.python import reflect
from twisted.internet import reactor
from twisted.internet.defer import Deferred, DeferredList, inlineCallbacks
from twisted.trial.unittest import TestCase

from jersey import cli, log
from jersey.cases.base import TestBase



class ProgramTestBase(TestBase):

    timeout = 2

    def setUp(self):
        self.program = self.id()



class OptionsCase(ProgramTestBase, TestCase):

    expectedUsageLines = (
        "Options:",
            "--version",
            "--help     Display this help and exit.",
        )


    def setUp(self):
        ProgramTestBase.setUp(self)
        self.expectedSynopsis = "Usage: {0.program} [options]".format(self)


    def test_getSynopsis(self):
        opts = cli.Options(self.program)
        synopsis = opts.getSynopsis()
        self.assertEquals(self.expectedSynopsis, synopsis)


    def test_program(self):
        opts = cli.Options(self.program)
        self.assertEquals(self.program, opts.program)


    def test_program_sysargv(self):
        opts = cli.Options()

        _sys_argv = sys.argv[:]
        sys.argv = ["/path/to/{0.program}".format(self), ]
        try:
            self.assertEquals(self.program, opts.program)
        finally:
            sys.argv = _sys_argv


    def test_getUsage(self):
        usage = cli.Options(self.program).getUsage()
        for expected, got in zip(self.expectedUsageLines, usage.splitlines()):
            self.assertEquals(expected, got.strip())


    def test_parseIP(self):
        for badIp in ("10", "one.two.three.four"):
            from twisted.python import usage
            self.assertRaises(usage.error, cli.Options.parseIP, badIp)



class TestCommandRunnerBase(object):

    class loggerFactory(object):
        def __init__(self, *args, **kw):
            pass

        def start(self, app):
            pass

        def stop(self):
            pass


    def startReactor(self):
        pass

    def stopReactor(self):
        pass



class ConfigTestBase(ProgramTestBase):

    optionsClass = cli.Options

    def setUp(self):
        ProgramTestBase.setUp(self)
        self.config = self.buildOptions()


    def buildOptions(self):
        assert self.optionsClass and self.program
        return self.optionsClass(self.program)


class RunnerTestBase(ConfigTestBase):

    runnerClass = None

    def buildRunner(self, *args, **kw):
        assert self.runnerClass is not None
        assert self.config is not None
        return self.runnerClass(self.program, self.config, *args, **kw)



class SensorCommand(cli.Command):

    started = False
    executed = False

    def startService(self):
        cli.Command.startService(self)
        self.started = True

    def execute(self):
        log.debug("Executing {0!r}".format(self))
        self.executed = True


class TrueCommand(SensorCommand):
    def execute(self):
        SensorCommand.execute(self)
        return True

class DeferredCommand(SensorCommand):
    def execute(self):
        SensorCommand.execute(self)
        d = Deferred()
        reactor.callLater(0, d.callback, True)
        return d

class ExitCommand(SensorCommand):

    def __init__(self, config, exitValue=os.EX_OK):
        cli.Command.__init__(self, config)
        self.exitValue = exitValue

    def execute(self):
        raise SystemExit(self.exitValue)


class ExoticException(Exception):
    pass

class ExceptionCommand(SensorCommand):
    def execute(self):
        SensorCommand.execute(self)
        raise ExoticException()



class CommandCases(ConfigTestBase, TestCase):

    def setUp(self):
        ConfigTestBase.setUp(self)
        self.config = self.buildOptions()


    def test_abstract(self):
        """Test a static runner that with a command that returns a value.
        """
        cmd = cli.Command(self.config)
        cmd._execute()
        return self.assertFailure(cmd.exit, NotImplementedError)


    @inlineCallbacks
    def test_startService(self):
        """Test a static runner that with a command that returns a value.
        """
        cmd = SensorCommand(self.config)
        cmd.startService()
        yield cmd.exit
        self.assertTrue(cmd.executed)


    def test_execute_return_value(self):
        """Test a static runner that with a command that returns a value.
        """
        cmd = TrueCommand(self.config)
        cmd.exit.addCallback(self.assertTrue)

        cmd._execute()
        return cmd.exit


    @inlineCallbacks
    def test_execute_return_deferred(self):
        """Test a static runner that with a command that returns a value.
        """
        cmd = DeferredCommand(self.config)
        cmd._execute()
        exit = yield cmd.exit
        self.assertTrue(exit)


    def test_execute_exception(self):
        cmd = ExceptionCommand(self.config)
        cmd._execute()
        return self.assertFailure(cmd.exit, ExoticException)



class CommandRunnerCases(RunnerTestBase, TestCase):

    commandClass = SensorCommand

    class runnerClass(TestCommandRunnerBase, cli.CommandRunner):
        pass


    def setUp(self):
        RunnerTestBase.setUp(self)
        self.cmd = self.commandClass(self.config)
        self.runner = self.buildRunner(self.cmd)


    def test_build(self):
        cmd = self.runner.buildCommand()
        self.assertIsInstance(cmd, self.commandClass)
        self.assertIdentical(self.cmd, cmd)


    @inlineCallbacks
    def test_run(self):
        self.assertFalse(self.cmd.started)
        self.runner.run()
        yield self.cmd.exit
        self.assertTrue(self.cmd.started)
        self.assertTrue(self.cmd.executed)



class CommandRunnerExitCases(RunnerTestBase, TestCase):

    class runnerClass(TestCommandRunnerBase, cli.CommandRunner):
        pass


    @inlineCallbacks
    def test_run_SystemExit(self):
        exVal = os.EX_SOFTWARE
        self.cmd = ExitCommand(self.config, exVal)
        self.runner = self.buildRunner(self.cmd)

        self.runner.run()
        try:
            yield self.cmd.exit
        except SystemExit:
            pass
        self.assertEquals(exVal, self.runner.exitValue)



    def test_run(self):
        self.cmd = SensorCommand(self.config)
        self.runner = self.buildRunner(self.cmd)
        self.assertFalse(self.cmd.started)
        self.runner.run()
        self.assertEquals(self.runner.exitValue, os.EX_OK)


class PluggableTestBase(ProgramTestBase):

    commandPackageName = "animal_command_plugins"
    class optionsClass(cli.PluggableOptions):
        longdesc = ""

    plugins = {
    "__init__": "",

    "monkey": """\
from twisted.plugin import IPlugin
from zope.interface import implements
from jersey.cli import CommandFactory, Command, Options

class MonkeyOptions(Options):
    optFlags = [("nana", "n", "I like nanas!"), ]

class MonkeyCommand(Command):
    def execute(self):
        return \"eep! eep!\"
        
class MonkeyPlugin(CommandFactory):
    implements(IPlugin)
    command = MonkeyCommand
    options = MonkeyOptions

    name = \"monkey\"
    shortcut = \"m\"
    description = \"My name is Bingo!\"
    
monkeyPlugin = MonkeyPlugin()
""",

    "frog": """\
from twisted.plugin import IPlugin
from zope.interface import implements
from jersey.cli import CommandFactory, Command, Options

class FrogCommand(Command):
    def execute(self):
        return \"ribbit! ribbit!\"
        
class FrogPlugin(CommandFactory):
    implements(IPlugin)
    command = FrogCommand
    options = Options

    name = \"frog\"
    shortcut = \"f\"
    description = \"Quoi?\"

frogPlugin = FrogPlugin()
""",
    }


    def installPlugins(self):
        # Prepare plugin directory
        rootDir = self.makeTestRoot()
        pluginDir = os.path.join(rootDir, self.commandPackageName)
        os.makedirs(pluginDir)

        # Write plugins files
        for name, content in self.plugins.iteritems():
            name = "{0}.py".format(name)
            path = os.path.join(pluginDir, name)
            with open(path, "w") as p:
                p.write(content)
        
        # Configure sys.path
        self._sys_path = sys.path[:]
        sys.path.append(os.path.abspath(rootDir))
        log.msg("System path altered to be: {0!r}".format(sys.path))


    def buildOptions(self):
        assert self.program is not None

        config = self.optionsClass(self.program)

        config.commandPackage = reflect.namedModule(self.commandPackageName)
        log.msg("Loaded the plugin package: {0.commandPackage}".format(config))

        return config



class PluggableOptionsCase(PluggableTestBase, TestCase):

    expectedUsageLines = (
        "Options:",
            "--version",
            "--help     Display this help and exit.",
        "Commands:",
            "monkey      My name is Bingo!",
            "frog        Quoi?",
        )


    def setUp(self):
        """Install plugins."""
        ProgramTestBase.setUp(self)
        self.expectedSynopsis = "Usage: {0} [options]".format(self.program)

        self.installPlugins()
        self.options = self.buildOptions()


    def tearDown(self):
        sys.path = self._sys_path


    def test_commandsUsage(self):
        self.assertEquals(self.expectedSynopsis, self.options.getSynopsis())

        for name in self.plugins.iterkeys():
            if not name.startswith("_"):
                plugin = self.options.getCommand(name)
                self.assertNotEquals(None, plugin)
                self.assertEquals(name, plugin.name)
                self.assertEquals(name[0], plugin.shortcut)
                self.assertTrue(plugin.description)

        self.assertRaises(KeyError, self.options.getCommand, "donkey")

        usage = self.options.getUsage()
        log.debug("USAGE: {0!r}".format(usage))

        usageLines = usage.splitlines()
        self.assertEquals(len(self.expectedUsageLines), len(usageLines),
                "Unexpected usage statement\n{0!r}".format("\n".join(usageLines)))
        for expected, got in zip(self.expectedUsageLines, usageLines):
            self.assertEquals(expected, got.strip())



class PluggableRunnerCase(PluggableTestBase, RunnerTestBase, TestCase):

    class optionsClass(cli.PluggableOptions):
        defaultSubCommand = "monkey"

    class runnerClass(TestCommandRunnerBase, cli.PluggableCommandRunner):
        def buildCommand(self):
            if not hasattr(self, "_command"):
                self._command = cli.PluggableCommandRunner.buildCommand(self)
            return self._command


    def setUp(self):
        self.program = self.id()
        self.installPlugins()
        self.config = self.buildOptions()
        self.runner = self.buildRunner()


    def test_default(self):
        self.assertNotEquals(None, self.config.defaultSubCommand)
        self.config.parseOptions([])
        command = self.runner.buildCommand()
        return self.assertCommandIsMonkey(command)


    def test_monkey(self):
        self.config.parseOptions(["monkey"])
        command = self.runner.buildCommand()
        return self.assertCommandIsMonkey(command)


    def assertCommandIsMonkey(self, command):
        self.assertImplements(cli.ICommand, command)

        def cb_assertMonkeySaysEep(says):
            self.assertEquals("eep! eep!", says)
            return says
        command.exit.addCallback(cb_assertMonkeySaysEep)

        self.runner.run()
        return command.exit


    def test_frog(self):
        self.config.parseOptions(["frog"])

        command = self.runner.buildCommand()
        self.assertImplements(cli.ICommand, command)

        def cb_assertFrogSaysRibbit(says):
            self.assertEquals("ribbit! ribbit!", says)
            return says
        command.exit.addCallback(cb_assertFrogSaysRibbit)

        self.runner.run()
        return command.exit



class _FakeObserver(object):

    def __init__(self):
        self.loggedEvents = list()

    def emit(self, event):
        self.loggedEvents.append(event)


class LoggerCases(ProgramTestBase, TestCase):

    def setUp(self):
        ProgramTestBase.setUp(self)

        self.config = config = cli.Options(self.program)

        patcher = self.patch(cli.Logger, "_getLogObserver", self._getObserver)
        self.observer = _FakeObserver()
        self.logger = cli.Logger(config)

        from twisted.application.service import Application
        self.app = Application(self.program)

        self.openedMsg = "Log opened."
        self.initMsg = "Starting logging for {0.program}".format(self)


    def _getObserver(self):
        return self.observer.emit


    def test_start(self):
        self.logger.start(self.app)

        self.assertEquals(self.observer.emit, self.logger._observer)
        self.assertEquals(2, len(self.observer.loggedEvents))

        # XXX TODO implement startLogWithObserver without "Log opened." msg
        event = self.observer.loggedEvents[0]
        self.assertEquals((self.openedMsg,), event.get("message"))
        self.assertEquals(log.INFO, event.get("logLevel", log.INFO))

        event = self.observer.loggedEvents[1]
        self.assertEquals((self.initMsg,), event.get("message"))
        self.assertEquals(log.DEBUG, event.get("logLevel"))


