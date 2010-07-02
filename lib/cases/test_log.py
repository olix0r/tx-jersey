import errno, os, sys

from twisted.internet import reactor
from twisted.internet.defer import Deferred, DeferredList, inlineCallbacks
from twisted.trial.unittest import TestCase

import jersey.log, jersey.cli

from jersey.cases.base import TestBase


class LogLevelTestBase(TestBase):

    knownLevels = ("TRACE", "DEBUG", "INFO", "WARN", "ERROR")


class ModuleCases(LogLevelTestBase, TestCase):

    def test_wraps_twisted_log(self):
        import twisted.python.log
        for attr in dir(twisted.python.log):
            if not attr.startswith("_"):
                self.assertIn(attr, jersey.log.__dict__)

    def test_has_helpers(self):
        for name in self.knownLevels:
            self.assertIn(name.lower(), jersey.log.__dict__)
            self.assertIn(name.upper(), jersey.log.__dict__)



class MsgHelperCases(LogLevelTestBase, TestCase):

    def setUp(self):
        self.patcher = self.patch(jersey.log, "msg", self._test_msg)

        self.expectedKw = dict()
        self.msgLogged = False


    def tearDown(self):
        self.patcher.restore()


    def _test_msg(self, *args, **kw):
        for k, v in self.expectedKw.iteritems():
            self.assertIn(k, kw)
            self.assertEquals(v, kw[k])

        self.msgLogged = True


    def _test_helper(self, level):
        self.expectedKw = {"logLevel": getattr(jersey.log, level.upper()), }

        helper = getattr(jersey.log, level.lower())

        self.assertFalse(self.msgLogged)
        helper("oink")
        self.assertTrue(self.msgLogged)


    def test_trace(self):
        self._test_helper("trace")

    def test_debug(self):
        self._test_helper("debug")

    def test_info(self):
        self._test_helper("info")

    def test_warn(self):
        self._test_helper("warn")

    def test_error(self):
        self._test_helper("error")



class CLIObserverTestBase(LogLevelTestBase):

    cliOptionsClass = jersey.cli.Options
    cliObserverClass = jersey.log.CLILogObserver

    def setUp(self):
        self.program = self.id()
        self.config = self.cliOptionsClass(self.program)
        self.observer = self.cliObserverClass(self.config)



class InitializeCLIObserverCases(CLIObserverTestBase, TestCase):

    def test_initializeEvent(self):
        event = {"message": ("oink",)}
        self.observer._initializeEvent(event)

        self.assertEquals(self.observer.defaultLogLevel, event["logLevel"])
        self.assertEquals(False, event["printed"])
        self.assertEquals(self.program, event["program"])
        self.assertNotIn("subCommand", event)
        self.assertEquals("oink", event["text"])


    def test_initializeEvent_isError_printed(self):
        event = {"message": ("OINK!",), "isError": True, "printed": True, }
        self.observer._initializeEvent(event)

        self.assertEquals(jersey.log.ERROR, event["logLevel"])
        self.assertEquals(True, event["printed"])
        self.assertNotIn("subCommand", event)
        self.assertEquals("OINK!", event["text"])


    def test_initializeEvent_subCommand_WARN(self):
        event = {"message": ("Oink?",), "logLevel": jersey.log.WARN, }
        self.config.subCommand = "wallow"
        self.observer._initializeEvent(event)

        self.assertEquals(jersey.log.WARN, event["logLevel"])
        self.assertEquals(False, event["printed"])
        self.assertEquals("wallow", event["subCommand"])
        self.assertEquals("Oink?", event["text"])



class FormatCLIObserverCases(CLIObserverTestBase, TestCase):

    def setUp(self):
        CLIObserverTestBase.setUp(self)

        self.oink = "Oink"
        self.event = {"message": (self.oink,), }
        self.observer._initializeEvent(self.event)


    def test_formatText_printed(self):
        self.event["printed"] = True
        text = self.observer._formatText(self.event)
        self.assertEquals(self.oink+"\n", text)


    def test_formatText_info(self):
        self.event["logLevel"] = jersey.log.INFO
        text = self.observer._formatText(self.event)
        self.assertEquals("{0.program}: INFO: {0.oink}\n".format(self), text)


    def test_formatText_subCommand_info(self):
        self.event["logLevel"] = jersey.log.INFO
        self.config.subCommand = "wallow"
        self.observer._initializeEvent(self.event)  # reinit OK

        text = self.observer._formatText(self.event)
        expectedFmt = "{0.program}: {0.config.subCommand}: INFO: {0.oink}\n"
        self.assertEquals(expectedFmt.format(self), text)


    def test_formatText_unnamedLevel(self):
        self.event["logLevel"] = jersey.log.INFO + 3
        text = self.observer._formatText(self.event)
        self.assertEquals("{0.program}: {0.oink}\n".format(self), text)


    def test_formatText_multiLineMessage(self):
        self.event["message"] = ("oink.\nOink.\nOINK!\n",)
        self.config.subCommand = "wallow"
        self.observer._initializeEvent(self.event)

        text = self.observer._formatText(self.event)
        expectedFmt = "{0.program}: {0.config.subCommand}: INFO: oink.\n" \
                      "{0.program}: {0.config.subCommand}: INFO: Oink.\n" \
                      "{0.program}: {0.config.subCommand}: INFO: OINK!\n" \
                      "{0.program}: {0.config.subCommand}: INFO: \n"
        self.assertEquals(expectedFmt.format(self), text)


    def test_formatText_multiArgMessage(self):
        self.event["message"] = ("oink.", "Oink.", "OINK!",)
        self.event["logLevel"] = jersey.log.WARN
        self.observer._initializeEvent(self.event)

        text = self.observer._formatText(self.event)
        expectedFmt = "{0.program}: WARN: oink. Oink. OINK!\n"
        self.assertEquals(expectedFmt.format(self), text)



class GetStreamCLIObserverCases(CLIObserverTestBase, TestCase):

    def test_getStream_TRACE(self):
        e = {"logLevel": jersey.log.TRACE}
        self.assertEquals(self.observer._out, self.observer._getStream(e))

    def test_getStream_DEBUG(self):
        e = {"logLevel": jersey.log.DEBUG}
        self.assertEquals(self.observer._out, self.observer._getStream(e))

    def test_getStream_INFO(self):
        e = {"logLevel": jersey.log.INFO}
        self.assertEquals(self.observer._out, self.observer._getStream(e))

    def test_getStream_WARN(self):
        e = {"logLevel": jersey.log.WARN}
        self.assertEquals(self.observer._out, self.observer._getStream(e))

    def test_getStream_ERROR(self):
        e = {"logLevel": jersey.log.ERROR}
        self.assertEquals(self.observer._err, self.observer._getStream(e))

    def test_getStream_ERROR_plus_10(self):
        e = {"logLevel": jersey.log.ERROR+10}
        self.assertEquals(self.observer._err, self.observer._getStream(e))



class LogworthinessCLIObserverCases(CLIObserverTestBase, TestCase):

    class cliOptionsClass(CLIObserverTestBase.cliOptionsClass):
        logLevel = jersey.log.WARN

    def setUp(self):
        CLIObserverTestBase.setUp(self)
        self.event = {"message": ("squeel",), }
        self.observer._initializeEvent(self.event)


    def _test_isLogworthy_level(self, level):
        self.event["logLevel"] = level

        if level < self.cliOptionsClass.logLevel:
            self.assertFalse(self.observer._isLogworthy(self.event))
            self.observer.thresholdLogLevel = level - 10
            self.assertTrue(self.observer._isLogworthy(self.event))

        else:
            self.assertTrue(self.observer._isLogworthy(self.event))
            self.observer.thresholdLogLevel = level + 10
            self.assertFalse(self.observer._isLogworthy(self.event))


    def test_isLogworthy_TRACE(self):
        self._test_isLogworthy_level(jersey.log.TRACE)

    def test_isLogworthy_DEBUG(self):
        self._test_isLogworthy_level(jersey.log.DEBUG)

    def test_isLogworthy_INFO(self):
        self._test_isLogworthy_level(jersey.log.INFO)

    def test_isLogworthy_WARN(self):
        self._test_isLogworthy_level(jersey.log.WARN)

    def test_isLogworthy_ERROR(self):
        self._test_isLogworthy_level(jersey.log.ERROR)


    def test_isLogworthy_printed(self):
        # Disable normal logs
        self.observer.thresholdLogLevel = jersey.log.ERROR
        assert jersey.log.ERROR > self.event["logLevel"]

        self.event["printed"] = True
        self.assertTrue(self.observer._isLogworthy(self.event))


    def test_isLogworthy_noText(self):
        self.event["message"] = ("",)
        self.observer.thresholdLogLevel = jersey.log.ERROR
        self.assertFalse(self.observer._isLogworthy(self.event))


    def test_isLogworthy_printed_noText(self):
        self.event.update({
            "message": ("",),
            "isError": False,
            "printed": True,
            })
        self.observer.thresholdLogLevel = jersey.log.ERROR
        self.observer._initializeEvent(self.event)

        self.assertTrue(self.observer._isLogworthy(self.event))
        self.assertTrue(self.observer.thresholdLogLevel > self.event["logLevel"])



class _StreamSensor(object):
    """Like a file handle, but fake."""

    def __init__(self):
        self.interruptWrite = False
        self.interruptFlush = False
        self.writeInterrupted = False
        self.flushInterrupted = False
        self._wrote = ""
        self.wrote = ""

    def write(self, data):
        if self.interruptWrite:
            self.interruptWrite = False
            self.writeInterrupted = True
            raise IOError(errno.EINTR)
        self._wrote += data

    def flush(self):
        if self.interruptFlush:
            self.interruptFlush = False
            self.flushInterrupted = True
            raise IOError(errno.EINTR)
        self.wrote += self._wrote
        self._wrote = ""


class CLIObserverEmitCases(CLIObserverTestBase, TestCase):
    """Tests CLILogObserver.emit(event) with false output descriptors.
    """

    def setUp(self):
        self.stream = _StreamSensor()
        self.patcher = self.patch(self.cliObserverClass, "_getStream",
                self._getStream)
        CLIObserverTestBase.setUp(self)

        self.wokka = "Wokka wokka wokka!"
        self.event = {"message": (self.wokka,), }


    def tearDown(self):
        self.patcher.restore()

    def _getStream(self, event):
        return self.stream


    def test_emit(self):
        self.observer.thresholdLogLevel = self.event["logLevel"] = jersey.log.INFO
        self.observer.emit(self.event)
        self.assertEquals("{0.program}: INFO: {0.wokka}\n".format(self),
                self.stream.wrote)


    def test_emit_printed(self):
        self.event["printed"] = True
        self.observer.emit(self.event)
        self.assertEquals(self.wokka+"\n", self.stream.wrote)


    def test_emit_noMessage_KeyError(self):
        del self.event["message"]
        self.assertRaises(KeyError, self.observer.emit, self.event)


    def test_emit_suppressed(self):
        self.event["logLevel"] = self.observer.thresholdLogLevel - 10
        self.observer.emit(self.event)
        self.assertEquals(0, len(self.stream.wrote))


    def test_emit_interrupted(self):
        self.stream.interruptWrite = True
        self.stream.interruptFlush = True

        self.event["printed"] = True
        self.observer.emit(self.event)

        self.assertTrue(self.stream.writeInterrupted)
        self.assertTrue(self.stream.flushInterrupted)

        self.assertEquals(self.wokka+"\n", self.stream.wrote)



