import asyncio
import logging
import sys
import socket
import json

from connection import serve_game
from game import Game
from player import Player
from round import Round
from deck import Deck
from client import Client

from config import SERVER_ADDRESS, SERVER_PORT, PLAYERS


def main(args):
    """
    Launch a client/server
    """
    # Make a while loop to keep the game running
    print("Starting game...")
    client = Client(SERVER_ADDRESS, SERVER_PORT)
    message = {
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

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((client.host, client.port))

        while message["msg"]["type"] != "GAME_OVER":
            message = client_socket.recv(sys.getsizeof(message))
            print("Message received:", message)
            message = json.loads(message.decode("utf-8"))
            msg_type = message["msg"]["type"]

            # check if the current player is the dst of the message
            # if not message["msg"]["dst"] == game.players[game.current_player].port:
            #     continue

            if msg_type == "DEALING":
                """
                In this state, the game will show the player's lifes and distribute its cards
                This state will only be executed if the client receives a token with the "DEALING" type
                """
                # individual lifes

                # ----- MOVIDO PARA O SERVIDOR -----
                # current_player = game.players[game.current_player]
                # current_shackle = game.round.shackle
                # current_player.cards = game.round.deck.distribute_cards(
                #     [current_player], game.cards_per_player
                # )

                # print(f"Vidas do jogador {current_player.port}: {current_player.lifes}")
                # print(f"Manilha atual: {current_shackle}")
                # print(
                #     f"Cartas do jogador {current_player.port}: {current_player.cards}"
                # )
                # input("Press Enter to continue...")
                # ----- MOVIDO PARA O SERVIDOR -----

                network_message = "\n\n====================================="
                network_message += f"\nRodada: {game.round.round_number}"
                network_message += f"\nA manilha é: {game.round.shackle}"
                network_message += "\n=====================================\n\n    "
                client_socket.sendall(network_message.encode())

                # print("\n\n=====================================")
                # print("Rodada:", game.round.round_number)
                # print("A manilha é:", game.round.shackle)
                # print("=====================================\n\n    ")
                game.state = "BETTING"

            elif game.state == "BETTING":
                if queue.empty():
                    game.state = "PLAYING"
                    for player in game.players:
                        queue.put_nowait(player)
                    continue

                player = queue.get_nowait()
                print(
                    f"Sua vez, {player.name_port()}, você tem {player.lifes} vidas e essas são suas cartas:"
                )
                print(player.cards)

                # Get the player's bet
                print(f"{player.name_port()} quantas rodadas você faz?")
                bet = int(input())

                # Sum of bets cannot be equal to the number of rounds
                if (
                    queue.qsize() == 0
                    and sum([bet["bet"] for bet in game.round.bets])
                    == game.round.cards_per_player
                ):
                    print("A soma das apostas deve ser diferente do número de rodadas")
                    print("Faça uma nova aposta:")
                    bet = int(input())

                game.round.play_bet(bet, player.port)

            elif game.state == "PLAYING":
                print(f" DEBUG Apostas: {game.round.bets}")

                for _ in range(game.cards_per_player):
                    if any(player.cards for player in game.players):
                        while not queue.empty():
                            player = queue.get_nowait()

                            print(
                                f"Sua vez, {player.name_port()}, você tem {player.lifes} vidas e essas são suas cartas:"
                            )
                            print(player.cards)

                            # Get the player's card
                            print(f"{player.name_port()} qual carta você joga?")
                            card_num = int(input())

                            # Get card from player's hand
                            card = player.cards.pop(card_num - 1)

                            print(f"Player {player.name_port()} jogou a carta {card}")

                            card_with_suit = card.rank + card.suit
                            game.round.play_card(
                                card_with_suit, card.value, player.port
                            )

                        winner = game.round.calculate_winner_round()
                        print(f"Vencedor da rodada Jogador {winner}")
                        game.put_players_queue(queue)
                        game.calculate_player_lifes()

                    else:
                        print("Acabou a rodada", game.state)
                        game.calculate_next_dealer()
                        game.calculate_player_lifes()
                        game.round.clean_round()
                        game.state = "DEALING"
                        break

                # Check if all cards have been played
                if all(len(player.cards) == 0 for player in game.players):
                    game.round.clean_round()
                    alive_count = sum(1 for player in game.players if player.is_alive)

                    if alive_count == 1:
                        for player in game.players:
                            if player.is_alive:
                                print(f"O jogador {player.port} ganhou!")
                                game.state = "GAME_OVER"
                                return

                    if game.round.round_number <= game.turns:
                        print("Todas as cartas foram jogadas. Iniciando nova rodada.")
                        game.state = "DEALING"
                    else:
                        game.state = "GAME_OVER"

            elif game.state == "GAME_OVER":
                print("Game Over")
                print(f"Vidas dos jogadores: {game.players}")
                break


if __name__ == "__main__":
    # Change to logging.DEBUG to see debug statements...
    logging.basicConfig(level=logging.INFO)
    main(sys.argv[1:])
