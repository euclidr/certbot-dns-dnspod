# certbot-dns-dnspod

DNSPod authenticator plugin for certbot

### Install

Make sure certbot is installed, and check which python is certbot running in.

```bash
$ head $(which certbot) -n 1
#!/usr/bin/python3
```

so, certbot will be running in python3, you should install the plugin with `pip3`

```bash
sudo pip3 install git+https://github.com/euclidr/certbot-dns-dnspod.git
```

### Name parameters

| Parameter | description |
| --authenticator certbot-dns-dnspod:dns-dnspod | set certbot-dns-dnspod as authenticator plugin (Required) |
| --certbot-dns-dnspod:dns-dnspod-credentials | path to credentials INI file (Required) |
| --certbot-dns-dnspod:dns-dnspod-propagation-seconds | waiting time for DNS to propagate before asking ACME server to verity the DNS record, default: 10 |


### Credentials INI file

DNSPod credentials INI file has params:

| key                                         | description                                                                            |
|---------------------------------------------|----------------------------------------------------------------------------------------|
| certbot_dns_dnspod:dns_dnspod_api_token     | DNSPod API token, see [DNSPod FAQ](https://support.dnspod.cn/Kb/showarticle/tsid/227/) |
| certbot_dns_dnspod:dns_dnspod_dns_ttl       | TTL value for DNS records, the minimum ttl for different VIP types is different        |
| certbot_dns_dnspod:dns_dnspod_contact_email | Contact email used to request DNSPod API                                               |

an example of credentials INI file is:

```ini
certbot_dns_dnspod:dns_dnspod_api_token = "136044,12345678abcde"
certbot_dns_dnspod:dns_dnspod_dns_ttl = 600
certbot_dns_dnspod:dns_dnspod_contact_email = 'dns_admin@example.com'
```

### Command Example


```bash
sudo certbot certonly \
    -a certbot-dns-dnspod:dns-dnspod \
    [--certbot-dns-dnspod:dns-dnspod-credentials /path/to/dnspod_credentials.ini] \
    [--cert-name star.example.com] \
    -d example.com
    -d *.example.com
```

### Renew certificates

When `certbot certonly` is done, cerbot will store configs that request the certificates, after that, you can run `certbot renew` periodically to renew the certificates.