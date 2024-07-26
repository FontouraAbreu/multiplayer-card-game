import argparse
import json
import sys

from config import RECV_BUFFER, PLAYERS


def parse_server_args():
    parser = argparse.ArgumentParser(description="Start a server")
    parser.add_argument(
        "cards_per_player",
        metavar="cards_per_player",
        type=int,
        help="The number of cards each player should have",
    )
    parser.add_argument(
        "turns",
        metavar="turns",
        type=int,
        help="The number of turns to play",
    )
    return parser.parse_args()


def parse_client_args():
    parser = argparse.ArgumentParser(description="Start a client player")
    parser.add_argument(
        "player_id",
        metavar="player_id",
        type=int,
        help="The player id that will be used to identify the player in the network. Keep in mind that the player id should be unique and in a range between 1 and {}".format(
            PLAYERS
        ),
    )
    return parser.parse_args()


def send_message(conn, message: bytes):
    """
    Sends a message to the client and waits for an ACK response
    while the message is not an ACK message it will keep sending the message
    """
    # print("size of the filled message:", sys.getsizeof(message))
    print("Sending message:", message)

    conn.sendall(message)
    # waits for ACK response
    print("waiting for ACK")
    answer = conn.recv(RECV_BUFFER)
    answer = json.loads(answer.decode("utf-8"))
    msg_type = answer["msg"]["type"]
    # keep sending the message until an ACK is received
    while msg_type != "ACK":
        # send the message again
        message = conn.sendall(message)
        # receive the answer again
        answer = conn.recv(RECV_BUFFER)
        answer = json.loads(answer.decode("utf-8"))
        msg_type = answer["msg"]["type"]

    print("ACK received")


def calculate_crc8(message):
    crc = 0
    for byte in message:
        crc += byte
    return crc % 256
