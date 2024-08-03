import socket
import threading
import asyncio
import sys
import json
import time


from utils import parse_server_args, calculate_crc8, send_message, receive_message
from game import Game

from config import (
    SERVER_ADDRESS,
    PLAYERS,
    RECV_BUFFER,
    NETWORK_CONNECTIONS,
    MESSAGE_TEMPLATE,
)

players_queue = asyncio.Queue()


class Server:
    def __init__(self, host, cards_per_player, turns):
        self.host = host
        self.cards_per_player = cards_per_player
        self.turns = turns
        self.clients = [i for i in range(1, PLAYERS + 1)]
        self.lock = threading.Lock()
        self.token = None
        self.current_player = 0
        self.listen_socket = None
        self.send_socket = None
        self.next_node_address = NETWORK_CONNECTIONS["M1"]["address"]
        self.send_port = NETWORK_CONNECTIONS["M0"]["send_port"]

    def start(self):
        config = NETWORK_CONNECTIONS["M0"]
        listen_address = config["address"]
        listen_port = config["listen_port"]
        send_port = config["send_port"]
        next_node_address = NETWORK_CONNECTIONS["M1"]["address"]

        # configuring listening socket
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.listen_socket.bind((listen_address, listen_port))
        print(f"Server listening on {listen_address}:{listen_port}")
        print("Waiting for connection... Press Enter when all players are listening")
        input()

        # configuring sending socket
        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print(f"Server connected to {next_node_address}:{send_port}")

        try:
            threading.Thread(target=self.manage_game).start()
        except Exception as e:
            print(f"Error starting the game: {e}")

    def manage_game(self):
        self.token = 0

        # Start the game
        game = Game(PLAYERS, self.cards_per_player, self.turns)
        game.state = "DEALING"
        game.put_players_queue(players_queue)
        # set the starting state

        while not players_queue.empty() and game.state != "GAME_OVER":
            input("Press Enter to continue...")
            with self.lock:  # lock the token
                current_conn = self.clients[self.token]

                print("Current player:", current_conn)

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

                        # send to the player the cards he has
                        message = MESSAGE_TEMPLATE
                        message["msg"]["src"] = "server"
                        message["msg"]["dst"] = f"M{current_player.port}"
                        message["msg"]["type"] = "DEALING"
                        message["msg"]["content"] = serializable_message
                        message["has_message"] = True
                        message["bearer"] = self.token
                        message["crc8"] = 1

                        # converts the message to bytes
                        message = json.dumps(message, indent=2).encode("utf-8")
                        send_message(
                            self.listen_socket,
                            self.send_socket,
                            message,
                            (self.next_node_address, self.send_port),
                        )

                        # send the player the lifes he has
                        message = MESSAGE_TEMPLATE
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
                        message = MESSAGE_TEMPLATE
                        message["msg"]["type"] = "BETTING"
                        message["msg"]["src"] = "server"
                        message["msg"]["dst"] = f"M{current_player.port}"
                        message["msg"][
                            "content"
                        ] = sum_of_bets  # the sum of the bets of all players
                        message["has_message"] = True
                        message["bearer"] = self.token
                        message["crc8"] = 1

                        # converts the message to bytes
                        message = json.dumps(message, indent=2).encode("utf-8")
                        send_message(
                            self.listen_socket,
                            self.send_socket,
                            message,
                            (self.next_node_address, self.send_port),
                        )

                        current_player = game.players[self.token]

                        # receive the player's bet
                        player_bet = receive_message(
                            self.listen_socket,
                            self.send_socket,
                            (self.next_node_address, self.send_port),
                        )

                        if player_bet == None:
                            continue
                        else:
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

                        message = MESSAGE_TEMPLATE
                        message["msg"]["type"] = "PLAYING"
                        message["msg"]["src"] = "server"
                        message["msg"]["dst"] = f"M{current_player.port}"
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
                        send_message(
                            self.listen_socket,
                            self.send_socket,
                            message,
                            (self.next_node_address, self.send_port),
                        )

                        # receive the player's card
                        card_played = receive_message(
                            self.listen_socket, self.send_socket, self.next_node_address
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
                print("Passing the token to the next player")
                self.token = (self.token + 1) % PLAYERS

    # def broadcast(self, message):
    #     for client in self.clients:
    #         client.sendall(message.encode())


if __name__ == "__main__":
    args = parse_server_args()
    server = Server(SERVER_ADDRESS, args.cards_per_player, args.turns)
    server.start()
