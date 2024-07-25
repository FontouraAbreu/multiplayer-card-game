import socket
import threading
import asyncio
import time
import sys
import json


from pprint import pprint

from utils import parse_args, calculate_crc8, send_message
from game import Game

from config import SERVER_ADDRESS, SERVER_PORT, PLAYERS, RECV_BUFFER

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

                        print("==================DEALING==================")
                        current_player = game.players[self.token]
                        current_player.has_bet = False
                        print("Current player:", current_player.port)
                        shackle = game.round.deck.shackle_rank
                        round_num = game.round.round_number

                        # message to be sent to the player
                        serializable_message = {
                            "cards": [],
                            "lifes": current_player.lifes,
                            "shackle": shackle,
                            "round_num": round_num,
                            "cards_per_player": self.cards_per_player,
                            "player_number": current_player.port,
                        }

                        for card in current_player.cards:
                            suit = json.dumps(card.get_suit())
                            rank = json.dumps(card.get_rank())
                            serializable_message["cards"].append(
                                {
                                    "suit": suit.strip('"'),
                                    "rank": rank.strip('"'),
                                }
                            )

                        print("info that will be sent:", serializable_message)
                        print("size of the clean message:")

                        sys.getsizeof(message_template),
                        # send to the player the cards he has
                        message = message_template
                        message["msg"]["type"] = "DEALING"
                        message["msg"]["content"] = serializable_message
                        message["has_message"] = True
                        message["bearer"] = self.token
                        message["crc8"] = 1

                        # converts the message to bytes
                        message = json.dumps(message, indent=2).encode("utf-8")
                        send_message(current_conn, message)

                        # send the player the lifes he has
                        message = message_template
                        # hop to the next player

                        current_player.has_cards = True

                        # verifica se todos os jogadores tem cartas, se tiver muda de estado
                        if all(player.has_cards for player in game.players):
                            game.state = "BETTING"
                            for player in game.players:
                                players_queue.put_nowait(player)
                        print("==================DEALING==================")

                    case "BETTING":
                        print("==================BETTING==================")

                        current_player = game.players[self.token]
                        current_player_lifes = current_player.lifes
                        print(
                            f"Player",
                            current_player.port,
                            "has",
                            current_player_lifes,
                            "lifes",
                        )

                        player = players_queue.get_nowait()

                        sum_of_bets = sum(player.current_bet for player in game.players)
                        # sends the player the BETTING message
                        message = message_template
                        message["msg"]["type"] = "BETTING"
                        message["msg"][
                            "content"
                        ] = sum_of_bets  # the sum of the bets of all players
                        message["has_message"] = True
                        message["bearer"] = self.token
                        message["crc8"] = 1

                        # converts the message to bytes
                        message = json.dumps(message, indent=2).encode("utf-8")
                        send_message(current_conn, message)

                        current_player = game.players[self.token]

                        # receive the player's bet
                        player_bet = current_conn.recv(RECV_BUFFER)
                        player_bet = json.loads(player_bet.decode("utf-8"))
                        # check if the message crc8 is valid
                        answer_crc8 = message_template
                        if player_bet["crc8"] != 1:
                            print("CRC8 inválido, enviando NACK")
                            # answer the message with a NACK
                            answer_crc8["has_message"] = False
                            answer_crc8["bearer"] = None
                            answer_crc8["msg"]["type"] = "NACK"
                            answer_crc8["crc8"] = 1
                            current_conn.sendall(
                                json.dumps(answer_crc8).encode("utf-8")
                            )
                            continue
                        else:
                            print("CRC8 válido, enviando ACK")
                            # answer the message with a ACK
                            answer_crc8["has_message"] = False
                            answer_crc8["bearer"] = None
                            answer_crc8["msg"]["type"] = "ACK"
                            answer_crc8["crc8"] = 1
                            current_conn.sendall(
                                json.dumps(answer_crc8).encode("utf-8")
                            )
                            current_player.has_bet = True
                            current_player.current_bet = player_bet["msg"]["content"]

                        print(
                            "Player",
                            current_player.port,
                            "bet: ",
                            player_bet["msg"]["content"],
                        )

                        game.round.play_bet(player_bet, player.port)

                        if all(player.has_bet for player in game.players):
                            game.state = "PLAYING"
                            for player in game.players:
                                players_queue.put_nowait(player)
                            continue

                        print("==================BETTING==================")

                    case "PLAYING":
                        print("==================PLAYING==================")
                        current_player = game.players[self.token]
                        current_player_lifes = current_player.lifes
                        print(
                            f"Player",
                            current_player.port,
                            "has",
                            current_player_lifes,
                            "lifes",
                        )

                        message = message_template
                        message["msg"]["type"] = "PLAYING"
                        message["has_message"] = True
                        message["bearer"] = self.token

                        # if the current player is not the first player
                        # send also the cards played by the other players as well as their lives
                        if (
                            game.round.current_player != 1
                            and game.round.current_winning_player != None
                        ):
                            message["msg"]["content"] = {
                                "current_winning_card": game.round.current_winning_card,
                                "current_winning_player": game.round.current_winning_player,
                                "current_winning_player_lives": game.round.current_winning_player_lives,
                            }
                        else:
                            message["msg"]["content"] = None
                        message["crc8"] = 1

                        # converts the message to bytes
                        message = json.dumps(message, indent=2).encode("utf-8")
                        send_message(current_conn, message)

                        # receive the player's card
                        card_played = current_conn.recv(RECV_BUFFER)
                        card_played = json.loads(card_played.decode("utf-8"))
                        # check if the message crc8 is valid
                        answer_crc8 = message_template
                        if card_played["crc8"] != 1:
                            print("CRC8 inválido, enviando NACK")
                            # answer the message with a NACK
                            answer_crc8["has_message"] = False
                            answer_crc8["bearer"] = None
                            answer_crc8["msg"]["type"] = "NACK"
                            answer_crc8["crc8"] = 1
                            current_conn.sendall(
                                json.dumps(answer_crc8).encode("utf-8")
                            )
                            continue
                        else:
                            print("CRC8 válido, enviando ACK")
                            # answer the message with a ACK
                            answer_crc8["has_message"] = False
                            answer_crc8["bearer"] = None
                            answer_crc8["msg"]["type"] = "ACK"
                            answer_crc8["crc8"] = 1
                            current_conn.sendall(
                                json.dumps(answer_crc8).encode("utf-8")
                            )

                        # extract the card from the message
                        card_played = card_played["msg"]["content"]
                        # trasnform the card into a dict with suit and rank
                        card_played = json.loads(card_played)
                        """
                        The card sent by the player is the index of the card in the player's hand
                        """

                        print("Card played:", current_player.cards[card_played])

                        # remove the card from the player's hand
                        current_played_card = current_player.cards.pop(card_played)

                        # calculate the total value of the card base on the rank and suit
                        card_with_suit = (
                            current_played_card.rank + current_played_card.suit
                        )

                        game.round.play_card(
                            card_with_suit,
                            current_played_card.value,
                            current_player.port,
                        )

                        player = players_queue.get_nowait()

            # this passes the token to the next player
            with self.lock:
                self.token = (self.token + 1) % PLAYERS

    def broadcast(self, message):
        for client in self.clients:
            client.sendall(message.encode())


if __name__ == "__main__":
    args = parse_args()
    server = Server(SERVER_ADDRESS, SERVER_PORT, args.cards_per_player, args.turns)
    server.start()
