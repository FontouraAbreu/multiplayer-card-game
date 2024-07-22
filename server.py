import socket
import threading
import asyncio
import time
import sys
import json


from pprint import pprint

from utils import parse_args, calculate_crc8
from game import Game

from config import SERVER_ADDRESS, SERVER_PORT, PLAYERS

players_queue = asyncio.Queue()


class Server:
    def __init__(self, host, port, cards_per_player, turns):
        self.host = host
        self.port = port
        self.cards_per_player = cards_per_player
        self.turns = turns
        self.clients = []
        self.lock = threading.Lock()
        self.token = None
        self.current_player = 0

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
            try:
                threading.Thread(target=self.manage_game).start()
            except Exception as e:
                print(f"Error starting the game: {e}")

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
        game.put_players_queue(players_queue)
        # set the starting state

        while not players_queue.empty() and game.state != "GAME_OVER":
            with self.lock:  # lock the token
                current_conn = self.clients[self.token]

                match game.state:
                    case "DEALING":
                        # individual lifes
                        print("Starting dealing state")
                        current_player = game.players[self.token]
                        print("Current player:", current_player.port)

                        serializible_cards = []
                        for card in current_player.cards:
                            suit = json.dumps(card.get_suit())  # Serializa a string para JSON
                            rank = json.dumps(card.get_rank())  # Serializa a string para JSON
                            serializible_cards.append(
                                {
                                    "suit": suit.strip('"'),
                                    "rank": rank.strip('"'),
                                }  # Remove as aspas extras
                            )

                        print("info that will be sent:", serializible_cards)
                        print("size of the clean message:" )

                        sys.getsizeof(message_template),
                        # send to the player the cards he has
                        message = message_template
                        message["msg"]["type"] = "DEALING"
                        message["msg"]["content"] = serializible_cards
                        message["has_message"] = True
                        message["bearer"] = self.token
                        message["crc8"] = calculate_crc8(json.dumps(message, indent=2).encode("utf-8"))

                        message = json.dumps(message, indent=2).encode("utf-8")

                        print("size of the filled message:", sys.getsizeof(message))
                        print("Sending message:", message)
                        current_conn.sendall(message)

                        # THIS NEEDS TO BE INTEGRATED WITH THE CLIENT
                        # answer = None
                        # while answer != "ACK":
                        #     answer = current_conn.recv(sys.getsizeof(message))
                        #     print("Answer received:", answer)
                        # THIS NEEDS TO BE INTEGRATED WITH THE CLIENT
                        # send the player the lifes he has
                        message = message_template
                        # hop to the next player

                        current_player.has_cards = True

                        # all()
                        # verifica se todos os jogadores tem cartas, se tiver muda de estado
                        if all(player.has_cards for player in game.players):
                            game.state = "BETTING"
                            for player in game.players:
                                players_queue.put_nowait(player)
    

                    case "BETTING":
                        print("starting betting state")
                        break

            with self.lock:
                self.token = (self.token + 1) % PLAYERS

    def broadcast(self, message):
        for client in self.clients:
            client.sendall(message.encode())


if __name__ == "__main__":
    args = parse_args()
    server = Server(SERVER_ADDRESS, SERVER_PORT, args.cards_per_player, args.turns)
    server.start()
