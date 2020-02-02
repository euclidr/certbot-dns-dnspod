from os import path
from setuptools import setup, find_packages

__version__ = "0.1.1"
__author__ = "Enzo Yang"
__author_email__ = "divisoryang@gmail.com"
__url__ = "https://github.com/euclidr/certbot-dns-dnspod"

this_directory = path.abspath(path.dirname(__file__))

with open(path.join(this_directory, "requirements.txt")) as f:
    install_requires = []
    for line in f:
        install_requires.append(line.strip())

with open(path.join(this_directory, "tests/requirements.txt")) as f:
    tests_requires = []
    for line in f:
        tests_requires.append(line.strip())

with open(path.join(this_directory, "README.md")) as f:
    long_description = f.read()

setup(
    name='certbot-dns-dnspod',
    packages=find_packages(),
    description='dnspod authenticator plugin for certbot',
    long_description=long_description,
    long_description_content_type="text/markdown",
    version=__version__,
    author=__author__,
    author_email=__author_email__,
    url=__url__,
    license="Apache License 2.0",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Plugins",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Security",
        "Topic :: System :: Installation/Setup",
        "Topic :: System :: Networking",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],
    install_requires=install_requires,
    tests_requires=tests_requires,
    entry_points={
        'certbot.plugins': [
            'dns-dnspod = certbot_dns_dnspod.dns_dnspod:Authenticator',
        ],
    },
    include_package_data=True,
    # test_suite='tests',
)
