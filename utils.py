import argparse
import json
import socket
import time
import sys

from config import RECV_BUFFER, PLAYERS, MESSAGE_TEMPLATE


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
    print("Sending message and waiting for ACK/NACK:", message)
    print(conn)
    try:
        conn.sendall(message)
    except Exception as e:
        print("Error sending message:", e)
        return

    # waits for ACK response
    print("waiting for ACK")
    answer = conn.recv(RECV_BUFFER)
    answer = json.loads(answer.decode("utf-8"))
    msg_type = answer["msg"]["type"]
    # keep sending the message until an ACK is received
    while msg_type != "ACK":
        # send the message again
        try:
            message = conn.sendall(message)
        except Exception as e:
            print("Error sending message:", e)
            return

        # receive the answer again
        answer = conn.recv(RECV_BUFFER)
        answer = json.loads(answer.decode("utf-8"))
        msg_type = answer["msg"]["type"]

    print("ACK received")


def receive_message(conn, player_id):
    """
    Receives a message from the client and sends an ACK response
    """
    message = conn.recv(RECV_BUFFER)
    if not message:
        return None

    message = json.loads(message.decode("utf-8"))

    # check if the message crc8 is valid
    answer_crc8 = MESSAGE_TEMPLATE
    if message["crc8"] != 1:
        print("CRC8 inválido, enviando NACK")
        # answer the message with a NACK
        answer_crc8["has_message"] = False
        answer_crc8["bearer"] = None
        answer_crc8["msg"]["type"] = "NACK"
        answer_crc8["crc8"] = 1
        try:
            conn.sendall(json.dumps(answer_crc8).encode("utf-8"))
        except socket.error as e:
            print(f"Error sending message - {e}")
            time.sleep(5)
            return None
        # finally:
        #     conn.close()
        #     print("Connection to the server closed")
        return None
    else:
        print("CRC8 válido, enviando ACK")
        # answer the message with a ACK
        answer_crc8["has_message"] = False
        answer_crc8["bearer"] = None
        answer_crc8["msg"]["type"] = "ACK"
        answer_crc8["crc8"] = 1
        try:
            conn.sendall(json.dumps(answer_crc8).encode("utf-8"))
        except socket.error as e:
            print(f"Error sending message - {e}")
            time.sleep(5)
            return None
        # finally:
        #     conn.close()
        #     print("Connection to the server closed")

    return message


def receive_message_no_ack(conn, player_id):
    """
    Receives a message from the client without sending an ACK response
    """
    message = conn.recv(RECV_BUFFER)
    if not message:
        return None

    message = json.loads(message.decode("utf-8"))

    # check if the message is destined to the player
    if message["msg"]["dst"] != player_id:
        print("Message not destined to player")
        return -1

    return message


def send_ack_or_nack(conn, message, current_player_id):
    """
    Sends an ACK or NACK message to the client
    """

    # set the message template
    ack_or_nack_answer = MESSAGE_TEMPLATE

    # fill the message template
    ack_or_nack_answer["has_message"] = False
    ack_or_nack_answer["msg"]["src"] = current_player_id
    ack_or_nack_answer["msg"]["dst"] = "server"
    ack_or_nack_answer["bearer"] = None
    ack_or_nack_answer["crc8"] = 1

    # check if the message crc8 is valid
    if message["crc8"] == 1:
        print("CRC8 válido, enviando ACK")
        # answer the message with a ACK
        ack_or_nack_answer["msg"]["type"] = "ACK"
    else:
        print("CRC8 inválido, enviando NACK")
        # answer the message with a NACK
        ack_or_nack_answer["msg"]["type"] = "NACK"

    print("Sending ACK/NACK message:", ack_or_nack_answer)

    # send the message to the next node
    try:
        conn.sendall(json.dumps(ack_or_nack_answer).encode("utf-8"))
    except socket.error as e:
        print(f"Error sending message - {e}")
        time.sleep(5)
        return None

    return 1


def calculate_crc8(message):
    crc = 0
    for byte in message:
        crc += byte
    return crc % 256
