# -*- coding: utf-8 -*-
"""Example Certbot plugins.
For full examples, see `certbot.plugins`.
"""
import logging
import requests
import zope.interface

from certbot import interfaces, errors
from certbot.plugins import dns_common

# https://github.com/m42e/certbot-dns-ispconfig/blob/master/certbot_dns_ispconfig/dns_ispconfig.py

logger = logging.getLogger(__name__)


@zope.interface.implementer(interfaces.IAuthenticator)
@zope.interface.provider(interfaces.IPluginFactory)
class Authenticator(dns_common.DNSAuthenticator):
    """DNSPod Authenticator."""

    description = "DNSPod Authenticator plugin"

    @classmethod
    def add_parser_arguments(cls, add, default_propagation_seconds=1200):  # pylint: disable=arguments-differ
        super().add_parser_arguments(add, default_propagation_seconds)

        add('credentials', help='DNSPod credentials INI file.')

    def more_info(self):
        return (
            "This plugin configures a DNS TXT record to respond to a dns-01 challenge using "
            + "the DNSpod API."
        )

    def _setup_credentials(self):
        self.credentials = self._configure_credentials(
            'credentials',
            'DNSPod credentials INI file',
            {
                'api_token': 'API token for DNSPod API',
                'dns_ttl': 'TTL value for DNS records',
                'contact_email': 'Your contact email used in requesting DNSPod API'
            },
        )

    def _perform(self, domain, validation_name, validation):
        self._get_dnspod_client().add_txt_record(
            domain, validation_name, validation
        )

    def _cleanup(self, domain, validation_name, validation):
        self._get_dnspod_client().del_txt_record(
            domain, validation_name, validation
        )

    def _get_dnspod_client(self):
        return _DNSPodClient(
            self.credentials.conf('api_token'),
            self.credentials.conf('dns_ttl'),
            self.credentials.conf('contact_email'))


class _DNSPodClient(object):

    USER_AGENT_FMT = 'certbot-dns-dnspod/0.0.1({email})'

    def __init__(self, api_token, ttl, contact_email):
        self.api_token = api_token
        self.ttl = ttl
        self.contact_email = contact_email
        self.user_agent = self.USER_AGENT_FMT.format(email=contact_email)

    def add_txt_record(self, domain, record_name, record_content):
        """Add TXT record"""
        org_record = self._get_txt_record_info_if_exists(domain, record_name)

        if org_record:
            if org_record['value'] != record_content:
                self._modify_txt_record(domain, org_record['id'],
                                        record_name, record_content)
        else:
            self._create_txt_record(domain, record_name, record_content)

    def del_txt_record(self, domain, record_name, record_content):
        """Delete TXT record"""

        org_record = self._get_txt_record_info_if_exists(domain, record_name)

        if org_record:
            if org_record['value'] == record_content:
                self._remove_record(domain, org_record['id'], record_name)

    def _create_txt_record(self, domain, record_name, record_content):
        """Create TXT record"""
        data = {
            'domain': domain,
            'sub_domain': record_name,
            'record_type': 'TXT',
            'record_line': '默认',
            'value': record_content,
            'ttl': self.ttl
        }

        result = self._do_post(self._get_url('Record.Create'), data)

        err_code = result['status']['code']
        if err_code != '1':
            full_domain = '{0}.{1}'.format(record_name, domain)
            raise errors.PluginError('Create TXT record failed, domain: {0}, err_code: {1}, err_msg: {2}'.format(
                full_domain, err_code, result['status']['message']))

        return True

    def _modify_txt_record(self, domain, record_id,
                           record_name, record_content):
        """Modify TXT record"""
        data = {
            'domain': domain,
            'record_id': record_id,
            'sub_domain': record_name,
            'record_type': 'TXT',
            'record_line': '默认',
            'value': record_content
        }

        result = self._do_post(self._get_url('Record.Modify'), data)

        err_code = result['status']['code']
        if err_code != '1':
            full_domain = '{0}.{1}'.format(record_name, domain)
            raise errors.PluginError('Modify TXT record failed, domain: {0}, err_code: {1}, err_msg: {2}'.format(
                full_domain, err_code, result['status']['message']))

        return True

    def _get_domain_info(self, domain):
        data = {
            'domain': domain
        }

        result = self._do_post(self._get_url('Domain.Info', data))

        err_code = result['status']['code']
        if err_code == '1':
            return result['domain']
        else:
            raise errors.PluginError('Get domain info failed, domain: {0}, err_code: {1}, err_msg: {2}'.format(
                domain, err_code, result['status']['message']))

    def _get_txt_record_info_if_exists(self, domain, record_name):
        NO_RECORD_CODE = '10'
        data = {
            'domain': domain,
            'sub_domain': record_name,
            'record_type': 'TXT'
        }

        result = self._do_post(self._get_url('Record.List'), data)

        err_code = result['status']['code']
        if err_code == NO_RECORD_CODE:
            return None
        elif err_code != '1':
            full_domain = '{0}.{1}'.format(domain, record_name)
            raise errors.PluginError('Get TXT record info failed, domain: {0}, err_code: {1}, err_msg: {2}'.format(
                full_domain, err_code, result['status']['message']))

        records = result.get('records') or []
        if records:
            return records[0]

    def _remove_record(self, domain, record_id, record_name):
        """Remove record"""
        data = {
            'domain': domain,
            'record_id': record_id
        }

        result = self._do_post(self._get_url('Record.Remove'), data)

        err_code = result['status']['code']
        if err_code != '1':
            full_domain = '{0}.{1}'.format(record_name, domain)
            logger.error('Remove record failed, domain: {0}, err_code: {1}, err_msg: {2}'.format(
                full_domain, err_code, result['status']['message']
            ))

        return True

    def _get_url(self, action):
        return 'https://dnsapi.cn/{0}'.format(
            action
        )

    def _do_post(self, url, data):
        if not data:
            data = {}

        common_data = {
            'login_token': self.api_token,
            'format': 'json',
        }

        data.update(common_data)

        headers = {
            'User-Agent': self.user_agent
        }

        resp = requests.post(url, data=data, headers=headers)
        if resp.status_code != 200:
            raise errors.PluginError('HTTP Error during login, status_code: {0}, url: {1}'.format(
                resp.status_code, url))

        try:
            result = resp.json()
        except Exception:
            raise errors.PluginError('API response with non JSON, url: {0}, content: {1}'.format(
                url, resp.text))

        return result


if __name__ == '__main__':
    import time

    token = '***'
    email = '***'
    ttl = 600
    client = _DNSPodClient(token, ttl, email)

    cur_record = client._get_txt_record_info_if_exists('zeemu.net', 'notxx')
    print('initial record:', cur_record)

    print('-----------------')
    print('set notxx at_alll')
    client.add_txt_record('zeemu.net', 'notxx', 'at_alll')
    cur_record = client._get_txt_record_info_if_exists('zeemu.net', 'notxx')
    print('current record:', cur_record)
    time.sleep(1)

    print('-----------------')
    print('set notxx at_alll222')
    client.add_txt_record('zeemu.net', 'notxx', 'at_alll222')
    cur_record = client._get_txt_record_info_if_exists('zeemu.net', 'notxx')
    print('current record:', cur_record)
    time.sleep(1)

    print('-----------------')
    print('del notxx at_alll')
    client.del_txt_record('zeemu.net', 'notxx', 'at_alll')
    cur_record = client._get_txt_record_info_if_exists('zeemu.net', 'notxx')
    print('current record:', cur_record)
    time.sleep(1)

    print('-----------------')
    print('del notxx at_alll222')
    client.del_txt_record('zeemu.net', 'notxx', 'at_alll222')
    cur_record = client._get_txt_record_info_if_exists('zeemu.net', 'notxx')
    print('current record:', cur_record)
