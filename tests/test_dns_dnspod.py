"""Tests for certbot_dns_dnspod.dns_dnspod."""

import mock

from certbot.compat import os
from certbot.plugins import dns_test_common
from certbot.plugins.dns_test_common import DOMAIN
from certbot.tests import util as test_util


FAKE_API_TOKEN = "12345,abcdefg"
FAKE_DNS_TTL = 600
FAKE_CONTACT_EMAIL = "dns_adm@example.com"


class AuthenticatorTest(
    test_util.TempDirTestCase, dns_test_common.BaseAuthenticatorTest
):
    def setUp(self):
        super(AuthenticatorTest, self).setUp()

        from certbot_dns_dnspod.dns_dnspod import Authenticator

        path = os.path.join(self.tempdir, "file.ini")
        dns_test_common.write(
            {
                "dnspod_api_token": FAKE_API_TOKEN,
                "dnspod_dns_ttl": FAKE_DNS_TTL,
                "dnspod_contact_email": FAKE_CONTACT_EMAIL,
            },
            path,
        )

        super(AuthenticatorTest, self).setUp()
        self.config = mock.MagicMock(
            dnspod_credentials=path, dnspod_propagation_seconds=0
        )  # don't wait during tests

        self.auth = Authenticator(self.config, "dnspod")

        self.mock_client = mock.MagicMock()
        # _get_dnspod_client | pylint: disable=protected-access
        self.auth._get_dnspod_client = mock.MagicMock(
            return_value=self.mock_client)

    def test_perform(self):
        self.auth.perform([self.achall])

        expected = [
            mock.call.add_txt_record(
                "_acme-challenge." + DOMAIN, mock.ANY
            )
        ]
        self.assertEqual(expected, self.mock_client.mock_calls)

    def test_cleanup(self):
        # _attempt_cleanup | pylint: disable=protected-access
        self.auth._attempt_cleanup = True
        self.auth.cleanup([self.achall])

        expected = [
            mock.call.del_txt_record(
                "_acme-challenge." + DOMAIN, mock.ANY
            )
        ]
        self.assertEqual(expected, self.mock_client.mock_calls)
