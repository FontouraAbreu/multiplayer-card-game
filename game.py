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
        print("Usage: python game.py <number_of_players> <cards_per_player> <lifes>")
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

    #add players to the queue
    for player in game:
        queue.put_nowait(player)

    print("Players in queue:", queue.qsize())

    #make a while loop to keep the game running
    print("Starting game...")
    while not game.state == "GAME_OVER":
        #get the player from the queue
        game.state = "DEALING"

        while game.round.round_number > 0:
            if (game.state == "DEALING"):
                game.round.deal_cards()
                print("Rodada:", game.round.round_number)
                print("A manilha é:", game.round.shackle)
                game.state = "BETING"

            if (game.state == "BETING"):
                if queue.empty():
                    game.state = "PLAYING"
                    for player in game:
                        queue.put_nowait(player)
                    continue

                player = queue.get_nowait()
                print(f"Player {player.name_port()} turn")
                print(f"Player {player.name_port()} lifes: {player.lifes}")
                print(f"Player {player.name_port()} cards: {player.cards}")

                #get the player's bet
                print(f"Player {player.name_port()} quantas rodadas você faz?")
                bet = int(input())
                if bet < 0 and queue.qsize() == 0:
                    print("A aposta deve ser maior igual a 0")
                    while bet < 0:
                        print("Faça uma nova aposta:")
                        bet = int(input())
                    continue

                if bet > game.round.round_number and queue.qsize() == 0:
                    print("A aposta deve ser menor igual ao número de rodadas")
                    while bet > game.round.round_number:
                        print("Faça uma nova aposta:")
                        bet = int(input())
                    continue


                print(f"Player {player.name_port()} apostou {bet} rodadas")

                game.round.play_bet(bet, player.port)

            if (game.state == "PLAYING"):

                print(f"apostas: {game.round.bets}")

                print("Rodada:", game.round.round_number)
                print("A manilha é:", game.round.shackle)

                player = queue.get_nowait()
                print(f"Player {player.name_port()} turn")
                print(f"Player {player.name_port()} lifes: {player.lifes}")
                print(f"Player {player.name_port()} cards: {player.cards}")

                #get the player's card
                print(f"Player {player.name_port()} qual carta você joga?")
                card_num = int(input())

                #get card from player's hand
                card = player.cards.pop(card_num+1)

                print(f"Player {player.name_port()} jogou a carta {card}")

                card_with_suit = card.rank + card.suit
                game.round.play_card(card_with_suit, card.value, player.port)


                print(f"Player {player.name_port()} jogou a carta {card_with_suit}")

                print(f"Cartas jogadas: {game.round.cards}")





if __name__ == "__main__":
    # change to logging.DEBUG to see debug statements...
    logging.basicConfig(level=logging.INFO)
    main(sys.argv[1:])