"""Test cases for jersey.inet"""

import socket

from twisted.python import log
from twisted.trial.unittest import TestCase

from jersey import inet


class AddressTestCase(TestCase):

    v4Addr = "10.0.1.20"
    v6v4Addr = "::ffff:" + v4Addr
    v6Addr = "2001:470:1f06:2b8::2"
    zeroPaddedV6Addr = "2001:0470:1f06:02b8:0000:0000:0000:0002"
    otherV6Addr = v6Addr[:-1] + "2222"
    hostName = "panix.olix0r.net"
    hexVal = 0x01010101

    def setUp(self):
        self.v4Bytes = socket.inet_pton(socket.AF_INET, self.v4Addr)
        self.v6v4Bytes = socket.inet_pton(socket.AF_INET6, self.v6v4Addr)
        self.v6Bytes = socket.inet_pton(socket.AF_INET6, self.v6Addr)
        self.otherV6Bytes = socket.inet_pton(socket.AF_INET6, self.otherV6Addr)


    def test_IP_v4(self):
        ip = inet.IP(self.v4Addr)
        self.assertIsInstance(ip, inet.V4Address)

    def test_IP_v6(self):
        ip = inet.IP(self.v6Addr)
        self.assertIsInstance(ip, inet.V6Address)

    def test_IP_hostname_error(self):
        self.assertRaises(ValueError, inet.IP, self.hostName)

    def test_IP_hex_error(self):
        self.assertRaises(ValueError, inet.IP, self.hexVal)
        self.assertRaises(ValueError, inet.IP, hex(self.hexVal))


    def test_IP_object_error(self):
        self.assertRaises(ValueError, inet.IP, object())


    def test_nToIP_v4(self):
        self.assertRaises(ValueError, inet.IP, self.v4Bytes)

        ip = inet.nToIP(self.v4Bytes)
        self.assertEquals(ip, inet.IP(self.v4Addr))

    def test_nToIP_v6(self):
        self.assertRaises(ValueError, inet.IP, self.v6Bytes)

        ip = inet.nToIP(self.v6Bytes)
        self.assertEquals(ip, inet.IP(self.v6Addr))


    #def test_nToIP_hostname_error(self):
    #    self.assertRaises(ValueError, inet.nToIP, self.hostName)
    #
    #test_nToIP_hostname_error.skip = "'panix.olix0r.net' is a valid IPv6 " \
    #            "bytestream representing the address: " \
    #            "7061:6e69:782e:6f6c:6978:3072:2e6e:6574."


    def test_nToIP_hex_error(self):
        self.assertRaises(ValueError, inet.nToIP, self.hexVal)
        self.assertRaises(ValueError, inet.nToIP, hex(self.hexVal))

    def test_nToIP_object_error(self):
        self.assertRaises(ValueError, inet.nToIP, object())



    def test_AbstractAddress_error(self):
        self.assertRaises(AssertionError, inet.AbstractAddress, self.v4Addr)
        self.assertRaises(AssertionError, inet.AbstractAddress, self.v6Addr)

    def test_AbstractAddress_fromBytes_error(self):
        self.assertRaises(AssertionError,
                inet.AbstractAddress.fromBytes, self.v4Bytes)
        self.assertRaises(AssertionError,
                inet.AbstractAddress.fromBytes, self.v6Bytes)


    def test_V4Address(self):
        ip = inet.V4Address(self.v4Addr)
        self.assertEquals(inet.AF_INET, ip.family)
        self.assertEquals(socket.AF_INET, inet.AF_INET)
        self.assertEquals(self.v4Addr, str(ip))
        self.assertEquals("V4Address(%r)" % self.v4Addr, repr(ip))
        self.assertEquals(self.v4Bytes, ip.toBytes())

    def test_V4Address_v6_error(self):
        self.assertRaises(ValueError, inet.V4Address, self.v6Addr)


    def test_V4Address_fromBytes(self):
        ip = inet.V4Address.fromBytes(self.v4Bytes)
        self.assertEquals(self.v4Bytes, ip.toBytes())

    def test_V4Address_fromBytes_v6_error(self):
        self.assertRaises(ValueError, inet.V4Address.fromBytes, self.v6Bytes)


    def test_V4Address_comparison(self):
        self.assertTrue(inet.V4Address("1.1.1.1") < inet.V4Address("1.1.1.2"))
        self.assertTrue("1.1.1.1" < inet.V4Address("1.1.1.2"))
        self.assertTrue(inet.V4Address("1.1.1.1") < "1.1.1.2")

        self.assertEquals(inet.V4Address("1.1.1.1"), inet.V4Address("1.1.1.1"))
        self.assertEquals("1.1.1.1", inet.V4Address("1.1.1.1"))

        self.assertNotEquals(inet.V4Address("1.1.1.2"), inet.V4Address("1.1.1.1"))
        self.assertNotEquals("1.1.1.2", inet.V4Address("1.1.1.1"))

        self.assertRaises(ValueError, cmp, inet.V4Address("1.1.1.2"), None) 
        self.assertRaises(ValueError, cmp, inet.V4Address("1.1.1.2"), "dog") 


    def test_V4Address_hash(self):
        ip = inet.V4Address(self.v4Addr)
        self.assertEquals(hash(self.v4Addr), hash(ip))

        ips = {self.v4Addr: ip}
        self.assertIn(self.v4Addr, ips)
        self.assertIn(ip, ips)

    def test_V4Address_toV6(self):
        ip = inet.V4Address(self.v4Addr).toV6()
        self.assertEquals(self.v6v4Addr, ip)

    def test_V4Address_inheritance(self):
        ip = inet.V4Address(self.v4Addr)
        self.assertIsInstance(ip, inet.AbstractAddress)
        self.assertNotIsInstance(ip, inet.V6Address)


    def test_V6Address(self):
        ip = inet.V6Address(self.v6Addr)
        self.assertEquals(inet.AF_INET6, ip.family)
        self.assertEquals(socket.AF_INET6, inet.AF_INET6)
        self.assertEquals(self.v6Addr, str(ip))
        self.assertEquals("V6Address(%r)" % self.v6Addr, repr(ip))
        self.assertEquals(self.v6Bytes, ip.toBytes())

    def test_V6Address_zeroPadded(self):
        ip = inet.V6Address(self.zeroPaddedV6Addr)
        self.assertEquals(self.v6Addr, str(ip))
        self.assertEquals("V6Address(%r)" % self.v6Addr, repr(ip))

    def test_V6Address_fromV4(self):
        ip = inet.V6Address.fromV4(self.v4Addr)
        self.assertEquals(self.v6v4Addr, ip)

        ip2 = inet.V6Address.fromV4(inet.V4Address(self.v4Addr))
        self.assertEquals(ip, ip2)


    def test_V6Address_v4_error(self):
        self.assertRaises(ValueError, inet.V6Address, self.v4Addr)


    def test_V6Address_fromBytes(self):
        ip = inet.V6Address.fromBytes(self.v6Bytes)
        self.assertEquals(self.v6Bytes, ip.toBytes())

    def test_V6Address_fromBytes_v4_error(self):
        self.assertRaises(ValueError, inet.V6Address.fromBytes, self.v4Bytes)


    def test_V6Address_comparison(self):
        lesser = inet.V6Address(self.v6Addr)
        paddedLesser = inet.V6Address(self.zeroPaddedV6Addr)
        greater = inet.V6Address(self.otherV6Addr)

        self.assertTrue(lesser < greater)
        self.assertTrue(str(lesser) < greater)
        self.assertTrue(lesser < str(greater))
        self.assertTrue(lesser <= str(greater))
        self.assertFalse(lesser < paddedLesser)

        self.assertTrue(lesser <= lesser)
        self.assertTrue(greater >= lesser)

        self.assertTrue(lesser == lesser)
        self.assertEquals(lesser, paddedLesser)
        self.assertEquals(str(lesser), paddedLesser)
        self.assertEquals(lesser, str(paddedLesser))

        self.assertNotEquals(lesser, greater)
        self.assertTrue(lesser != greater)

        self.assertRaises(ValueError, cmp, lesser, None) 
        self.assertNotEquals(lesser, None) 
        self.assertRaises(ValueError, cmp, greater, "dog") 
        self.assertNotEquals(greater, "dog") 

        self.assertEquals(sorted([greater, lesser]), [lesser, greater])


    def test_V6Address_equality_v4mapped(self):
        ip = inet.V6Address(self.v6v4Addr)
        self.assertEquals(self.v6v4Addr, ip)

        # XXX Pending clarification from ipv6-devel@
        self.assertNotEquals(self.v4Addr, ip)


    def test_V6Address_hash(self):
        ip = inet.V6Address(self.v6Addr)
        self.assertEquals(hash(self.v6Addr), hash(ip))
        self.assertNotEquals(hash(self.zeroPaddedV6Addr), hash(ip))

        ips = {ip: ip}
        self.assertIn(self.v6Addr, ips)
        self.assertIn(ip, ips)
        self.assertNotIn(self.zeroPaddedV6Addr, ips)


    def test_V6Address_inheritance(self):
        ip = inet.V6Address(self.v6Addr)
        self.assertIsInstance(ip, inet.AbstractAddress)
        self.assertNotIsInstance(ip, inet.V4Address)


    def test_V4Address_V6Address_comparison(self):
        self.assertNotEquals(inet.V4Address("0.0.0.1"), inet.V6Address("::1"))


