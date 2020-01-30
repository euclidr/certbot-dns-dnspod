from setuptools import setup, find_packages

setup(
    name='certbot-dns-dnspod',
    packages=find_packages(),
    install_requires=[
        'certbot',
        'zope.interface',
    ],
    entry_points={
        'certbot.plugins': [
            'dns-dnspod = certbot_dns_dnspod.dns_dnspod:Authenticator',
        ],
    },
)
