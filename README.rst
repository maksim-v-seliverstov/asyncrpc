Installation
-------------

::

   $ pip install asyncrpc

Getting started
----------------

Client
~~~~~~

.. code-block:: python

   import asyncio

   from asyncrpc.client import UniCastClient


   if __name__ == '__main__':
       client = UniCastClient(
           interfaces_info=[('127.0.0.1', 9001)]
       )
       loop = asyncio.get_event_loop()
       print(loop.run_until_complete(client.echo('test asyncrpc')))
       loop.run_until_complete(client.close())



Server
~~~~~~

.. code-block:: python

   import asyncio

   from asyncrpc.server import UniCastServer


   class Test:

       @asyncio.coroutine
       def echo(self, msg):
           return msg


   if __name__ == '__main__':
       server = UniCastServer(
           obj=Test(),
           ip_addrs='127.0.0.1',
           port=9001
       )

       loop = asyncio.get_event_loop()
       loop.run_until_complete(server.start())
       loop.run_forever()

