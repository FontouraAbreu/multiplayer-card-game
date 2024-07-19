import socket
from config import SERVER_ADDRESS, SERVER_PORT

# from main import main


class Client:
    """
    This is just an example of a client
    we are actually going to implement the client logic in the main.py file
    """

    def __init__(self, host, port):
        self.host = host
        self.port = port

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((self.host, self.port))
            while True:
                message = client_socket.recv(1024)
                if message == b"Your turn":
                    self.play_turn()
                    client_socket.sendall(b"Turn complete")

    def play_turn(self):
        print("It's your turn to play!")
        # Implement the game logic here
        input("Press Enter after completing your turn...")


if __name__ == "__main__":
    client = Client(
        SERVER_ADDRESS, SERVER_PORT
    )  # Replace 'server_ip_address' with the actual server IP address
    client.start()
