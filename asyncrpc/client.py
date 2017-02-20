import sys
import time
import asyncio
from collections import deque

import aiohttp
from aiohttp.errors import ClientOSError

from asyncrpc.call import create_request, deserialize


PY_35 = sys.version_info >= (3, 5)


class _ContextManager:

    def __init__(self, client):
        self.client = client

    def __enter__(self):
        return None

    @asyncio.coroutine
    def __exit__(self, *args):
        try:
            yield from self.client.stop()
        finally:
            self.client = None  # Crudely prevent reuse.


class ContextManagerMixin:

    def __enter__(self):
        raise RuntimeError(
            '"yield from" should be used as context manager expression')

    def __exit__(self, *args):
        pass

    @asyncio.coroutine
    def __iter__(self):
        return _ContextManager(self)

    if PY_35:
        @asyncio.coroutine
        def __aenter__(self):
            return self

        @asyncio.coroutine
        def __aexit__(self, exc_type, exc_val, exc_tb):
            yield from self.close()


class LockCounter:
    _count = 0

    def __init__(self):
        self._fut = asyncio.Future()
        self._fut.set_result(None)

    def __enter__(self):
        self._count += 1
        self._fut = asyncio.Future()

    def __exit__(self, a, b, c):
        self._count -= 1
        if self._count <= 0:
            self._fut.set_result(None)

    if PY_35:
        @asyncio.coroutine
        def __aenter__(self):
            return self.__enter__()

        @asyncio.coroutine
        def __aexit__(self, *a):
            return self.__exit__(*a)

    @asyncio.coroutine
    def wait(self):
        yield from self._fut


class RequestError(Exception):
    pass


class RPCMethodException(Exception):

    def __init__(self, value):
        super().__init__(value)
        self.value = value


@asyncio.coroutine
def wait_first_completed(futures):
    flag_completed = False

    timeout = 30
    while not flag_completed:
        done, pending = (yield from asyncio.wait(futures, return_when=asyncio.FIRST_COMPLETED, timeout=timeout))

        if not done:
            for f in pending:
                f.cancel()
            raise RequestError()

        error_info = None
        for f in done:
            try:
                result, status, headers = f.result()
                if status != 200:
                    if status == 500:
                        error_info = result
                    continue
                flag_completed = True
                break
            except:
                pass

        timeout = 15

        if flag_completed:
            break

        if pending:
            futures = list(pending)
        else:
            try:
                if error_info is not None:
                    raise RPCMethodException(error_info)
                done.pop().result()  # raise exception
            except ClientOSError:
                raise RequestError()

    return result, status, headers, pending


def session_decorator(func):
    @asyncio.coroutine
    def session_post(self, data, headers=None):
        futures = list()

        yield from self.try_clear()

        if not self.sessions:
            connector = aiohttp.TCPConnector(
                loop=self.loop, ssl_context=self.ssl_context, limit=self.limit
            )
            self.sessions.append(aiohttp.ClientSession(connector=connector))

        for ip_addr, port in self.interfaces_info:
            futures.append(
                func(
                    self,
                    url='{}/{}'.format(self.url_mask.format(ip_addr, port), self.patch),
                    session=self.sessions[-1],
                    data=data,
                    headers=headers
                )
            )
        try:
            result, status, headers, pending = yield from wait_first_completed(futures)
        except RPCMethodException as error_data:
            for session in self.sessions:
                yield from session.close()
            self.sessions.clear()
            error = deserialize(error_data.value)
            raise RPCMethodException(error['error'])
        except RequestError:
            for session in self.sessions:
                yield from session.close()
            self.sessions.clear()
            raise RPCMethodException('RequestError')

        for f in pending:
            f.cancel()

        return result
    return session_post


class UniCastClient(ContextManagerMixin):
    _closing = False

    def __init__(self, interfaces_info, patch='post', limit=20, loop=None, url_mask=None, **kwargs):
        self.interfaces_info = interfaces_info
        self.patch = patch

        self.limit = limit

        self.loop = asyncio.get_event_loop() if loop is None else loop

        self.url_mask = url_mask or 'http://{}:{}'

        self.sessions = deque()

        self.__start_ts = None
        self.__finish_ts = None
        self.monitoring_timeout = 5

        self._req_counter = LockCounter()

    def __getattr__(self, name):
        return lambda *args, **kwargs: self._async_call(name, *args, **kwargs)

    @asyncio.coroutine
    def _async_call(self, method_name, *args, **kwargs):
        request = create_request(method_name, *args, **kwargs)
        data = yield from self.session_post(data=request)
        response = deserialize(data)
        if 'error' in response and response['error'] is not None:
            raise RPCMethodException(response['error'])
        return response['result']

    @asyncio.coroutine
    def request(self, f):
        if self._closing:
            raise asyncio.CancelledError

        with self._req_counter:
            resp = yield from f
            try:
                return (yield from resp.read()), resp.status, resp.headers
            finally:
                yield from resp.release()

    @session_decorator
    def session_post(self, url, session, data, headers):
        return (
            yield from self.request(session.post(url, data=data, headers=headers))
        )

    @session_decorator
    def session_delete(self, url, session, *args, **kwargs):
        return (
            yield from self.request(session.delete(url))
        )

    @session_decorator
    def session_get(self, url, session, headers, *args, **kwargs):
        return (
            yield from self.request(session.get(url, headers=headers))
        )

    @asyncio.coroutine
    def close(self):
        self._closing = True
        yield from self._req_counter.wait()
        for session in self.sessions:
            yield from session.close()
        self.sessions.clear()

    @asyncio.coroutine
    def try_clear(self):
        if self.__start_ts is None:
            self.__start_ts = time.perf_counter()
            return

        if time.perf_counter() - self.__start_ts > self.monitoring_timeout and self.__finish_ts is None:
            self.__finish_ts = time.perf_counter()

            connector = aiohttp.TCPConnector(loop=self.loop, ssl_context=self.ssl_context, limit=self.limit)
            self.sessions.append(aiohttp.ClientSession(connector=connector))
            return

        if self.__finish_ts and time.perf_counter() - self.__finish_ts > self.monitoring_timeout:
            if len(self.sessions) > 1:
                session = self.sessions.popleft()
                yield from session.close()
            self.__start_ts = None
            self.__finish_ts = None
            return
