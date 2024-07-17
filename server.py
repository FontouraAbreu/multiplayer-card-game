import socket
import threading
import time
import sys
import json

from config import SERVER_ADDRESS, SERVER_PORT, PLAYERS


class Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.clients = []
        self.lock = threading.Lock()
        self.current_player = 0
        self.token = None

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((self.host, self.port))
            server_socket.listen(PLAYERS)
            print(f"Server started at {self.host}:{self.port}")
            while len(self.clients) < PLAYERS:
                conn, addr = server_socket.accept()
                with self.lock:
                    self.clients.append(conn)
                print(f"Player connected from {addr}")
            threading.Thread(target=self.manage_game).start()

    def manage_game(self):
        self.token = 0
        message_template = {
            "has_message": False,
            "msg": {
                "src": None,
                "dst": None,
                "content": None,
                "crc": None,
                "type": None,
            },
            "bearer": None,
        }
        while True:
            with self.lock:
                current_conn = self.clients[self.token]
            # testing sending the dealing message
            message = message_template
            message["msg"]["type"] = "DEALING"
            message["msg"]["crc"] = 0
            message["has_message"] = True
            message["bearer"] = self.token
            message = json.dumps(message, indent=2).encode("utf-8")
            print("Sending message:", message)
            current_conn.sendall(message)
            current_conn.recv(
                sys.getsizeof(message)
            )  # Wait for the player to finish their turn
            # here we should check the answer for a ack or nack

            with self.lock:
                self.token = (self.token + 1) % PLAYERS

    def broadcast(self, message):
        for client in self.clients:
            client.sendall(message.encode())


if __name__ == "__main__":
    server = Server(SERVER_ADDRESS, SERVER_PORT)
    server.start()
