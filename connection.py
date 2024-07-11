import asyncio
import logging
import sys

def serve_game(host, port):
    """
    TODO: Open a socket for listening for new connections on host:port, and
    perform the war protocol to serve a game of war between each client.
    This function should run forever, continually serving clients.
    """
    loop = asyncio.get_event_loop()
    coro = asyncio.start_server(new_player, host, port, loop=loop)
    server = loop.run_until_complete(coro)

    logging.debug('Serving on %s', server.sockets[0].getsockname())
    print('Serving on %s', server.sockets[0].getsockname())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass