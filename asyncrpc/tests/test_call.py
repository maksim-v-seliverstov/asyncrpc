import uuid
import asyncio
import unittest
from unittest.mock import patch

from asyncrpc.tests import Test, create_request
from asyncrpc.call import call_method, RequestsStorage, deserialize


class Response:

    def __init__(self, body, *args, **kwargs):
        self.body = deserialize(body)


class TestJSONRPCCallMethod(unittest.TestCase):
    loop = asyncio.get_event_loop()

    @patch('aiohttp.web.Response', side_effect=Response)
    def test_call_method(self, _):
        msg = str(uuid.uuid1())
        request = create_request('echo', msg=msg)

        respond = self.loop.run_until_complete(
            call_method(Test(), RequestsStorage(), dict(echo=Test.echo), request)
        )

        self.assertIn('jsonrpc', respond.body)
        self.assertIn('result', respond.body)
        self.assertNotIn('error', respond.body)
        self.assertIn('id', respond.body)
        self.assertEquals(msg, respond.body['result'])

    @patch('aiohttp.web.Response', side_effect=Response)
    def test_error_call_method(self, _):
        request = create_request('error')

        respond = self.loop.run_until_complete(
            call_method(Test(), RequestsStorage(), dict(error=Test.error), request)
        )

        self.assertIn('jsonrpc', respond.body)
        self.assertNotIn('result', respond.body)
        self.assertIn('error', respond.body)
        self.assertIn('id', respond.body)

    @patch('aiohttp.web.Response', side_effect=Response)
    def test_does_not_exist_method(self, _):
        request = create_request('not_exist')

        respond = self.loop.run_until_complete(
            call_method(Test(), RequestsStorage(), dict(), request)
        )

        self.assertIn('jsonrpc', respond.body)
        self.assertNotIn('result', respond.body)
        self.assertIn('error', respond.body)
        self.assertIn('id', respond.body)
