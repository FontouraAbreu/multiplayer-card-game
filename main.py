import asyncio
import logging
import sys
import time
import socket
import json

from game import Game
from player import Player
from round import Round
from deck import Deck
from utils import (
    calculate_crc8,
    send_message,
    parse_client_args,
    receive_message,
    receive_message_no_ack,
    send_ack_or_nack,
    send_broadcast_message,
)

from config import (
    SERVER_ADDRESS,
    PLAYERS,
    RECV_BUFFER,
    NETWORK_CONNECTIONS,
    MESSAGE_TEMPLATE,
    LISTEN_PORT,
    SEND_PORT,
)


player_id = None
"""
The player id that will be used to identify the player in the network.
it can be any number between 1 and the number of players
"""

# TODO USAR A CLASSE DECK PARA GERENCIAR AS INFORMAÇÕES DE CADA RODADA
current_round_status = {
    "round_number": 1,
    "shackle": None,
    "num_players": PLAYERS,
    "cards_per_player": None,
    "current_player_cards": [],
    "current_player_lifes": None,
    "current_player_bet": None,
    "current_won_rounds": 0,
    "current_player_number": 1,
    "current_winning_card": None,
    "current_winning_player": None,
    "current_winning_player_lives": 0,
    "current_players_bets": [],
    "cards_played": [],
}
# TODO USAR A CLASSE DECK PARA GERENCIAR AS INFORMAÇÕES DE CADA RODADA

game_winners = []


def main(args):
    """
    Launch a client/server
    """
    # Make a while loop to keep the game running
    print("Starting game...")

    # self node config
    node_config = NETWORK_CONNECTIONS[f"M{player_id}"]
    # the listen address must be the previous node address
    listen_address = node_config["address"]
    # send_port = node_config["send_port"]
    if player_id == PLAYERS:
        print(f"M0")
        next_node_address = NETWORK_CONNECTIONS["M0"]["address"]
    else:
        print(f"M{player_id + 1}")
        next_node_address = NETWORK_CONNECTIONS[f"M{player_id + 1}"]["address"]

    # configuring listen socket
    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    listen_socket.bind((listen_address, LISTEN_PORT))

    print("ouvindo em", listen_address, LISTEN_PORT)

    print("Esperando os jogadores se conectarem e o jogo começar...")
    print(
        f"Esperando pelas conexões... Aperte Enter quando todos os jogadores estiverem conectados"
    )
    input()

    # configuring send socket
    send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    print("enviando em ", next_node_address, SEND_PORT)

    message = MESSAGE_TEMPLATE

    # connect to the next node
    while message["msg"]["type"] != "GAME_OVER":

        # client_socket, address = listen_socket.accept()
        current_player = current_round_status["current_player_number"]

        # Receive the message from the server
        message = receive_message_no_ack(
            listen_socket,
            send_socket,
            "M{}".format(player_id),
            (next_node_address, SEND_PORT),
        )
        print(f"Received message from server: {message}")
        if message is None:
            # print("Message is None")
            message = MESSAGE_TEMPLATE
            continue

        # if the message is not destined to the player
        # return to message template and continue
        elif message == -1:
            message = MESSAGE_TEMPLATE
            continue

        # if the message is destined to the player
        # send an ACK | NACK based on the crc8
        sent = send_ack_or_nack(
            listen_socket,
            message,
            "M{}".format(player_id),
            (next_node_address, SEND_PORT),
        )
        if sent is None:
            # print("Message sent is None")
            message = MESSAGE_TEMPLATE
            continue

        # if the message is only the player's bet
        if message["msg"]["type"] == "PLAYER_BET":
            current_round_status["current_players_bets"].append(
                {
                    "player": message["msg"]["content"]["player"],
                    "bet": message["msg"]["content"]["bet"],
                }
            )
            print(
                "Jogador {} apostou {} rodada(s)!".format(
                    message["msg"]["content"]["player"],
                    message["msg"]["content"]["bet"],
                )
            )
            continue

        if message["msg"]["type"] == "PLAYER_CARD":
            current_round_status["cards_played"].append(message["msg"]["content"])
            # print(message["msg"]["content"])
            continue

        msg_type = message["msg"]["type"]

        # print(f"Received message from server: {message}")

        if msg_type == "DEALING":
            """
            In this state, the game will show the player's lifes and distribute its cards
            This state will only be executed if the client receives a token with the "DEALING" type
            """
            message_content = message["msg"]["content"]
            # extract cards and suits from the message

            print(f"=----= Rodada {message_content['round_num']} =----=")
            # save the round number in the local round status
            current_round_status["round_number"] = message_content["round_num"]

            print("")
            print(f"A manilha é {message_content['shackle']}")
            # save the shackle in the local round status
            current_round_status["shackle"] = message_content["shackle"]

            # save the number of cards per player in the local round status
            current_round_status["cards_per_player"] = message_content[
                "cards_per_player"
            ]

            # save the current player number in the local round status
            current_round_status["current_player_number"] = message_content[
                "player_number"
            ]

            # save the player's lifes in the local round status
            current_round_status["current_player_lifes"] = message_content["lifes"]

            # save the player's cards in the local round status
            for card in message_content["cards"]:
                # converting the card suit to the unicode representation
                card["suit"] = (
                    card["suit"].replace("\\\\", "\\").encode().decode("unicode-escape")
                )
                current_round_status["current_player_cards"].append(
                    f"{card['rank']} {card['suit']}"  # DEVERIAMOS ESTAR CRIANDO UM OBJETO CARD AQUI
                )

            # print the player's lifes with hearts
            print("")
            print("Suas vidas são:")
            for _ in range(current_round_status["current_player_lifes"]):
                print("❤️", end="  ")

            # print the player's cards
            print("")
            print("\nSuas cartas são:")
            for card in current_round_status["current_player_cards"]:
                print(card)
        elif msg_type == "BETTING":
            """
            In this state, the game will show the player's lifes and asks for the player's bet
            """
            print("")
            print("Hora de apostar:")
            # ask the player for the bet
            print("Quantas rodadas você faz?")
            bet = int(input())
            # check if the bet is a number
            while bet != int(bet):
                print("Digite apenas o número de rodadas que você faz!")
                print("Faça uma nova aposta:")
                bet = input()

            # retrieve the sum of the bets
            sum_of_bets = message["msg"]["content"] + bet

            # Last player must && sum of bets cannot be equal to the number of rounds
            while (
                current_round_status["current_player_number"] == PLAYERS + 1
                and sum_of_bets == current_round_status["cards_per_player"]
            ):
                print("A soma das apostas deve ser diferente do número de rodadas!")
                print(
                    "Você pode apostar qualquer número de rodadas diferente de",
                    current_round_status["cards_per_player"]
                    - message["msg"]["content"],
                )
                print("Faça uma nova aposta:")
                bet = int(input())
                sum_of_bets = message["msg"]["content"] + bet

            print("Esperando os outros jogadores apostarem...")

            # Send the player's bet
            current_player_bet = MESSAGE_TEMPLATE
            current_player_bet["msg"]["type"] = "BETTING"
            current_player_bet["msg"]["src"] = f"M{player_id}"
            current_player_bet["msg"]["dst"] = "server"
            current_player_bet["msg"]["content"] = bet
            current_player_bet["has_message"] = True
            current_player_bet["bearer"] = None
            current_player_bet["crc8"] = 1

            # send the current player bet to the server first
            current_player_bet = json.dumps(current_player_bet, indent=2).encode(
                "utf-8"
            )
            send_message(
                listen_socket,
                send_socket,
                current_player_bet,
                (next_node_address, SEND_PORT),
            )

        elif msg_type == "PLAYING":
            """
            In this state, the game will show the player's lifes and asks for the player's card
            """
            print("=----= JOGANDO =----=")

            # clear the screen
            # print round status

            if len(current_round_status["current_players_bets"]) > 0:
                print("")
                print("Apostas:")
                for bet in current_round_status["current_players_bets"]:
                    print(f"\tJogador {bet['player']} Apostou {bet['bet']} rodada(s)!")

            # print the played cards
            if len(current_round_status["cards_played"]) > 0:
                print("")
                print("Cartas jogadas:")
                for card_played in current_round_status["cards_played"]:
                    print(card_played)

            # if there is a message content
            # extract the current round winning status
            if message["msg"]["content"] != None:
                current_round_status["current_winning_card"] = message["msg"][
                    "content"
                ]["current_winning_card"]
                current_round_status["current_winning_player"] = message["msg"][
                    "content"
                ]["current_winning_player"]
                current_round_status["current_winning_player_lives"] = message["msg"][
                    "content"
                ]["current_winning_player_lives"]
                print(
                    f"O jogador {current_round_status['current_winning_player']} está ganhando a rodada com a carta {current_round_status['current_winning_card']}"
                )

            # print the current shackle
            print(f"A manilha é {current_round_status['shackle']}")
            print("")

            print("\nSuas cartas são:")
            for i, card in enumerate(current_round_status["current_player_cards"]):
                print(f"{i} - {card}")

            # ask the player for the card
            print("Qual carta você joga?")
            card_num = input()
            while int(card_num) < 0 or int(card_num) > len(
                current_round_status["current_player_cards"]
            ):
                print("Carta inválida, tente novamente")
                card_num = input()

            print("Esperando os outros jogadores jogarem...")
            # Get card from player's hand
            card = current_round_status["current_player_cards"].pop(int(card_num) - 1)

            # Send the player's card
            card_played = MESSAGE_TEMPLATE
            card_played["msg"]["type"] = "PLAYING"
            card_played["msg"]["content"] = card_num
            card_played["has_message"] = True
            card_played["bearer"] = None
            card_played["crc8"] = 1
            card_played["broadcast"] = False

            # converts the card_played to bytes
            card_played = json.dumps(card_played, indent=2).encode("utf-8")
            send_message(
                listen_socket,
                send_socket,
                card_played,
                (next_node_address, SEND_PORT),
            )

        elif msg_type == "TURN_WINNER":
            """
            In this state, the game will show the winner of the round and some information about the players
            """
            print("=----= FIM DO TURNO =----=")

            # reset cards played
            current_round_status["cards_played"] = []

            # print the winner of the round
            if message["msg"]["content"]["winner"] == player_id:
                print("Parabéns! Você ganhou o turno")
                current_round_status["current_won_rounds"] += 1
            else:
                print(f"O jogador {message['msg']['content']['winner']} ganhou o turno")
            print("")

            # print the players bets
            print("Situação das apostas:")
            for bet in message["msg"]["content"]["bets"]:
                if bet["player"] == player_id:
                    print(
                        f"Você apostou {bet['bet']} rodada(s) e ganhou {bet['turns_won']}"
                    )
                else:
                    print(
                        f"Jogador {bet['player']} apostou {bet['bet']} rodada(s) e ganhou {bet['turns_won']}"
                    )

        elif msg_type == "WINNER":
            """
            In this state, the game will show the winner of the round and some information about the players
            """
            # clear the terminal

            print("=----= FIM DO JOGO =----=")

            # print the winner of the round
            print("O jogo chegou ao fim!\n")

            # print the players lifes with hearts
            print("Os jogadores que sobreviveram foram:")
            for player in message["msg"]["content"]["players"]:
                lifes_emoji = "❤️  " * player["lifes"]
                if player["port"] == player_id:
                    if player["lifes"] <= 0:
                        print(
                            "Você perdeu todas as suas vidas e não sobreviveu ao jogo!"
                        )
                    else:
                        print(f"Você - {lifes_emoji}")
                else:
                    print(f"Jogador {player['port']} - {lifes_emoji}")

        # hop to the next player
        current_round_status["current_player_number"] += (
            1 if current_player < PLAYERS else 1
        )


if __name__ == "__main__":
    # Change to logging.DEBUG to see debug statements...
    logging.basicConfig(level=logging.INFO)
    args = parse_client_args()
    player_id = args.player_id
    main(args)
