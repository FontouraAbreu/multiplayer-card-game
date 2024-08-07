import random
from deck import Deck


class Round:
    """
    Classe para representar uma rodada do jogo
    """

    def __init__(self, round_number, num_players, cards_per_player):
        self.shackle = random.choice(["4", "5", "6", "7", "Q", "J", "K", "A", "2", "3"])
        self.round_number = round_number
        self.deck = Deck(self.shackle)
        self.deck.shuffle()
        self.new_shackle()
        self.num_players = num_players
        self.cards_per_player = cards_per_player
        self.current_player = 0
        self.current_winning_card = None
        self.current_winning_player = None
        self.current_winning_player_lives = 0
        self.cards = []
        self.bets = []

    # Obj with bet and player of bet
    def play_bet(self, bet, player):
        """
        Função para fazer uma aposta
        bet: aposta
        player: jogador
        Atualiza a lista de apostas
        """
        self.bets.append({"bet": bet, "player": player, "turns_won": 0})
        return None

    def win_turn(self, player):
        """
        Função para incrementar o número de turnos ganhos
        player: jogador
        """
        for bet in self.bets:
            if bet["player"] == player:
                bet["turns_won"] += 1
                break
        return None

    def play_card(self, card, value, player):
        """
        Função para jogar uma carta
        card: carta
        value: valor da carta
        player: jogador
        Atualiza a lista de cartas jogadas
        """
        self.cards.append({"card": card, "value": value, "player": player})
        return None

    def deal_cards(self):
        """
        Função para distribuir as cartas
        return: lista de cartas distribuídas
        """
        return self.deck.deal(self.num_players, self.cards_per_player)

    def clean_turn(self):
        """
        Função para limpar o turno
        Limpa a lista de cartas
        """
        self.cards = []

    def clean_round(self):
        """
        Função para limpar a rodada
        Limpa a lista de cartas e apostas e incrementa o número da rodada
        """
        self.cards = []
        self.bets = []
        self.round_number += 1

    def new_shackle(self):
        """
        Função para definir uma nova manilha
        """
        self.shackle = random.choice(["4", "5", "6", "7", "Q", "J", "K", "A", "2", "3"])
        self.deck.__init__(self.shackle)

    def calculate_winner_round(self):
        """
        Função para calcular o vencedor da rodada
        return: jogador vencedor
        """
        # Encontrar o objeto com o maior valor
        max_card = max(self.cards, key=lambda x: x["value"])
        winner_player = max_card["player"]

        # # Diminuir a aposta do jogador vencedor
        # for bet in self.bets:
        #     if bet["player"] == winner_player:
        #         bet["bet"] -= 1
        #         break

        # Vencedor da rodada
        return winner_player

    def calculate_winner(self):
        """
        Função para calcular o vencedor da rodada
        return: jogador vencedor
        """
        # Encontrar o jogador com o maior número de turnos ganhos
        winner = max(self.bets, key=lambda x: x["turns_won"])
        return winner["player"]

    def __repr__(self):
        return f"Round {self.round_number} with {self.num_players} players, shackled at {self.shackle}"
