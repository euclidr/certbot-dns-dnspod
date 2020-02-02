# -*- coding: utf-8 -*-
"""DNSPod Client"""

import logging
import requests

# from acme.magic_typing import Dict
# from acme.magic_typing import Any

from certbot import errors

from . import __version__

logger = logging.getLogger(__name__)  # pylint: disable=C0103


NO_RECORD_CODE = '10'


class DNSPodClient(object):

    USER_AGENT_FMT = 'certbot-dns-dnspod/{version}({email})'

    def __init__(self, api_token, ttl, contact_email):
        """Init DNSPodClient

        :param str api_token: API token used for authentication,
            see: https://support.dnspod.cn/Kb/showarticle/tsid/227/
        :param int ttl: DNS ttl, DNSPod limits ttl ranges for different
            VIP types, If you are free user,
            the ttl must not be less than 600.
        :param str contact_email: Contact email used to request DNSPod API
        """
        self.api_token = api_token
        self.ttl = ttl
        self.contact_email = contact_email
        self.user_agent = self.USER_AGENT_FMT.format(
            version=__version__,
            email=contact_email)

    def add_txt_record(self, full_domain, record_content):
        """Add TXT record

        :param str full_domain: Full domain.
        :param str record_content: Value that the record should be set.
        :raises errors.PluginError: if fails to create the record.
        """
        org_record = self._get_txt_record_info_if_exists(full_domain)

        if org_record:
            if org_record['value'] != record_content:
                self._modify_txt_record(org_record['id'],
                                        full_domain,
                                        record_content)
        else:
            self._create_txt_record(full_domain, record_content)

    def del_txt_record(self, full_domain, record_content):
        """Delete TXT record if record value is match

        :param str full_domain: Full domain.
        :param str record_content: Value that the record should be match.
        :raises errors.PluginError: if fails to delete the record.
        """
        org_record = self._get_txt_record_info_if_exists(full_domain)

        if org_record:
            if org_record['value'] == record_content:
                self._remove_record(org_record['id'], full_domain)

    def _create_txt_record(self, full_domain, record_content):
        """Create TXT record

        :param str record_id: DNS record ID in DNSPod.
        :param str full_domain: Full domain.
        :param str record_content: Value that the record should be set.
        :raises errors.PluginError: If fails to create record.
        """
        sub_domain, base_domain = self._split_full_domain(full_domain)

        data = {
            'domain': base_domain,
            'sub_domain': sub_domain,
            'record_type': 'TXT',
            'record_line': '默认',
            'value': record_content,
            'ttl': self.ttl
        }

        result = self._do_post(self._get_url('Record.Create'), data)

        err_code = result['status']['code']
        if err_code != '1':
            raise errors.PluginError(
                '[DNSPod] Create TXT record failed,'
                'domain: {0}, err_code: {1}, err_msg: {2}'.format(
                    full_domain, err_code, result['status']['message']))

        return True

    def _modify_txt_record(self, record_id, full_domain, record_content):
        """Modify TXT record

        :param str record_id: DNS record ID in DNSPod.
        :param str full_domain: Full domain.
        :param str record_content: Value that the record should be set.
        :raises errors.PluginError: If fails to modify the record.
        """
        sub_domain, base_domain = self._split_full_domain(full_domain)

        data = {
            'domain': base_domain,
            'record_id': record_id,
            'sub_domain': sub_domain,
            'record_type': 'TXT',
            'record_line': '默认',
            'value': record_content
        }

        result = self._do_post(self._get_url('Record.Modify'), data)

        err_code = result['status']['code']
        if err_code != '1':
            raise errors.PluginError(
                '[DNSPod] Modify TXT record failed, domain:'
                ' {0}, err_code: {1}, err_msg: {2}'.format(
                    full_domain, err_code, result['status']['message']))

    def _get_txt_record_info_if_exists(self, full_domain):
        """
        Get TXT record info by full domain

        :param str full_domain: Full domain.
        :returns: record of the domain, None if not exists.
        :rtype: Optional[Dict[str, Any]]
        :raises errors.PluginError: If the API returns error.
        """

        sub_domain, base_domain = self._split_full_domain(full_domain)

        data = {
            'domain': base_domain,
            'sub_domain': sub_domain,
            'record_type': 'TXT'
        }

        result = self._do_post(self._get_url('Record.List'), data)

        err_code = result['status']['code']
        if err_code == NO_RECORD_CODE:
            return None
        elif err_code != '1':
            full_domain = '{0}.{1}'.format(sub_domain, base_domain)
            raise errors.PluginError(
                '[DNSPod] Get TXT record info failed, domain: {0},'
                ' err_code: {1}, err_msg: {2}'.format(
                    full_domain, err_code, result['status']['message']))

        records = result.get('records') or []
        if records:
            return records[0]

    def _remove_record(self, record_id, full_domain):
        """
        Remove DNS record

        :param str record_id: DNS record ID in DNSPod
        :param str full_domain: Full domain.
        :returns: whether the operation is success
        :rtype: bool
        """
        _, base_domain = self._split_full_domain(full_domain)

        data = {
            'domain': base_domain,
            'record_id': record_id
        }

        result = self._do_post(self._get_url('Record.Remove'), data)

        err_code = result['status']['code']
        if err_code != '1':
            logger.error(
                '[DNSPod] Remove record failed, domain: {0}, '
                'err_code: {1}, err_msg: {2}'.format(
                    full_domain, err_code, result['status']['message']
                ))
            return False

        return True

    @staticmethod
    def _get_url(action):
        """
        Get API URL from action

        :param str action: action
        :returns: full URL of API
        :rtype: str
        """
        return 'https://dnsapi.cn/{0}'.format(
            action
        )

    def _do_post(self, url, data):
        """
        Do request DNSPod API

        :param str url: URL for DNSPod API.
        :param Dict[str, Any] data: request parameters
        :returns: API response
        :rtype: Dict[str, Any]
        """
        if not data:
            data = {}

        common_data = {
            'login_token': self.api_token,
            'format': 'json',
            'error_on_empty': 'no',
            'lang': 'en'
        }

        data.update(common_data)

        headers = {
            'User-Agent': self.user_agent
        }

        resp = requests.post(url, data=data, headers=headers)
        if resp.status_code != 200:
            raise errors.PluginError(
                '[DNSPod] HTTP Error, status_code: {0}, url: {1}'
                .format(resp.status_code, url))

        try:
            result = resp.json()
        except Exception:
            raise errors.PluginError(
                '[DNSPod] API response with non JSON, url: {0}, content: {1}'
                .format(url, resp.text))

        return result

    @staticmethod
    def _split_full_domain(full_domain):
        """
        Split full domain into sub_domain and base_domain

        :param str full_domain: domain like abc.example.com
        :returns: (sub_domain, base_domain) splitted domain parts,
            'abc.example.com' will be splitted into ('abc', 'example.com')
        :rtype: Tuple[str, str]
        """
        parts = full_domain.rsplit('.', 2)

        if len(parts) == 3:
            sub_domain, domain, tld = parts
        elif len(parts) == 2:
            sub_domain = '@'
            domain, tld = parts
        else:
            raise errors.PluginError(
                '[DNSPod] Unable to split full domain: {0}'
                .format(full_domain))

        base_domain = '{0}.{1}'.format(domain, tld)

        return sub_domain, base_domain
