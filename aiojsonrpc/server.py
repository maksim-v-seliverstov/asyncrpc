import inspect
import asyncio
from functools import partial

from aiohttp import web

from aiojsonrpc.call import call_method, RequestsStorage


class UniCastServer:

    def __init__(self, obj, ip_addrs, port, storage=RequestsStorage(), loop=None):
        self.ip_addrs = ip_addrs
        self.port = port

        cls = type(obj)
        self.methods = {info[0]: info[1] for info in inspect.getmembers(cls, inspect.isfunction) if not info[0].startswith('_')}

        self.loop = asyncio.get_event_loop() if loop is None else loop

        self.app = web.Application()
        self.app.router.add_route(
            'POST', '/post', partial(call_method, obj, storage, self.methods)
        )

        self.servers = dict()

        self.delay = 5
        self.flag_continue = True
        self.update_task = None

    @asyncio.coroutine
    def start(self):
        self.update_task = self.loop.create_task(self.update())

    @asyncio.coroutine
    def update(self):
        ip_addrs = list()
        while self.flag_continue:
            try:
                for ip_addr in list(set(self.ip_addrs) - set(ip_addrs)):
                    self.loop.create_task(self.create_server(ip_addr, self.port))
                    ip_addrs.append(ip_addr)
            finally:
                yield from asyncio.sleep(self.delay)

    @asyncio.coroutine
    def create_server(self, ip_addr, port):
        try:
            srv = yield from self.loop.create_server(
                self.app.make_handler(), ip_addr, port
            )
            self.servers[self._get_id(ip_addr, srv.sockets[0].getsockname()[1])] = srv
        except OSError:
            yield from asyncio.sleep(self.delay)
            self.loop.create_task(self.create_server(ip_addr, port))

    @asyncio.coroutine
    def stop(self):
        self.flag_continue = False
        for srv in self.servers.values():
            srv.close()
        for srv in self.servers.values():
            yield from srv.wait_closed()
        yield from asyncio.wait([self.update_task], timeout=self.delay)

    def _get_id(self, ip_addr, port):
        return '{}:{}'.format(ip_addr, port)
