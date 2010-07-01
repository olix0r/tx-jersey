import os

from twisted.python import log, reflect
from twisted.enterprise.adbapi import ConnectionPool

from zope.interface.exceptions import DoesNotImplement
from zope.interface.verify import verifyObject



class TestBase(object):
    """Base class for tests.  Does not subclass TestCase.
    """


    def makeTestRoot(self):
        """Create a test-specific directory."""
        pathParts = self.id().split(".")

        try:
            casesIdx = pathParts.index("cases")

        except IndexError:
            self.rootDir = os.path.sep.join(pathParts)

        else:
            self.rootDir = os.path.sep.join(pathParts[casesIdx+1:])

        os.makedirs(self.rootDir)

        return self.rootDir


    def assertImplements(self, interface, obj):
        """Fail if obj does not implement interface."""
        try:
            verifyObject(interface, obj)

        except DoesNotImplement, dni:
            self.fail("{0!r}: {1!s}".format(obj, dni))

    failIfNotImplements = assertImplements


