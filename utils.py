import argparse


def parse_args():
    parser = argparse.ArgumentParser(description="Start a server")
    parser.add_argument(
        "cards_per_player",
        metavar="cards_per_player",
        type=int,
        help="The number of cards each player should have",
    )
    parser.add_argument(
        "turns",
        metavar="turns",
        type=int,
        help="The number of turns to play",
    )
    return parser.parse_args()


def calculate_crc8(message):
    crc = 0
    for byte in message:
        crc += byte
    return crc % 256
