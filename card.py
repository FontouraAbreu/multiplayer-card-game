class Card:
    def __init__(self, suit, rank, value):
        self.suit = suit
        """
        suit: naipe da carta (♦️, ♠️, ❤️, ♣️)

        """
        self.rank = rank
        """
        rank: valor da carta (2, 3, 4, 5, 6, 7, 8, 9, 10, J, Q, K, A)
        """
        self.value = value
        """
        value: valor numerico representando a "força" da carta
        """

    def get_suit(self):
        return self.suit

    def get_rank(self):
        return self.rank

    def get_value(self):
        return self.value

    def __repr__(self):
        return f"{self.rank} {self.suit} ({self.value})"
