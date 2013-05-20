# -*- coding: utf-8 -*-

import unittest
from txclib.packages.ssl_match_hostname import (
    CertificateError, _dnsname_to_pat
)


class DnsRecognitionTestCase(unittest.TestCase):
    """Tests for extracting the hostname from a SSL certificate."""

    def test_wildcard_as_fragment_works(self):
        dn = '*.transifex.com'
        res = _dnsname_to_pat(dn, max_wildcards=2)
        self.assertIsNotNone(res.match('www.transifex.com'))

    def test_one_wildcard_inside_a_fragment_works(self):
        dn = 'w*.transifex.com'
        res = _dnsname_to_pat(dn, max_wildcards=2)
        self.assertIsNotNone(res.match('www.transifex.com'))

    def test_two_wildcards_inside_a_fragment_works(self):
        dn = 'w*w*.transifex.com'
        res = _dnsname_to_pat(dn, max_wildcards=2)
        self.assertIsNotNone(res.match('www.transifex.com'))

    def test_three_wildcards_inside_a_fragment_raises(self):
        dn = 'w*w*w*.transifex.com'
        self.assertRaises(
            CertificateError, _dnsname_to_pat, dn, max_wildcards=2
        )
