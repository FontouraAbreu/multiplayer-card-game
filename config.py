SERVER_ADDRESS = ""
PLAYERS = 2
RECV_BUFFER = 1024

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
