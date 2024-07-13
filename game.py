import asyncio
import logging
import sys
from connection import serve_game
from rules import Card, Player, Game, Deck, Round
from utils import calculate_winner_round, put_players_queue, calculate_player_lifes, calculate_next_dealer

queue = asyncio.Queue()

def main(args):
    """
    Launch a client/server
    """
    if len(args) < 3:
        print("args", args)
        print("Usage: python game.py <number_of_players> <cards_per_player> <lifes>")
        return

    num_players = int(args[0])
    cards_per_player = int(args[1])
    lifes = int(args[2])

    game = Game(num_players, cards_per_player, lifes)
    
    print(game)

    # Add players to the queue
    put_players_queue(game, queue)

    # Make a while loop to keep the game running
    print("Starting game...")
    while not game.state == "GAME_OVER":
        game.state = "DEALING"

        while game.round.round_number <= 3:
            if game.state == "DEALING":
                for player in game:
                    player.print_lifes()
                    
                game.round.new_shackle()
                game.round.deck.distribute_cards(game.players, game.cards_per_player)
                print("\n\nRodada:", game.round.round_number)
                print("A manilha é:", game.round.shackle)
                game.state = "BETTING"

            if game.state == "BETTING":
                if queue.empty():
                    game.state = "PLAYING"
                    for player in game:
                        queue.put_nowait(player)
                    continue

                player = queue.get_nowait()
                print(f"{player.name_port()} turn")
                print(f"{player.name_port()} lifes: {player.lifes}")
                print(f"{player.name_port()} cards: {player.cards}")

                # Get the player's bet
                print(f"{player.name_port()} quantas rodadas você faz?")
                bet = int(input())

                # Sum of bets cannot be equal to the number of rounds
                if queue.qsize() == 0 and sum([bet['bet'] for bet in game.round.bets]) == game.round.round_number:
                    print("A soma das apostas deve ser diferente do número de rodadas")
                    print("Faça uma nova aposta:")
                    bet = int(input())

                game.round.play_bet(bet, player.port)

            if game.state == "PLAYING":
                print("\n\n\nRodada:", game.round.round_number)
                print(f"Apostas: {game.round.bets}")
                print("A manilha é:", game.round.shackle)

                for _ in range(game.cards_per_player):
                    if all(player.cards for player in game):
                        while queue.qsize() > 0:
                            player = queue.get_nowait()
                            print(f"Player {player.name_port()} turn")
                            print(f"Player {player.name_port()} lifes: {player.lifes}")
                            print(f"Player {player.name_port()} cards: {player.cards}")

                            # Get the player's card
                            print(f"Player {player.name_port()} qual carta você joga?")
                            card_num = int(input())

                            # Get card from player's hand
                            card = player.cards.pop(card_num - 1)

                            print(f"Player {player.name_port()} jogou a carta {card}")

                            card_with_suit = card.rank + card.suit
                            game.round.play_card(card_with_suit, card.value, player.port)

                            print(f"Cartas jogadas: {game.round.cards}")

                        winner = calculate_winner_round(game.round)
                        print(f"Vencedor da rodada Jogador {winner}")
                        print(f"Apostas: {game.round.bets}")
                        put_players_queue(game, queue)
                        break
                    
                    else:
                        print("Acabaram as cartas dos jogadores, vamos para a proxima rodada")
                        calculate_next_dealer(game)
                        calculate_player_lifes(game)
                        game.round.round_number += 1
                        game.cards_per_player -= 1
                        game.state = "DEALING"
                        break

            if game.state == "GAME_OVER":
                print("Game Over")
                print(f"Vidas dos jogadores: {game.players}")
                break

if __name__ == "__main__":
    # Change to logging.DEBUG to see debug statements...
    logging.basicConfig(level=logging.INFO)
    main(sys.argv[1:])
