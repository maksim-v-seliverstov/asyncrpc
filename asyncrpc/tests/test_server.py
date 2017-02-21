import os
import uuid
import asyncio
import unittest

from asyncrpc.tests import Test
from asyncrpc.server import UniCastServer
from asyncrpc.client import UniCastClient, RPCMethodException


class TestUniCastServer(unittest.TestCase):

    loop = asyncio.get_event_loop()

    def setUp(self):
        port = 9000
        self.interfaces_info = [('127.0.0.1', port), ('127.0.0.2', port)]
        ip_addrs = [ip_addr for ip_addr, _ in self.interfaces_info]
        self.srvc = UniCastServer(
            obj=Test(),
            ip_addrs=ip_addrs,
            port=port
        )
        self.srvc.delay = 0.1
        self.loop.run_until_complete(self.srvc.start())

        self.client = UniCastClient(interfaces_info=self.interfaces_info)

    def tearDown(self):
        self.loop.run_until_complete(self.client.close())
        self.loop.run_until_complete(self.srvc.stop())

    def test_rpc(self):
        msg = str(uuid.uuid1())
        result = self.loop.run_until_complete(self.client.echo(msg=msg))
        self.assertEquals(result, msg)

    def test_only_one_called(self):
        self.loop.run_until_complete(self.client.add())
        count = self.loop.run_until_complete(self.client.get_count())
        self.assertEquals(count, 1)

    def test_exception(self):
        with self.assertRaises(RPCMethodException):
            self.loop.run_until_complete(self.client.error())

    def test_func(self):
        msg = str(uuid.uuid1())
        result = self.loop.run_until_complete(self.client.func(msg))
        self.assertEquals(result, msg)


class TestUniCastServerWithSSLAuth(TestUniCastServer):

    def setUp(self):
        ssl_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'ssl')
        port = 9000
        self.interfaces_info = [('127.0.0.1', port), ('127.0.0.2', port)]
        ip_addrs = [ip_addr for ip_addr, _ in self.interfaces_info]
        self.srvc = UniCastServer(
            obj=Test(),
            ip_addrs=ip_addrs,
            port=port,
            cafile=os.path.join(ssl_path, 'ca.crt'),
            certfile=os.path.join(ssl_path, 'crt', 'server.crt'),
            keyfile=os.path.join(ssl_path, 'key', 'server.key')
        )
        self.srvc.delay = 0.1
        self.loop.run_until_complete(self.srvc.start())

        self.client = UniCastClient(
            interfaces_info=self.interfaces_info,
            certfile=os.path.join(ssl_path, 'crt', 'client01.crt'),
            keyfile=os.path.join(ssl_path, 'key', 'client01.key')
        )
