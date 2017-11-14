import json, socket, uuid, sudoku
from threading import Thread
from argparse import ArgumentParser

from common import *

running_games = {}


##########################################################
class Game():
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.state = self.generate_new()
        self.players = {}

    def generate_new(self):
        solution = sudoku.generate_grid()
        game = sudoku.generate_game(solution)
        state = ''
        for row in game:
            for elem in row:
                state += str(elem)
        solution_str = ""
        for row in solution:
            for elem in row:
                solution_str += str(elem)
        return state, solution_str

    def increase_score(self, nickname, amount):
        self.players[nickname] += amount
        print '[Game] New score of ' + nickname + ": " + str(amount)

    def decrease_score(self, nickname, amount):
        self.players[nickname] -= amount
        print '[Game] New score of ' + nickname + ": " + str(amount)

    def add_player(self, nickname, connection):
        self.players[nickname] = (0, connection)
        print '[Game] Added: ' + nickname + ", initial score 0."

    def remove_player(self, nickname):
        del self.players[nickname]
        print '[Game] Removed: ' + nickname + " from the game."

    def notify_everyone(self):
        for nickname, (_, connection) in self.players.iteritems():
            print("Sending back to: " + nickname)
            connection.send(json.dumps({"req": GAME_STATE, "state": self.state[0]}))


##########################################################

class ClientSession(Thread):
    def __init__(self, address, sock):
        Thread.__init__(self)
        self.address = address
        self.sock = sock

    def run(self):
        print "[Connections] Client connected: " + str(self.address)
        while True:
            msg = self.sock.recv(BUFFER_SIZE)
            if not msg: break

            msg_json = json.loads(msg)
            request_str = msg_json['req']

            if request_str == JOIN_GAME:
                self.handle_join_game(msg_json['game_id'], msg_json['nickname'])
            elif request_str == LIST_GAMES:
                self.handle_list_games()
            elif request_str == CREATE_GAME:
                self.handle_new_game()
            else:
                print "Unknown request: " + request_str
        print '[Connections] Client disconnected: ' + str(self.address)

    def handle_new_game(self):
        new_game = Game()
        running_games[new_game.id] = new_game
        self.done()
        print '[Connections] Created a new game: ' + str(new_game)

    def handle_list_games(self):
        games_list = []
        for id in running_games:
            games_list.append(id)
        self.sock.send(json.dumps(games_list))
        self.done()
        print '[Connections] Sent games list back to: ' + str(self.sock)

    def handle_join_game(self, game_id, nickname):
        game = running_games.get(game_id)
        game.add_player(nickname, self.sock)
        self.sock.send(JOIN_OK)
        print '[Game] Joined: ' + nickname + "@" + game_id
        self.sock.send(json.dumps({"req": GAME_STATE, "state": game.state[0]}))
        while True:
            msg = self.sock.recv(BUFFER_SIZE)
            if not msg: break

            msg_json = json.loads(msg)
            request_str = msg_json['req']

            if request_str == NEW_GUESS:
                x, y, guess = list(msg_json["guess"])

                if self.check_match(x, y, guess, game):
                    index = 9 * int(x) + int(y)
                    modified_game_state = (game.state[0][:index] + guess + game.state[0][index + 1:], game.state[1])
                    game.state = modified_game_state
                    game.notify_everyone()
        print '[Game] Left: ' + nickname
        game.remove_player(nickname)

    def check_match(self, x, y, guess, game):
        correct = game.state[1]
        print(correct)
        print(guess)
        if correct[9 * int(x) + int(y)] == guess:
            return True
        return False

    def done(self):
        self.sock.send(DONE)


###############################################################
def main(args):
    TCP_IP = args.listenaddr
    TCP_PORT = args.port

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((TCP_IP, TCP_PORT))

    while True:
        print '[Connections] ... idle ...'
        s.listen(1)
        try:
            sock, addr = s.accept()
            client_session = ClientSession(addr, sock)
            client_session.start()
        except (Exception, KeyboardInterrupt) as e:
            print '[Connections] Something happened', e
            break


if __name__ == '__main__':
    # Parsing arguments
    parser = ArgumentParser()
    parser.add_argument('-l', '--listenaddr', help='IP address to listen.', required=True)
    parser.add_argument('-p', '--port', type=int, help='TCP port to listen.', required=True)
    args = parser.parse_args()

    main(args)
