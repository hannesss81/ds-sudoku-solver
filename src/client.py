import socket

SERVER = "127.0.0.1"
PORT = 6666


def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((SERVER, PORT))
    while True:
        client.send("blabla")
        break
    client.close()


if __name__ == '__main__':
    main()
