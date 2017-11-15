import json, socket, uuid, sudoku
from threading import Thread
from argparse import ArgumentParser

from common import *

## Keeps track of current running games
running_games = {}
game_counter = 0  # Increments after each new session for generating a unique name (GAME0, GAME1, ...)


## Game Object itself
class Game():
    def __init__(self):
        global game_counter
        self.id = "GAME" + str(game_counter)
        self.state = self.generate_new()
        self.players = {}
        game_counter += 1

    ## Generates a new sudoku, uses 3rd party code from - Ripley6811
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

    def add_player(self, nickname, connection):
        self.players[nickname] = (0, connection)
        print '[Game] Added: ' + nickname + ", initial score 0."

    ## Removes player from the game and also notifies all other players for GUI update
    def remove_player(self, nickname):
        player, connection = self.players[nickname]
        del self.players[nickname]
        if (len(self.players) == 0):
            del running_games[self.id]
            return
        self.notify_everyone()
        print '[Game] Removed: ' + nickname + " from the game."

    ## Notifies every current player of the latest game state (table and scores)
    def notify_everyone(self):
        scores = []
        for nickname, (score, _) in self.players.iteritems():
            scores.append((nickname, score))
        for nickname, (_, connection) in self.players.iteritems():
            print("Sending back to: " + nickname)
            connection.send(json.dumps({"req": GAME_STATE, "state": self.state[0], "scores": scores}))

    def notify_everyone_winner(self, current_winner):
        for nickname, (score, connection) in self.players.iteritems():
            connection.send(json.dumps({"req": WIN, "msg": "Winner was: " + current_winner + "! Game over."}))


##########################################################

## Session thread, for each client a new thread will be created
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
        self.sock.send(json.dumps({"games": games_list}))
        print '[Connections] Sent games list back to: ' + str(self.sock)

    ## Moves to 'game' mode and starts receiving events of new guesses and will notify all players afterwards.
    def handle_join_game(self, game_id, nickname):
        game = running_games.get(game_id)
        game.add_player(nickname, self.sock)
        self.sock.send(JOIN_OK)
        print '[Game] Joined: ' + nickname + "@" + game_id
        game.notify_everyone()
        while True:
            msg = self.sock.recv(BUFFER_SIZE)
            if not msg: break

            msg_json = json.loads(msg)
            request_str = msg_json['req']

            if request_str == NEW_GUESS:
                x, y, guess = list(msg_json["guess"])
                if self.check_match(x, y, guess, game):
                    game.players[nickname] = (game.players[nickname][0] + 1, game.players[nickname][1])
                    index = 9 * int(x) + int(y)
                    modified_game_state = (game.state[0][:index] + guess + game.state[0][index + 1:], game.state[1])
                    game.state = modified_game_state
                else:
                    game.players[nickname] = (game.players[nickname][0] - 1, game.players[nickname][1])
                if game.state[0] == game.state[1]:
                    current_winner = ""
                    current_max = -999999
                    for name, (score, connection) in game.players.iteritems():
                        if current_max < score:
                            current_winner = name
                            current_max = score
                    print("Winner: " + str(name) + ", score: " + str(score))
                    game.notify_everyone_winner(current_winner)
                    break
                game.notify_everyone()

        print '[Game] Left: ' + nickname
        game.remove_player(nickname)

    ## Checks whether the guess was correct
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
            client_session = ClientSession(addr, sock)  ## New thread for each client.
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
