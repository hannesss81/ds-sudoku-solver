import json
import socket
from threading import Thread
from argparse import ArgumentParser

BUFFER_SIZE = 1024

JOIN_GAME = 'join'
LIST_GAMES = 'list'
CREATE_GAME = 'create'

client_sessions = []


class ClientSession(Thread):
    def __init__(self, address, sock):
        Thread.__init__(self)
        self.address = address
        self.sock = sock

    def run(self):
        print "New session started with: " + str(self.address)
        while True:
            msg = self.sock.recv(BUFFER_SIZE)
            print 'Request: ' + msg
            break
        print 'Client ' + str(self.address) + ' disconnected.'


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
            client_sessions.append(client_session)
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
