import random
from enum import Enum

#ENUM STATE GAME
class State(Enum):
    WAITING = 1
    DEALING = 2
    BETING = 3
    PLAYING = 4
    GAME_OVER = 5

class Game:
    def __init__(self, num_players, cards_per_player, turns):
        self.num_players = num_players
        self.cards_per_player = cards_per_player
        self.turns = turns
        self.round = Round(1, num_players, cards_per_player)
        self.players = [Player(port, turns, cards, True, False, color) for port, cards, color in zip(range(1, num_players + 1), self.round.deal_cards(), ["red", "blue", "green", "yellow", "purple", "orange", "brown", "pink"])]
        self.players[0].is_dealer = True
        self.current_player = 0
        self.state = State.WAITING

    def __repr__(self):
        return f"Game with {self.num_players} players, {self.cards_per_player} cards per player and {self.turns} turns"

    def __str__(self):
        return f"Game with {self.num_players} players, {self.cards_per_player} cards per player and {self.turns} turns"

    def __len__(self):
        return self.num_players

    def __getitem__(self, key):
        return self.players[key]

    def __iter__(self):
        self.index = 0  # Reinicialize o índice ao começar a iteração
        return self

    def __next__(self):
        if self.index < len(self.players):
            player = self.players[self.index]
            self.index += 1
            return player
        else:
            raise StopIteration

    def __contains__(self, item):
        return item in self.players

    def __reversed__(self):
        return reversed(self.players)

    def __add__(self, other):
        return self.num_players + other.num_players

class Round:
    def __init__(self, round_number, num_players, cards_per_player):
        self.shackle = random.choice(["4", "5", "6", "7", "Q", "J", "K", "A", "2", "3"])
        self.round_number = round_number
        self.deck = Deck(self.shackle)
        self.deck.shuffle()
        self.new_shackle()
        self.num_players = num_players
        self.cards_per_player = cards_per_player
        self.current_player = 0
        self.current_card = None
        self.current_value = None
        self.cards = []
        self.bets = []

    def next_player(self):
        self.current_player = (self.current_player + 1) % self.num_players

    def next_turn(self):
        self.current_card = None
        self.current_value = None
        self.next_player()
    
    # Obj with bet and player of bet
    def play_bet(self, bet, player):
        self.bets.append({"bet": bet, "player": player})
        return None
    
    def play_card(self, card, value, player):
        self.cards.append({"card": card, "value": value, "player": player})
        return None
    
    def deal_cards(self):
        return self.deck.deal(self.num_players, self.cards_per_player)
    
    def new_shackle(self):
        self.shackle = random.choice(["4", "5", "6", "7", "Q", "J", "K", "A", "2", "3"])
        self.deck.__init__(self.shackle)
    
    def __repr__(self):
        return f"Round {self.round_number} with {self.num_players} players, shackled at {self.shackle}"

class Player:
    def __init__(self, port, lifes, cards, is_alive, is_dealer, color):
        self.port = port
        self.lifes = lifes
        self.cards = cards
        self.is_alive = is_alive
        self.is_dealer = is_dealer
        self.color = color

    def name_port(self):
        return f'Player {self.port}'

    def take_damage(self):
        self.lifes -= 1
        if self.lifes == 0:
            self.is_alive = False

    def print_lifes(self):
        print(f"\nJogador {self.port}")
        for _ in range(0, self.lifes):
            print("❤️", end="  ")

class Card:
    def __init__(self, suit, rank, value):
        self.suit = suit
        self.rank = rank
        self.value = value

    def __repr__(self):
        return f"{self.rank} {self.suit} ({self.value})"

class Deck:
    ranks = ["4", "5", "6", "7", "Q", "J", "K", "A", "2", "3"]
    suits = ["♦️", "♠️", "❤️", "♣️"]
    base_values = {"4": 1, "5": 2, "6": 3, "7": 4, "Q": 5, "J": 6, "K": 7, "A": 8, "2": 9, "3": 10}
    suit_values = {"♦️": 1, "♠️": 2, "❤️": 3, "♣️": 4}

    def __init__(self, shackle_rank):
        self.shackle_rank = shackle_rank
        self.cards = []

        # Adjust values for the shackle (manilha)
        self.values = self.base_values.copy()
        # Set next value shackles to the highest value
        self.values[shackle_rank] = 11

        # Create the deck of cards
        for suit in self.suits:
            for rank in self.ranks:
                rank_value = self.values[rank]
                suit_value = self.suit_values[suit]
                # Combine rank and suit values to get the overall value of the card
                value = rank_value * 10 + suit_value
                self.cards.append(Card(suit, rank, value))

    def shuffle(self):
        random.shuffle(self.cards)

    
    def distribute_cards(self, players, cards_per_player):
        self.shuffle()

        if len(self.cards) < len(players) * cards_per_player:
            raise ValueError("Not enough cards to deal")
        for player in players:
            player.cards = [self.cards.pop() for _ in range(cards_per_player)]
            
        # new_cards = self.round.deal_cards()
        # for player, cards in zip(self.players, new_cards):
        #     player.cards = cards
        

    def new_shackle(self):
        self.shackle_rank = random.choice(self.ranks)
        self.__init__(self.shackle_rank)

    def deal(self, num_players, cards_per_player):
        if num_players * cards_per_player > len(self.cards):
            raise ValueError("Not enough cards to deal")
        return [[self.cards.pop() for _ in range(cards_per_player)] for _ in range(num_players)]