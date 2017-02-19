# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='asyncrpc',
    version=__import__('asyncrpc').__version__,
    description='JSON RPC Server and Client',
    author='Seliverstov Maksim',
    author_email='Maksim.V.Seliverstov@yandex.ru',
    packages=find_packages(),
    zip_safe=False,
    keywords=['rpc', 'jsonrpc', 'aiorpc', 'asyncrpc', 'multiple interfaces rpc'],
    install_requires=['aiohttp']
)
