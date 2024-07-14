import random
from enum import Enum


# ENUM STATE GAME
class State(Enum):
    WAITING = 1
    DEALING = 2
    BETING = 3
    PLAYING = 4
    GAME_OVER = 5


class Game:
    """
    Classe para representar o jogo
    num_players: número de jogadores
    cards_per_player: número de cartas por jogador
    turns: número de turnos
    """

    def __init__(self, num_players, cards_per_player, turns):
        self.num_players = num_players
        self.cards_per_player = cards_per_player
        self.turns = turns
        self.round = Round(1, num_players, cards_per_player)
        self.players = [
            Player(port, turns, cards, True, False, color)
            for port, cards, color in zip(
                range(1, num_players + 1),
                self.round.deal_cards(),
                ["red", "blue", "green", "yellow", "purple", "orange", "brown", "pink"],
            )
        ]
        self.players[0].is_dealer = True
        self.current_player = 0
        self.state = State.WAITING

    def put_players_queue(self, queue):
        """
        Função para adicionar os jogadores na fila de jogadores
        queue: fila de jogadores
        """
        for player in self.players:
            if player.is_alive:
                queue.put_nowait(player)  # Adiciona o jogador na fila de jogadores

    def calculate_next_dealer(self):
        """
        Função para calcular o próximo dealer
        """
        for player in self.players:
            if player.is_dealer:
                player.is_dealer = False
                break

        # seta o próximo dealer
        for i, player in enumerate(self.players):
            # se o dealer for o último jogador, o próximo dealer é o primeiro
            if player.port == self.players[-1].port:
                self.players[0].is_dealer = True
                break
            elif player.is_dealer:
                self.players[i + 1].is_dealer = True
                break

    def check_lifes(self):
        """
        Função para verificar a quantidade de jogadores vivos
        return: quantidade de jogadores vivos
        """
        for player in self.players:
            if player.lifes <= 0:
                player.is_alive = False

        # retorna a quantidade de jogadores vivos
        return sum(1 for player in self.players if player.is_alive)

    def calculate_player_lifes(self):
        """
        Função para calcular a quantidade de vidas dos jogadores

        """
        for player in self.players:
            for bet in self.round.bets:
                if bet["player"] == player.port:
                    if bet["bet"] != 0:
                        player.lifes -= abs(bet["bet"])
                    break

        for player in self.players:
            if player.lifes <= 0:
                player.is_alive = False

    def check_game_over(self):
        """
        Função para verificar se o jogo acabou
        """
        alive_count = sum(1 for player in self.players if player.is_alive)

        # Verificar se restou apenas um jogador vivo
        if alive_count == 1:
            for player in self.players:
                if player.is_alive:
                    self.state = "GAME_OVER"
                    return

        # Verificar se nenhum jogador está vivo
        elif alive_count == 0:
            self.state = "GAME_OVER"

        # Verificar se o número de rodadas atingiu o limite de turnos
        elif self.round.round_number > self.turns:
            self.state = "GAME_OVER"

        # Verificar se todos os jogadores estão sem cartas
        elif all(len(player.cards) == 0 for player in self.players):
            self.state = "DEALING"

        # Continuar jogando se nenhuma das condições acima for satisfeita
        else:
            self.state = "PLAYING"

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
        self.bets.append({"bet": bet, "player": player})
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

        # Diminuir a aposta do jogador vencedor
        for bet in self.bets:
            if bet["player"] == winner_player:
                bet["bet"] -= 1
                break

        # Vencedor da rodada
        return winner_player

    def __repr__(self):
        return f"Round {self.round_number} with {self.num_players} players, shackled at {self.shackle}"


class Player:
    """
    Classe para representar um jogador
    port: número do jogador
    lifes: vidas do jogador
    cards: cartas do jogador
    is_alive: jogador está vivo?
    is_dealer: jogador é o dealer?
    color: cor do jogador
    """

    def __init__(self, port, lifes, cards, is_alive, is_dealer, color):
        self.port = port
        self.lifes = lifes
        self.cards = cards
        self.is_alive = is_alive
        self.is_dealer = is_dealer
        self.color = color

    def name_port(self):
        """
        Função para retornar o nome do jogador
        """
        return f"Player {self.port}"

    def take_damage(self):
        """
        Função para tirar uma vida do jogador
        """
        self.lifes -= 1
        if self.lifes == 0:
            self.is_alive = False

    def print_lifes(self):
        """
        Função para imprimir as vidas do jogador
        """
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
