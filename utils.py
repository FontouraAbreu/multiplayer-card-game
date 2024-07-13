from rules import Card, Player, Game, Deck, Round

#Calcula a carta de maior valor da rodada é dimini o valor da aposta do jogador
def calculate_winner_round(round):
    # Encontrar o objeto com o maior valor
    max_card = max(round.cards, key=lambda x: x['value'])
    winner_player = max_card['player']

    # Diminuir a aposta do jogador vencedor
    for bet in round.bets:
        if bet['player'] == winner_player:
            bet['bet'] -= 1
            break
    
    # Vencedor da rodada
    return winner_player

#recoloca todos jogadores na fila e aumenta o número de rodadas
def put_players_queue(game, queue):
    for player in game.players:
        queue.put_nowait(player)

def calculate_player_lifes(game):
    for player in game.players:
        for bet in game.round.bets:
            if bet['player'] == player.port:
                if bet['bet'] != 0:
                    player.lifes -= abs(bet['bet'])
                break


def calculate_next_dealer(game):
    for player in game.players:
        if player.is_dealer:
            player.is_dealer = False
            break

    for i, player in enumerate(game.players):
        if player.port == game.players[-1].port:
            game.players[0].is_dealer = True
            break
        elif player.is_dealer:
            game.players[i + 1].is_dealer = True
            break