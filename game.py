import random
from enum import Enum
from round import Round
from player import Player


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
            Player(port, turns, cards, True, False, False, color)
            for port, cards, color in zip(
                range(1, num_players + 1),
                self.round.deal_cards(),
                ["red", "blue", "green", "yellow", "purple", "orange", "brown", "pink"],
            )
        ]
        self.players[0].is_dealer = True
        self.current_player = 0
        self.state = State.WAITING

    def new_round(self):
        """
        Função para criar uma nova rodada
        """
        self.round = Round(
            self.round.round_number + 1, self.num_players, self.cards_per_player
        )
        # Distribui as cartas
        for player in self.players:
            player.cards = self.round.deal_cards()
            player.has_cards = True
            player.has_played = False
            player.current_bet = 0
            player.bets_won = 0
            player.has_bet = False

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
        # if the turns_won are different from the player's bet, the player loses a life
        for player in self.players:
            for bet in self.round.bets:
                print(bet)
                if bet["player"] == player.port:
                    print(
                        "player {} bet {} and won {}".format(
                            player.port, bet["bet"], bet["turns_won"]
                        )
                    )
                    if player.current_bet != player.bets_won:
                        print("player {} lost a life".format(player.port))
                        player.lifes -= abs(player.current_bet)

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

    def next_player(self):
        """
        Função para calcular o próximo jogador
        """
        self.current_player = (self.current_player + 1) % self.num_players

    def next_state(self):
        """
        Função para calcular o próximo estado do jogo
        """
        if self.state == "DEALING":
            self.state = "BETTING"
        # elif self.state == "BETTING":
        #     self.state = "PLAYING"
        # elif self.state == "PLAYING":
        #     self.state = "DEALING"

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
