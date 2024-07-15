import random
from card import Card


class Deck:
    ranks = ["4", "5", "6", "7", "Q", "J", "K", "A", "2", "3"]
    suits = ["♦️", "♠️", "❤️", "♣️"]
    base_values = {
        "4": 1,
        "5": 2,
        "6": 3,
        "7": 4,
        "Q": 5,
        "J": 6,
        "K": 7,
        "A": 8,
        "2": 9,
        "3": 10,
    }
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
        """
        Função para embaralhar o baralho
        """
        random.shuffle(self.cards)

    def distribute_cards(self, players, cards_per_player):
        """
        Função para distribuir as cartas
        players: lista de jogadores
        cards_per_player: número de cartas por jogador
        """
        self.shuffle()

        # Check if there are enough cards to deal
        if len(self.cards) < len(players) * cards_per_player:
            raise ValueError("Not enough cards to deal")

        # Distribute cards to players
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
        return [
            [self.cards.pop() for _ in range(cards_per_player)]
            for _ in range(num_players)
        ]
