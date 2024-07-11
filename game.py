import asyncio
import logging
import sys
from connection import serve_game
from rules import Card, Player, Game, Deck, Round

queue = asyncio.Queue()

def main(args):
    """
    launch a client/server
    """
    if len(args) < 3:
        print("args", args)
        print("Usage: python game.py <number_of_players> <cards_per_player>")
        return

    num_players = int(args[0])
    cards_per_player = int(args[1])
    lifes = int(args[2])

    game = Game(num_players, cards_per_player, lifes)
    
    print(game)
    print("Dealing cards...", game.round)
    for player in game:
        player.print_lifes()
        print(f"{player.name_port()} hand: {player.cards}")


if __name__ == "__main__":
    # change to logging.DEBUG to see debug statements...
    logging.basicConfig(level=logging.INFO)
    main(sys.argv[1:])