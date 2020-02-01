# -*- coding: utf-8 -*-

import requests
import responses
import pytest

from certbot.errors import PluginError

from certbot_dns_dnspod.dnspod_client import DNSPodClient

if requests.compat.is_py2:
    from urlparse import parse_qsl  # pylint: disable=E0611,E0401
else:
    from urllib.parse import parse_qsl  # pylint: disable=E0611,E0401


API_TOKEN = '1234,abcdefg'
TTL = 600
CONTACT_EMAIL = 'admin@example.com'

SUB_DOMAIN = '_acme-challenge'
BASE_DOMAIN = 'example.com'
FULL_DOMAIN = '.'.join([SUB_DOMAIN, BASE_DOMAIN])
RECORD_VALUE = 'record_value'

RECORD_ID = '1234567'


@pytest.fixture
def dnspod():
    return DNSPodClient(API_TOKEN, TTL, CONTACT_EMAIL)


def list_record_result(record_id, record_value):
    return {
        'status': {'code': '1'},
        'domain': {
            'id': '1234',
            'name': BASE_DOMAIN
        },
        'records': [
            {
                'id': record_id,
                'name': SUB_DOMAIN,
                'type': 'TXT',
                'ttl': '600',
                'value': record_value,
            }
        ]
    }


def complete_params(data_dict):
    common_params = {
        'login_token': API_TOKEN,
        'format': 'json',
        'error_on_empty': 'no',
        'lang': 'en'
    }

    common_params.update(data_dict)
    return common_params


def parse_resp_data(encoded_str):
    return dict(parse_qsl(encoded_str))


@responses.activate
def test_add_txt_record_create(dnspod):
    responses.add(
        responses.POST, 'https://dnsapi.cn/Record.Create',
        json={'status': {'code': '1'}}
    )
    responses.add(
        responses.POST, 'https://dnsapi.cn/Record.List',
        json={
            'status': {'code': '10'},
        }
    )

    dnspod.add_txt_record(FULL_DOMAIN, RECORD_VALUE)

    expected_create_params = complete_params({
        'record_type': 'TXT',
        'record_line': '默认',
        'ttl': str(TTL),
        'domain': BASE_DOMAIN,
        'sub_domain': SUB_DOMAIN,
        'value': RECORD_VALUE
    })

    expected_list_params = complete_params({
        'domain': BASE_DOMAIN,
        'sub_domain': SUB_DOMAIN,
        'record_type': 'TXT'
    })

    assert len(responses.calls) == 2
    assert (parse_resp_data(responses.calls[0].request.body)
            == expected_list_params)
    assert (parse_resp_data(responses.calls[1].request.body)
            == expected_create_params)


@responses.activate
def test_add_txt_record_modify(dnspod):
    RECORD_VALUE2 = 'record_value2'

    responses.add(
        responses.POST, 'https://dnsapi.cn/Record.List',
        json=list_record_result(RECORD_ID, RECORD_VALUE2)
    )

    responses.add(
        responses.POST, 'https://dnsapi.cn/Record.Modify',
        json={
            'status': {'code': '1'}
        }
    )

    dnspod.add_txt_record(FULL_DOMAIN, RECORD_VALUE)

    expected_modify_params = complete_params({
        'record_id': RECORD_ID,
        'record_type': 'TXT',
        'record_line': '默认',
        'domain': BASE_DOMAIN,
        'sub_domain': SUB_DOMAIN,
        'value': RECORD_VALUE
    })

    expected_list_params = complete_params({
        'domain': BASE_DOMAIN,
        'sub_domain': SUB_DOMAIN,
        'record_type': 'TXT'
    })

    assert len(responses.calls) == 2
    assert (parse_resp_data(responses.calls[0].request.body)
            == expected_list_params)
    assert (parse_resp_data(responses.calls[1].request.body)
            == expected_modify_params)


@responses.activate
def test_add_txt_record_dup_modify(dnspod):
    responses.add(
        responses.POST, 'https://dnsapi.cn/Record.List',
        json=list_record_result(RECORD_ID, RECORD_VALUE)
    )

    dnspod.add_txt_record(FULL_DOMAIN, RECORD_VALUE)

    expected_list_params = complete_params({
        'domain': BASE_DOMAIN,
        'sub_domain': SUB_DOMAIN,
        'record_type': 'TXT'
    })

    assert len(responses.calls) == 1
    assert (parse_resp_data(responses.calls[0].request.body)
            == expected_list_params)


@responses.activate
def test_del_txt_record(dnspod):
    responses.add(
        responses.POST, 'https://dnsapi.cn/Record.List',
        json=list_record_result(RECORD_ID, RECORD_VALUE)
    )

    responses.add(
        responses.POST, 'https://dnsapi.cn/Record.Remove',
        json={'status': {'code': '1'}}
    )

    dnspod.del_txt_record(FULL_DOMAIN, RECORD_VALUE)

    expected_remove_params = complete_params({
        'record_id': RECORD_ID,
        'domain': BASE_DOMAIN,
    })

    expected_list_params = complete_params({
        'domain': BASE_DOMAIN,
        'sub_domain': SUB_DOMAIN,
        'record_type': 'TXT'
    })

    assert len(responses.calls) == 2
    assert (parse_resp_data(responses.calls[0].request.body)
            == expected_list_params)
    assert (parse_resp_data(responses.calls[1].request.body)
            == expected_remove_params)
    assert responses.calls[1].response.json()['status']['code'] == '1'


@responses.activate
def test_del_txt_record_failed(dnspod):
    '''It won't raise any exception when API returns error'''
    responses.add(
        responses.POST, 'https://dnsapi.cn/Record.List',
        json=list_record_result(RECORD_ID, RECORD_VALUE)
    )

    responses.add(
        responses.POST, 'https://dnsapi.cn/Record.Remove',
        json={'status': {
            'code': '21',
            'message': 'Domain is locked.'
        }}
    )

    dnspod.del_txt_record(FULL_DOMAIN, RECORD_VALUE)

    expected_remove_params = complete_params({
        'record_id': RECORD_ID,
        'domain': BASE_DOMAIN,
    })

    expected_list_params = complete_params({
        'domain': BASE_DOMAIN,
        'sub_domain': SUB_DOMAIN,
        'record_type': 'TXT'
    })

    assert len(responses.calls) == 2
    assert (parse_resp_data(responses.calls[0].request.body)
            == expected_list_params)
    assert (parse_resp_data(responses.calls[1].request.body)
            == expected_remove_params)
    assert responses.calls[1].response.json()['status']['code'] == '21'


@responses.activate
def test_get_record_info_failed(dnspod):
    ERR_MSG = 'Domain not exists'
    responses.add(
        responses.POST, 'https://dnsapi.cn/Record.List',
        json={
            'status': {
                'code': '13',
                'message': ERR_MSG}
        }
    )

    with pytest.raises(
            PluginError,
            match=r'\[DNSPod\] Get TXT record info failed.*') as exc_info:
        dnspod._get_txt_record_info_if_exists(FULL_DOMAIN)

    assert ERR_MSG in str(exc_info)


@responses.activate
def test_http_status_error(dnspod):
    responses.add(
        responses.POST, 'https://dnsapi.cn/Record.List',
        body='Internal server error.',
        status=500
    )

    with pytest.raises(PluginError, match=r'\[DNSPod\] HTTP Error.*'):
        dnspod._get_txt_record_info_if_exists(FULL_DOMAIN)


@responses.activate
def test_http_request_failed(dnspod):
    responses.add(
        responses.POST, 'https://dnsapi.cn/Record.List',
        body=requests.exceptions.ConnectionError('Connection error.')
    )

    with pytest.raises(requests.exceptions.ConnectionError):
        dnspod._get_txt_record_info_if_exists(FULL_DOMAIN)
