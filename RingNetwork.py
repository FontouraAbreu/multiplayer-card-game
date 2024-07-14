from enum import Enum


class Type(Enum):
    ACK = 0
    NACK = 1
    CARDS = 2
    BET = 3
    GAME_INFO = 4
    GAME_OVER = 5
    GAME_START = 6
    ROUND_WINNER = 7


class RingNetwork:
    def __init__(self, size):
        self.circular_buffer = []
        self.size = size
        self.token = {
            "has_message": False,  # has_message is a boolean that indicates if the token has a message
            "msg": {
                "src": None,
                "dst": None,
                "content": None,
                "crc": None,
                "type": None,
            },  # msg is the message that is being sent
            "bearer": None,  # bearer is the index o the node that has the token
        }

    def set_token(self, bearer, msg):
        """
        Sets the token with the message and the bearer
        bearer: the index of the node that has the token
        msg: the message that is being sent
        """
        self.token["has_message"] = True
        self.token["msg"] = msg
        self.token["bearer"] = bearer

    def get_token(self):
        """
        Returns the token
        """
        return self.token

    def clear_token(self):
        """
        Clears the token
        """
        self.token["has_message"] = False
        self.token["msg"] = {
            "src": None,
            "dst": None,
            "content": None,
            "crc": None,
            "type": None,
        }
        self.token["bearer"] = None

    def hop_token(self):
        """
        Hops the token to the next node
        """
        self.token["bearer"] = (self.token["bearer"] + 1) % self.size
