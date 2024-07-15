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
        self.message_queue = []  # Fila de mensagens do jogador
        self.has_token = False  # O jogador tem o token?

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
