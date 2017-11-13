import json, socket
from common import *

SERVER = "127.0.0.1"
PORT = 6666


def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((SERVER, PORT))

    client.send(json.dumps({'req': LIST_GAMES}))
    response = client.recv(BUFFER_SIZE)

    print("Response: " + response)


if __name__ == '__main__':
    main()
