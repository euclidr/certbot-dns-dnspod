# certbot-dns-dnspod

dnspod authenticator plugin for certbot

### How to use

##### Install

Make sure certbot is installed, and check which python is certbot running in.

```bash
$ head $(which certbot) -n 1
#!/usr/bin/python3
```

so, certbot will be running in python3, you should install the plugin with `pip3`

```bash
sudo pip3 install git+https://github.com/euclidr/certbot-dns-dnspod.git
```

##### Request for certificates

Create dnspod credentials INI file with params bellow

| key                                         | description                                                                                   |
|---------------------------------------------|-----------------------------------------------------------------------------------------------|
| certbot_dns_dnspod:dns_dnspod_api_token     | DNSPod API token, see [DNSPod FAQ](https://support.dnspod.cn/Kb/showarticle/tsid/227/)        |
| certbot_dns_dnspod:dns_dnspod_dns_ttl       | TTL value for DNS records, the minimum ttl for different VIP types is different |
| certbot_dns_dnspod:dns_dnspod_contact_email | Contact email used to request DNSPod API                                                      |

an example of credentials INI file is:

```ini
certbot_dns_dnspod:dns_dnspod_api_token = "136044,12345678abcde"
certbot_dns_dnspod:dns_dnspod_dns_ttl = 600
certbot_dns_dnspod:dns_dnspod_contact_email = 'dns_admin@example.com'
```

Now run:

```bash
sudo certbot certonly \
    -a certbot-dns-dnspod:dns-dnspod \
    [--certbot-dns-dnspod:dns-dnspod-credentials /path/to/dnspod_credentials.ini] \
    [--cert-name star.example.com] \
    -d example.com
    -d *.example.com
```

`--certbot-dns-dnspod:dns-dnspod-credentials` is optional, if you don't provide credentials INI file path, certbot will prompt you for `api_token` `dns_ttl` and `contact_email`.


##### Renew certificates

When `certbot certonly` is done, the certificates is stored in your filesystem. request configs, domains, absolute path of INI file will be recorded and used in renewal.