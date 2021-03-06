import json
import uuid
import inspect
import aiohttp
import asyncio
import traceback
from collections import OrderedDict

from asyncrpc.cleaner import Cleaner


def _create_request(method, *args, **kwargs):
    return dict(
        jsonrpc='2.0',
        method=method,
        params=args or kwargs,
        id=str(uuid.uuid1())
    )


def create_request(method, *args, **kwargs):
    return serialize(_create_request(method, *args, **kwargs))


class RequestsStorage(Cleaner):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.events = OrderedDict()
        self.lock = asyncio.Lock()

    def is_called(self, request_id):
        return request_id in self.data

    def set_result(self, request_id):
        if request_id not in self.data:
            self.events[request_id] = asyncio.Event()
            self.data[request_id] = dict()

    @asyncio.coroutine
    def wait(self, request_id):
        yield from self.events[request_id].wait()

    def set(self, request_id):
        self.events[request_id].set()

    def popleft(self, count):
        for _ in range(count):
            self.events.popitem(last=False)

        super().popleft(count)


def serialize(value):
    return json.dumps(value).encode()


def deserialize(data):
    return json.loads(data.decode())


def isinteger(value):
    try:
        int(value)
        return True
    except ValueError:
        return False


@asyncio.coroutine
def _call_method(obj, storage, methods, request):
    try:
        with (yield from storage.lock):
            flag_called = storage.is_called(request['id'])
            storage.set_result(request['id'])

        if not isinteger(request['id']) and flag_called:
            yield from storage.wait(request['id'])
            respond = dict(
                jsonrpc='2.0',
                error='Method {} was already called'.format(request['method']),
                id=request['id']
            )
            return respond, 202

        if request['method'] not in methods:
            respond = dict(
                jsonrpc='2.0',
                error='Method {} does not exist'.format(request['method']),
                id=request['id']
            )
            storage.set(request['id'])
            return respond, 405

        method = getattr(obj, request['method'])

        if inspect.isgeneratorfunction(methods[request['method']]):
            if isinstance(request['params'], dict):
                result = yield from method(**request['params'])
            else:
                result = yield from method(*request['params'])
        else:
            if isinstance(request['params'], dict):
                result = method(**request['params'])
            else:
                result = method(*request['params'])

        respond = dict(
            jsonrpc='2.0',
            result=result,
            id=request['id']
        )
        storage.set(request['id'])
        return respond, 200
    except:
        respond = dict(
            jsonrpc='2.0',
            error=traceback.format_exc(),
            id=request['id']
        )
        storage.set(request['id'])
        return respond, 500

@asyncio.coroutine
def call_method(obj, storage, methods, request):
    storage.try_clear()
    data = yield from request.read()
    response, status = yield from _call_method(obj, storage, methods, deserialize(data))
    return aiohttp.web.Response(body=serialize(response), status=status)
