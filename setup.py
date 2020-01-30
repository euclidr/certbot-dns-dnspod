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
            'dnspod_authenticator = certbot_dns_dnspod:Authenticator',
        ],
    },
)
