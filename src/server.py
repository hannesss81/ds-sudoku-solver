import json, socket, uuid
from threading import Thread
from argparse import ArgumentParser
from common import *

running_games = []


class Game():
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.state = self.generate_new()
        self.players = []

    def generate_new(self):
        return "123"


class ClientSession(Thread):
    def __init__(self, address, sock):
        Thread.__init__(self)
        self.address = address
        self.sock = sock

    def run(self):
        print "New session started with: " + str(self.address)
        while True:
            msg = self.sock.recv(BUFFER_SIZE)
            if not msg: break

            msg_json = json.loads(msg)
            request_str = msg_json['req']

            if request_str == JOIN_GAME:
                print "want to join"
            elif request_str == LIST_GAMES:
                self.handle_list_games()
            elif request_str == CREATE_GAME:
                self.handle_new_game()
            else:
                print "unknown request"
        print 'Client ' + str(self.address) + ' disconnected.'

    def handle_new_game(self):
        new_game = Game()
        running_games.append(new_game)
        print 'Created new game, ' + str(new_game)

    def handle_list_games(self):
        games_list = []
        for game in running_games:
            games_list.append(game.id)
        self.sock.send(json.dumps(games_list))
        print 'Sent games list back to: ' + str(self.sock)


def main(args):
    TCP_IP = args.listenaddr
    TCP_PORT = args.port

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((TCP_IP, TCP_PORT))

    while True:
        print '... idle ...'
        s.listen(1)
        try:
            sock, addr = s.accept()
            client_session = ClientSession(addr, sock)
            client_session.start()
        except (Exception, KeyboardInterrupt) as e:
            print 'Something happened', e
            break


if __name__ == '__main__':
    # Parsing arguments
    parser = ArgumentParser()
    parser.add_argument('-l', '--listenaddr', help='IP address to listen.', required=True)
    parser.add_argument('-p', '--port', type=int, help='TCP port to listen.', required=True)
    args = parser.parse_args()

    main(args)
