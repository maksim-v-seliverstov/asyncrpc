# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='aiojsonrpc',
    version=__import__('aiojsonrpc').__version__,
    description='JSON RPC Server and Client',
    author='Seliverstov Maksim',
    author_email='Maksim.V.Seliverstov@yandex.ru',
    packages=find_packages(),
    zip_safe=False,
    keywords=['rpc', 'jsonrpc', 'aiorpc', 'aiojsonrpc', 'multiple interfaces rpc']
)
