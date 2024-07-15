import asyncio
import logging
import sys
import socket

from connection import serve_game
from game import Game
from player import Player
from round import Round
from deck import Deck
from client import Client

from config import SERVER_ADDRESS, SERVER_PORT, PLAYERS

queue = asyncio.Queue()


def main(args):
    """
    Launch a client/server
    """
    if len(args) < 3:
        print("args", args)
        print("Usage: python game.py <number_of_players> <cards_per_player> <turns>")
        return

    num_players = int(args[0])
    cards_per_player = int(args[1])
    turns = int(args[2])

    game = Game(num_players, cards_per_player, turns)

    print(game)

    # Add players to the queue
    game.put_players_queue(queue)
    game.state = "DEALING"

    # Make a while loop to keep the game running
    print("Starting game...")
    client = Client(SERVER_ADDRESS, SERVER_PORT)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((client.host, client.port))
        while game.state != "GAME_OVER":
            print(f"Current State: {game.state}")

            if game.state == "DEALING":

                for player in game.players:
                    player.print_lifes()

                game.round.new_shackle()
                game.round.deck.distribute_cards(game.players, game.cards_per_player)

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
