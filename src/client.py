import json, socket, ast, threading
import tkMessageBox
from tkSimpleDialog import askstring
from Tkinter import *

import time

from common import *

SERVER = ""
PORT = 0000

connected = False

## Menu view (JOIN-GAME, CREATE-NEW)
class Menu():
    def __init__(self, master, nickname):
        self.nickname = nickname
        self.master = master
        self.frame = Frame(self.master)

        self.master.title(self.nickname)
        self.create_buttons()
        self.frame.pack()

    ## Setting up layout
    def create_buttons(self):
        global SERVER, PORT

        while True:
            try:
                SERVER = askstring("Enter server IP", "")
                PORT = int(askstring("Enter server PORT", ""))
                if SERVER == None or PORT == None:
                    sys.exit(0)
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.connect((SERVER, int(PORT)))
                client.close()
                break
            except Exception as e:
                tkMessageBox.showinfo("Try again", e)

        self.JOIN = Button(self.frame, command=lambda: self.handle_join_game())
        self.JOIN['text'] = 'JOIN GAME'
        self.JOIN.pack({'side': 'left'})
        self.CREATE = Button(self.frame, command=lambda: self.connect(CREATE_GAME))
        self.CREATE['text'] = 'CREATE GAME'
        self.CREATE.pack({'side': 'left'})

    ## Does a request of LIST_GAMES and then asks for user input.
    def handle_join_game(self):
        games = json.loads(self.connect(LIST_GAMES))["games"]

        while True:
            self.JOIN["state"] = DISABLED
            self.CREATE["state"] = DISABLED
            game_id = askstring("Which game do you want to join?", games)
            if game_id == None:
                self.JOIN["state"] = NORMAL
                self.CREATE["state"] = NORMAL
                return
            elif game_id in games:
                break
        new_window = Toplevel(self.master)
        new_window.protocol('WM_DELETE_WINDOW', lambda: self.handle_quit(new_window))
        game_view = GameView(new_window)

        # Starts a new thread which handles the network communication and adds messages to GUI queue for updating
        thread = threading.Thread(target=connect_to_game, args=[game_view, game_id, self.nickname])
        thread.start()

    ## Enables buttons again when window is destroyed, also tells network thread that the connection can be closed
    def handle_quit(self, context):
        global connected
        self.JOIN["state"] = NORMAL
        self.CREATE["state"] = NORMAL
        connected = False
        context.destroy()

    def connect(self, type):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((SERVER, PORT))

        response = ""
        if type == CREATE_GAME:
            client.send(json.dumps({'req': CREATE_GAME}))
            response = client.recv(BUFFER_SIZE)
            assert response == DONE
        elif type == LIST_GAMES:
            client.send(json.dumps({'req': LIST_GAMES}))
            response = client.recv(BUFFER_SIZE)
        client.close()
        return response

############################################################################

## Game View GUI
class GameView:
    def __init__(self, master):
        self.master = master
        self.frame = Frame(self.master)
        self.state = "0" * 81
        self.scores = {}
        self.buttons = []
        self.latest_guess = ""


        ## Setting up the 9x9 grid for sudoku
        Grid.rowconfigure(self.master, 0, weight=1)
        Grid.columnconfigure(self.master, 0, weight=1)
        self.frame.grid(row=0, column=0, stick=N + S + E + W)

        for row_index in range(9):
            self.buttons.append([])
            Grid.rowconfigure(self.frame, row_index, weight=1)
            for col_index in range(9):
                Grid.columnconfigure(self.frame, col_index, weight=1)
                btn = Button(self.frame, command=lambda i=(row_index, col_index): self.new_guess(i[0], i[
                    1]))
                self.buttons[row_index].append(btn)
                btn.grid(row=row_index, column=col_index, sticky=N + S + E + W)
        self.score_label = Label(self.frame)
        self.score_label.grid(row=0, column=10, columnspan=10, rowspan=10, sticky=W + E + N + S)
        self.frame.pack()
        self.periodic_update()

    ## Updates the latest_guess which is being listened by network thread
    def new_guess(self, row_index, col_index):
        print(row_index, col_index)
        current = self.buttons[row_index][col_index]["text"]
        print(current)
        if current != "0":
            return
        guess = ""
        while not (guess in ["1", "2", "3", "4", "5", "6", "7", "8", "9"]):
            guess = askstring("Guess", "1-9")
            if guess is None:
                return
        self.latest_guess = str(row_index) + str(col_index) + str(guess)

    ## Every 1 second the GUI is updated with latest data
    def periodic_update(self):
        for row_index in range(9):
            for col_index in range(9):
                self.buttons[row_index][col_index]["text"] = self.state[row_index * 9 + col_index]
        scores = ""
        for (k, v) in self.scores.iteritems():
            scores += k + ": " + str(v) + "\n"
        self.score_label["text"] = scores
        self.frame.after(1000, self.periodic_update)

## Separate thread which handles networking and updating data in GUI (indirectly)
def connect_to_game(widget, game_id, nickname):
    global connected
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(1.0)
    client.connect((SERVER, PORT))
    connected = True

    client.send(json.dumps({'req': JOIN_GAME, 'nickname': nickname, 'game_id': game_id}))
    resp = client.recv(BUFFER_SIZE)
    if resp == JOIN_OK:
        thread = threading.Thread(target=poll_new_guesses, args=[widget, client])
        thread.start()
        while True:
            msg_json = ""
            try:
                msg_json = json.loads(client.recv(BUFFER_SIZE))
            except Exception as e:
                if not connected:
                    client.close()
                    if len(widget.scores) == 1:
                        tkMessageBox.showinfo("Gratz", "You were the last to leave. You win!")
                    print "Closing connection."
                    return
                continue
            if msg_json['req'] == GAME_STATE:
                widget.state = msg_json['state']
                widget.scores = {}
                for (nickname, score) in msg_json['scores']:
                    widget.scores[nickname] = score
            elif msg_json['req'] == WIN:
                tkMessageBox.showinfo("Game over", msg_json['msg'])
                return
    else:
        print 'Bad response: ' + resp

## Checks whether the latest_guess has been changed and needs to be sent to server
def poll_new_guesses(widget, client):
    while True:
        if widget.latest_guess != "":
            client.send(json.dumps({'req': NEW_GUESS, 'guess': widget.latest_guess}))
            print "Sent a new guess: " + widget.latest_guess
        widget.latest_guess = ""
        time.sleep(0.2)

## Asks for nickname and then starts the Main menu
def main():
    root = Tk()
    nickname = ""
    while (nickname == "") or (" " in nickname) or (len(nickname) > 8):
        nickname = askstring("What's your nickname?", "length <= 8 and spaces not allowed")
        if nickname is None:
            return
    app = Menu(root, nickname)
    root.mainloop()


if __name__ == '__main__':
    main()
