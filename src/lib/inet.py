"""Internet Addresses
"""

import socket

AF_INET = socket.AF_INET
AF_INET6 = socket.AF_INET6


def IP(address):
    """Build an IPv4 or IPv6 address from a string representation.
    """
    for klass in (V4Address, V6Address):
        try:
            ip = klass(address)
        except ValueError, e:
            error = e
        else:
            return ip

    raise error


def nToIP(bytes):
    """Build an IPv4 or IPv6 address from a network representation.
    """
    for klass in (V4Address, V6Address):
        try:
            return klass.fromBytes(bytes)
        except ValueError, ve:
            error = ve
        else:
            return ip

    raise error



class AbstractAddress(object):
    """Abstract Internet address.

    Attributes:
        family --  Address family (i.e. AF_INET or AF_INET6).
                   Must be set by subclasses.
    """

    family = None

    def __init__(self, address):
        """Build an instance based on an address string.

        Arguments:
            address --  Text-representation of an Address.
        Preconditions:
            self.family is set (i.e. by a subclass)
        Raises:
            ValueError if address is not a valid IP address.
        """
        assert self.family is not None

        try:
            self._bytes = socket.inet_pton(self.family, address)

        except (socket.error, TypeError):
            raise ValueError("Invalid {0.__class__.__name__}".format(self),
                             address, self.family)


    @classmethod
    def fromBytes(klass, bytes):
        """Build an instance based on a network-ordered byte-representation.

        Arguments:
            bytes --  Network-ordered bytes representing an Address.
        Preconditions:
            klass.family is set (i.e. by a subclass)
        Raises:
            ValueError if bytes
        """
        assert klass.family is not None

        try:
            address = socket.inet_ntop(klass.family, bytes)

        except (socket.error, TypeError):
            raise ValueError("Invalid {0.__name__}".format(klass), bytes)

        return klass(address)


    def toBytes(self):
        """Return a network-order byte-representation of the address."""
        return self._bytes


    def __str__(self):
        return socket.inet_ntop(self.family, self._bytes)

    def __repr__(self):
        return "{0.__class__.__name__}('{0!s}')".format(self)


    def __cmp__(self, obj):
        """Compare this object with another.""" 
        # If obj is an Address, stringifying it puts it in a state where it
        # can be parsed by IP().
        other = IP(str(obj))

        # Compare IPs by byte representation.
        if self.family == other.family:
            return cmp(self._bytes, other.toBytes())
        else:
            return cmp(self.family, other.family)


    def __eq__(self, obj):
        try:
            comparison = self.__cmp__(obj)

        except (ValueError, TypeError):
            # The obj can't be stringified or it is not a valid IP address.
            equality = False

        else:
            equality = bool(comparison == 0)

        return equality


    def __ne__(self, obj):
        return not self.__eq__(obj)


    def __hash__(self):
        return hash(str(self))



class V4Address(AbstractAddress):
    """IPv4 Address"""

    family = AF_INET

    def toV6(self):
        """Return the a V6Address mapped from this address."""
        return V6Address.fromV4(self)


class V6Address(AbstractAddress):
    """IPv6 Address"""

    family = AF_INET6

    @classmethod
    def fromV4(klass, ip):
        """Build an IPv4-mapped IPv6 address."""
        if not isinstance(ip, V4Address):
            ip = V4Address(str(ip))
        return klass("::ffff:{0!s}".format(ip))



__version__ = """$Revision: 74 $"""[11:-2]
__author__ = """Oliver Gould <ver@yahoo-inc.com>"""
__copyright__ = """Copyright Yahoo!, Inc (2010).  All rights reserved."""

