import json
import uuid
import asyncio


class Test:

    count = 0

    @asyncio.coroutine
    def echo(self, msg):
        return msg

    @asyncio.coroutine
    def error(self):
        raise Exception('Internal Error')

    @asyncio.coroutine
    def add(self):
        self.count += 1

    @asyncio.coroutine
    def get_count(self):
        return self.count

    def func(self, msg):
        return msg


def create_request(method, *args, **kwargs):
    class Request:

        @asyncio.coroutine
        def read(self):
            return json.dumps(
                dict(
                    jsonrpc='2.0',
                    method=method,
                    params=args or kwargs,
                    id=str(uuid.uuid1())
                )
            ).encode()

    return Request()
