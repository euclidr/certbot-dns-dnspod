# -*- coding: utf-8 -*-
"""Example Certbot plugins.
For full examples, see `certbot.plugins`.
"""
import logging
import zope.interface

from certbot import interfaces
from certbot.plugins import dns_common

from .dnspod_client import DNSPodClient

# https://github.com/m42e/certbot-dns-ispconfig/blob/master/certbot_dns_ispconfig/dns_ispconfig.py

logger = logging.getLogger(__name__)


@zope.interface.implementer(interfaces.IAuthenticator)
@zope.interface.provider(interfaces.IPluginFactory)
class Authenticator(dns_common.DNSAuthenticator):
    """DNSPod Authenticator."""

    description = "DNSPod Authenticator plugin"

    @classmethod
    def add_parser_arguments(cls, add, default_propagation_seconds=10):
        super().add_parser_arguments(add, default_propagation_seconds)

        add('credentials', help='DNSPod credentials INI file.')

    def more_info(self):
        return (
            "This plugin configures a DNS TXT record to respond to a "
            + "dns-01 challenge using the DNSpod API."
        )

    def _setup_credentials(self):
        """Setup credential parser

        It define a command line option for setting .ini file path for
            configuring DNSPod related params.

        If .ini file path is not set, or some params is missing It will
            prompt the user for necessary infos.
        """
        self.credentials = self._configure_credentials(
            'credentials',
            'DNSPod credentials INI file',
            {
                'api_token': 'API token for DNSPod API',
                'dns_ttl': 'TTL value for DNS records, DNSPod limits the minimum ttl for different VIP types',
                'contact_email': 'Contact email used to request DNSPod API'
            },
        )

    def _perform(self, domain, validation_name, validation):
        """
        Configures a DNS TXT record

        :param str domain: The domain being validated.
        :param str validation_name: The validation record domain name.
        :param str validation: The validation record content.
        :raises errors.PluginError: If the chanllenge can not be performed.
        """
        self._get_dnspod_client().add_txt_record(
            validation_name, validation
        )

    def _cleanup(self, domain, validation_name, validation):
        """
        Deletes the DNS TXT record which would have been created by `_perform`

        :param str domain: The domain being validated.
        :param str validation_name: The validation record domain name.
        :param str validation: The validation record content.
        """
        self._get_dnspod_client().del_txt_record(
            validation_name, validation
        )

    def _get_dnspod_client(self):  # pylint: disable=missing-docstring
        return DNSPodClient(
            self.credentials.conf('api_token'),
            self.credentials.conf('dns_ttl'),
            self.credentials.conf('contact_email'))
