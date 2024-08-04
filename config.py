SERVER_ADDRESS = ""
PLAYERS = 2
RECV_BUFFER = 1024

MESSAGE_TEMPLATE = {
    "has_message": False,
    "broadcast": False,
    "msg": {
        "src": None,
        "dst": None,
        "content": None,
        "crc": None,
        "type": None,
    },
    "bearer": None,
    "crc8": None,
}
"""
the message template is a dictionary that represents the structure of the message
the format is:
{
    "has_message": bool, # if the message has content
    "msg": {
        "src": str, # the source of the message [server, M1, M2, M3, M4]
        "dst": str, # the destination of the message [server, M1, M2, M3, M4]
        "content": str, # the content of the message
        "crc": str, # the crc of the message
        "type": str, # the type of the message
    },
    "bearer": str, # the bearer of the message
    "crc8": int, # the crc8 of the message
}
"""

# SERVER
SERVER_LISTEN_PORT = 12345
SERVER_SEND_PORT = 12346
# SERVER
# M1
M1_LISTEN_PORT = SERVER_SEND_PORT
M1_SEND_PORT = 12347
# M1
# M2
M2_LISTEN_PORT = M1_SEND_PORT
M2_SEND_PORT = 12348
# M2
# M3
M3_LISTEN_PORT = M2_SEND_PORT
M3_SEND_PORT = 12349
# M3
# M4
M4_LISTEN_PORT = M3_SEND_PORT
M4_SEND_PORT = SERVER_LISTEN_PORT
# M4

NETWORK_CONNECTIONS = {
    "M0": {
        "address": "localhost",
        "listen_port": SERVER_LISTEN_PORT,
        "send_port": SERVER_SEND_PORT,
    },
    "M1": {
        "address": "localhost",
        "listen_port": M1_LISTEN_PORT,
        "send_port": M1_SEND_PORT,
    },
    "M2": {
        "address": "localhost",
        "listen_port": M2_LISTEN_PORT,
        "send_port": SERVER_LISTEN_PORT,
    },
    "M3": {
        "address": "localhost",
        "listen_port": M3_LISTEN_PORT,
        "send_port": M3_SEND_PORT,
    },
    "M4": {
        "address": "localhost",
        "listen_port": M4_LISTEN_PORT,
        "send_port": M4_SEND_PORT,
    },
}
