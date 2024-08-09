import socket
import threading
import asyncio
import sys
import json
import time


from utils import (
    parse_server_args,
    calculate_crc8,
    send_message,
    receive_message,
    send_broadcast_message,
    receive_message_no_ack,
)
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
        print("Clients:", self.clients)
        self.lock = threading.Lock()
        self.token = None
        self.current_player = 0
        self.listen_socket = None
        self.send_socket = None
        self.next_node_address = NETWORK_CONNECTIONS["M1"]["address"]
        self.send_port = NETWORK_CONNECTIONS["M0"]["send_port"]
        self.current_turn = {}
        self.game_winners = []

    def start(self):
        config = NETWORK_CONNECTIONS["M0"]
        # listen address and port must be the previous node's send address and port
        previous_node = "M{}".format(PLAYERS - 1)
        previous_node = NETWORK_CONNECTIONS[previous_node]
        print("Previous node:", previous_node)
        listen_address = previous_node["address"]
        listen_port = previous_node["send_port"]
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
            with self.lock:  # lock the token
                current_conn = self.clients[self.token]

                print("Current player:", current_conn)

                if game.state == "DEALING":
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

                elif game.state == "BETTING":
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

                    # register the player's bet
                    if player_bet == None:
                        continue
                    else:
                        game.round.play_bet(player_bet["msg"]["content"], player.port)

                    # send the player's bet to each player
                    for player in game.players:

                        # if the player is the current player, skip
                        if player.port == current_player.port:
                            continue
                        print("Sending player's bet to player ", player.port)
                        message = MESSAGE_TEMPLATE
                        message["msg"]["type"] = "PLAYER_BET"
                        message["msg"]["src"] = "server"
                        message["msg"]["dst"] = f"M{player.port}"
                        message["msg"]["content"] = {
                            "player": current_player.port,
                            "bet": player_bet["msg"]["content"],
                        }
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

                    if all(player.has_bet for player in game.players):
                        self.token = (self.token + 1) % PLAYERS
                        game.state = "PLAYING"
                        for player in game.players:
                            players_queue.put_nowait(player)
                        continue

                    print("==================BETTING==================")

                elif game.state == "PLAYING":
                    print("==================PLAYING==================")

                    print(game.round.bets)
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
                    message = json.dumps(message, indent=2).encode("utf-8")
                    send_message(
                        self.listen_socket,
                        self.send_socket,
                        message,
                        (self.next_node_address, self.send_port),
                    )

                    # receive the player's card
                    card_played = receive_message(
                        self.listen_socket,
                        self.send_socket,
                        (self.next_node_address, self.send_port),
                    )

                    # extract the card from the message
                    card_played = card_played["msg"]["content"]
                    print(
                        "Card played by player", current_player.port, ":", card_played
                    )
                    # transform the card into a dict with suit and rank
                    card_played = json.loads(card_played)
                    current_player.has_played = True

                    """
                    The card sent by the player is the index of the card in the player's hand
                    """

                    print("Card played:", current_player.cards[card_played])

                    # remove the card from the player's hand
                    current_played_card = current_player.cards.pop(card_played)

                    # calculate the total value of the card base on the rank and suit
                    card_with_suit = current_played_card.rank + current_played_card.suit

                    print("sending card played to other players")
                    # send the card played by the player to the other players
                    for player in game.players:
                        content = "\tO jogador {} jogou a carta {}".format(
                            current_player.port, card_with_suit
                        )
                        if player.port == current_player.port:
                            content = "\tVocê jogou a carta {}".format(card_with_suit)

                        message = MESSAGE_TEMPLATE
                        message["msg"]["type"] = "PLAYER_CARD"
                        message["msg"]["src"] = "server"
                        message["msg"]["dst"] = f"M{player.port}"
                        message["msg"]["content"] = content
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

                    game.round.play_card(
                        card_with_suit,
                        current_played_card.value,
                        current_player.port,
                    )

                    # if every player have played
                    if all(player.has_played for player in game.players):
                        game.state = "TURN_END"
                        for player in game.players:
                            players_queue.put_nowait(player)
                        continue

                    player = players_queue.get_nowait()
                    print("==================PLAYING==================")
                elif game.state == "TURN_END":
                    """
                    In this state the winner of the turn is calculated,
                    the players turns won are updated,
                    every player is notified of the winner and
                    every player is notified of the current bet status
                    """
                    print("==================TURN_END==================")
                    # calculate the winner of the turn
                    winner_player = game.round.calculate_winner_round()

                    print("Winner of the turn:", winner_player)
                    for player in game.players:
                        if player.port == winner_player:
                            player.bets_won += 1
                            bets_won = player.bets_won

                    game.round.win_turn(winner_player)

                    bets = []
                    for player in game.players:
                        bets.append(
                            {
                                "player": player.port,
                                "bet": player.current_bet,
                                "turns_won": player.bets_won,
                            }
                        )

                    game.round.clean_turn()
                    for player in game.players:
                        player.has_played = False

                    turn_ending_info = {
                        "winner": winner_player,
                        "bets": bets,
                    }

                    # send the winner to each player
                    for player in game.players:
                        message = MESSAGE_TEMPLATE
                        message["msg"]["type"] = "TURN_WINNER"
                        message["msg"]["src"] = "server"
                        message["msg"]["dst"] = f"M{player.port}"
                        message["msg"]["content"] = turn_ending_info
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

                    # if all players have zero cards
                    if all(not player.cards for player in game.players):
                        game.state = "CALCULATING"
                        for player in game.players:
                            players_queue.put_nowait(player)
                        continue

                    # change to the next state
                    game.state = "PLAYING"

                elif game.state == "CALCULATING":
                    print("==================CALCULATING==================")
                    print("Calculating winner")
                    # calculate the winner of the round
                    game.calculate_player_lifes()
                    game.round.clean_round()
                    # game.calculate_next_dealer()
                    game.check_lifes()

                    round_ending_info = {
                        "winner": winner_player,
                        "players": [
                            {
                                "port": player.port,
                                "lifes": player.lifes,
                            }
                            for player in game.players
                        ],
                    }

                    # send the winner to each player
                    for player in game.players:
                        message = MESSAGE_TEMPLATE
                        message["msg"]["type"] = "WINNER"
                        message["msg"]["src"] = "server"
                        message["msg"]["dst"] = f"M{player.port}"
                        message["msg"]["content"] = round_ending_info
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
                    exit()
                    print("==================CALCULATING==================")

            # this passes the token to the next player
            with self.lock:
                print("Passing the token to the next player")
                self.token = (self.token + 1) % PLAYERS


if __name__ == "__main__":
    args = parse_server_args()
    server = Server(SERVER_ADDRESS, args.cards_per_player, args.turns)
    server.start()
