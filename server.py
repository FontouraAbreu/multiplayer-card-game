import socket
import threading
import asyncio
import time
import sys
import json

from utils import parse_args
from game import Game

from config import SERVER_ADDRESS, SERVER_PORT, PLAYERS

queue = asyncio.Queue()


class Server:
    def __init__(self, host, port, cards_per_player, turns):
        self.host = host
        self.port = port
        self.cards_per_player = cards_per_player
        self.turns = turns
        self.clients = []
        self.lock = threading.Lock()
        self.current_player = 0
        self.token = None

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((self.host, self.port))
            server_socket.listen(PLAYERS)
            print(f"Server started at {self.host}:{self.port}")
            while len(self.clients) < PLAYERS:
                conn, addr = server_socket.accept()
                with self.lock:
                    self.clients.append(conn)
                print(f"Player connected from {addr}")
            threading.Thread(target=self.manage_game).start()

    def manage_game(self):
        self.token = 0
        message_template = {
            "has_message": False,
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

        # Start the game
        game = Game(PLAYERS, self.cards_per_player, self.turns)
        game.state = "DEALING"
        game.put_players_queue(queue)
        # set the starting state

        while not queue.empty() and game.state != "GAME_OVER":
            with self.lock:
                current_conn = self.clients[self.token]

                match game.state:
                    case "DEALING":
                        # individual lifes
                        current_player = game.players[self.current_player]
                        print("Current player:", current_player.port)

                        current_shackle = game.round.shackle
                        current_player.cards = game.round.deck.distribute_cards(
                            [current_player], game.cards_per_player
                        )

                        # send to the player the cards he has
                        message = message_template
                        message["msg"]["type"] = "DEALING"
                        message["msg"]["content"] = current_player.cards
                        print("Cards sent to player:", current_player.cards)
                        message["has_message"] = True
                        message["bearer"] = self.token
                        message["crc8"] = self.calculate_crc8(
                            json.dumps(message, indent=2).encode("utf-8")
                        )
                        message = json.dumps(message, indent=2).encode("utf-8")

                        answer = None
                        while answer != "ACK":
                            print("Sending message:", message)
                            current_conn.sendall(message)
                            answer = current_conn.recv(sys.getsizeof(message))
                            print("Answer received:", answer)

                        # send the player the lifes he has
                        message = message_template

            # testing sending the dealing message
            message = message_template
            message["msg"]["type"] = "DEALING"
            message["msg"]["crc"] = 0
            message["has_message"] = True
            message["bearer"] = self.token
            message = json.dumps(message, indent=2).encode("utf-8")

            print("Sending message:", message)
            current_conn.sendall(message)
            current_conn.recv(
                sys.getsizeof(message)
            )  # Wait for the player to finish their turn
            # here we should check the answer for a ack or nack

            with self.lock:
                self.token = (self.token + 1) % PLAYERS

    def calculate_crc8(self, message):
        crc = 0
        for byte in message:
            crc += byte
        return crc % 256

    def broadcast(self, message):
        for client in self.clients:
            client.sendall(message.encode())


if __name__ == "__main__":
    args = parse_args()
    server = Server(SERVER_ADDRESS, SERVER_PORT, args.cards_per_player, args.turns)
    server.start()
