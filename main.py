import asyncio
import logging
import sys
import socket
import json

from game import Game
from player import Player
from round import Round
from deck import Deck
from client import Client
from utils import calculate_crc8, send_message

from config import SERVER_ADDRESS, SERVER_PORT, PLAYERS, RECV_BUFFER


# TODO USAR A CLASSE DECK PARA GERENCIAR AS INFORMAÇÕES DE CADA RODADA
current_round_status = {
    "round_number": 1,
    "shackle": None,
    "num_players": PLAYERS,
    "cards_per_player": None,
    "current_player_cards": [],
    "current_player_lifes": None,
    "current_player_bet": None,
    "current_player_number": 0,
}
# TODO USAR A CLASSE DECK PARA GERENCIAR AS INFORMAÇÕES DE CADA RODADA


def main(args):
    """
    Launch a client/server
    """
    # Make a while loop to keep the game running
    print("Starting game...")
    client = Client(SERVER_ADDRESS, SERVER_PORT)
    message_template = {
        "has_message": False,  # has_message is a boolean that indicates if the token has a message
        "msg": {
            "src": None,
            "dst": None,
            "content": None,
            "crc": None,
            "type": None,
        },  # msg is the message that is being sent
        "bearer": None,  # bearer is the index o the node that has the token
    }
    message = message_template

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((client.host, client.port))

        while message["msg"]["type"] != "GAME_OVER":

            msg_type = message["msg"]["type"]

            # check if the current player is the dst of the message
            # if not message["msg"]["dst"] == game.players[game.current_player].port:
            #     continue

            match msg_type:
                case "DEALING":
                    """
                    In this state, the game will show the player's lifes and distribute its cards
                    This state will only be executed if the client receives a token with the "DEALING" type
                    """
                    message_content = message["msg"]["content"]
                    # extract cards and suits from the message

                    print(f"=----= Rodada {message_content['round_num']} =----=")
                    # save the round number in the local round status
                    current_round_status["round_number"] = message_content["round_num"]

                    print(f"A manilha {message_content['shackle']}")
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

                    # print the player's lifes with hearts
                    print("Suas vidas são:")
                    for _ in range(message_content["lifes"]):
                        print("❤️", end="  ")

                    # save the player's lifes in the local round status
                    current_round_status["current_player_lifes"] = message_content[
                        "lifes"
                    ]

                    print("\nSuas cartas são:")
                    for card in message_content["cards"]:
                        # converting the card suit to the unicode representation
                        card["suit"] = (
                            card["suit"]
                            .replace("\\\\", "\\")
                            .encode()
                            .decode("unicode-escape")
                        )
                        print(f"Carta: {card['rank']} {card['suit']}")
                        # save the player's cards in the local round status
                        current_round_status["current_player_cards"].append(
                            f"{card['rank']} {card['suit']}"  # DEVERIAMOS ESTAR CRIANDO UM OBJETO CARD AQUI
                        )

                    # save the player's cards

                case "BETTING":
                    """
                    In this state, the game will show the player's lifes and asks for the player's bet
                    """

                    # print the players lifes with hearts
                    print("Suas vidas são:")
                    for _ in range(current_round_status["current_player_lifes"]):
                        print("❤️", end="  ")

                    # print the player's cards
                    print("\nSuas cartas são:")
                    for card in current_round_status["current_player_cards"]:
                        print(card)

                    # ask the player for the bet
                    print("Quantas rodadas você faz?")
                    bet = int(input())
                    # retrieve the sum of the bets
                    sum_of_bets = message["msg"]["content"] + bet

                    # Last player must && sum of bets cannot be equal to the number of rounds
                    while (
                        current_round_status["current_player_number"] == PLAYERS
                        and sum_of_bets == current_round_status["cards_per_player"]
                    ):
                        print(
                            "A soma das apostas deve ser diferente do número de rodadas!"
                        )
                        print(
                            "Você pode apostar qualquer número de rodadas diferente de",
                            current_round_status["cards_per_player"]
                            - message["msg"]["content"],
                        )
                        print("Faça uma nova aposta:")
                        bet = int(input())
                        sum_of_bets = message["msg"]["content"] + bet

                    # Send the player's bet
                    message = message_template
                    message["msg"]["type"] = "BETTING"
                    message["msg"]["content"] = bet
                    message["has_message"] = True
                    message["bearer"] = None
                    message["crc8"] = 1

                    # converts the message to bytes
                    message = json.dumps(message, indent=2).encode("utf-8")
                    send_message(client_socket, message)

            # Receive the message from the server
            message = client_socket.recv(RECV_BUFFER)
            # decode the message
            message = json.loads(message.decode("utf-8"))

            # check if the message crc8 is valid
            answer_crc8 = message_template
            if message["crc8"] != 1:
                print("CRC8 inválido, enviando NACK")
                # answer the message with a NACK
                answer_crc8["has_message"] = False
                answer_crc8["bearer"] = None
                answer_crc8["msg"]["type"] = "NACK"
                answer_crc8["crc8"] = 1
                client_socket.sendall(json.dumps(answer_crc8).encode("utf-8"))
                continue
            else:
                print("CRC8 válido, enviando ACK")
                # answer the message with a ACK
                answer_crc8["has_message"] = False
                answer_crc8["bearer"] = None
                answer_crc8["msg"]["type"] = "ACK"
                answer_crc8["crc8"] = 1
                client_socket.sendall(json.dumps(answer_crc8).encode("utf-8"))

            # if game.state == "BETTING":
            #     if queue.empty():
            #         game.state = "PLAYING"
            #         for player in game.players:
            #             queue.put_nowait(player)
            #         continue

            #     player = queue.get_nowait()
            #     print(
            #         f"Sua vez, {player.name_port()}, você tem {player.lifes} vidas e essas são suas cartas:"
            #     )
            #     print(player.cards)

            #     # Get the player's bet
            #     print(f"{player.name_port()} quantas rodadas você faz?")
            #     bet = int(input())

            #     # Sum of bets cannot be equal to the number of rounds
            #     if (
            #         queue.qsize() == 0
            #         and sum([bet["bet"] for bet in game.round.bets])
            #         == game.round.cards_per_player
            #     ):
            #         print("A soma das apostas deve ser diferente do número de rodadas")
            #         print("Faça uma nova aposta:")
            #         bet = int(input())

            #     game.round.play_bet(bet, player.port)

            # elif game.state == "PLAYING":
            #     print(f" DEBUG Apostas: {game.round.bets}")

            #     for _ in range(game.cards_per_player):
            #         if any(player.cards for player in game.players):
            #             while not queue.empty():
            #                 player = queue.get_nowait()

            #                 print(
            #                     f"Sua vez, {player.name_port()}, você tem {player.lifes} vidas e essas são suas cartas:"
            #                 )
            #                 print(player.cards)

            #                 # Get the player's card
            #                 print(f"{player.name_port()} qual carta você joga?")
            #                 card_num = int(input())

            #                 # Get card from player's hand
            #                 card = player.cards.pop(card_num - 1)

            #                 print(f"Player {player.name_port()} jogou a carta {card}")

            #                 card_with_suit = card.rank + card.suit
            #                 game.round.play_card(
            #                     card_with_suit, card.value, player.port
            #                 )

            #             winner = game.round.calculate_winner_round()
            #             print(f"Vencedor da rodada Jogador {winner}")
            #             game.put_players_queue(queue)
            #             game.calculate_player_lifes()

            #         else:
            #             print("Acabou a rodada", game.state)
            #             game.calculate_next_dealer()
            #             game.calculate_player_lifes()
            #             game.round.clean_round()
            #             game.state = "DEALING"
            #             break

            #     # Check if all cards have been played
            #     if all(len(player.cards) == 0 for player in game.players):
            #         game.round.clean_round()
            #         alive_count = sum(1 for player in game.players if player.is_alive)

            #         if alive_count == 1:
            #             for player in game.players:
            #                 if player.is_alive:
            #                     print(f"O jogador {player.port} ganhou!")
            #                     game.state = "GAME_OVER"
            #                     return

            #         if game.round.round_number <= game.turns:
            #             print("Todas as cartas foram jogadas. Iniciando nova rodada.")
            #             game.state = "DEALING"
            #         else:
            #             game.state = "GAME_OVER"

            # elif game.state == "GAME_OVER":
            #     print("Game Over")
            #     print(f"Vidas dos jogadores: {game.players}")
            #     break


if __name__ == "__main__":
    # Change to logging.DEBUG to see debug statements...
    logging.basicConfig(level=logging.INFO)
    main(sys.argv[1:])
