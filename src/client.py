import json, socket
import threading
from tkSimpleDialog import askstring
from Tkinter import *

import time

from common import *

SERVER = "127.0.0.1"
PORT = 6666


class Menu():
    def __init__(self, master):
        self.master = master
        self.frame = Frame(self.master)
        self.create_buttons()
        self.frame.pack()

    def create_buttons(self):
        self.JOIN = Button(self.frame, command=lambda: self.handle_join_game())
        self.JOIN['text'] = 'JOIN GAME'
        self.JOIN.pack({'side': 'left'})
        self.CREATE = Button(self.frame, command=lambda: self.connect(CREATE_GAME))
        self.CREATE['text'] = 'CREATE GAME'
        self.CREATE.pack({'side': 'left'})
        self.LIST = Button(self.frame, command=lambda: self.connect(LIST_GAMES))
        self.LIST['text'] = 'LIST GAMES'
        self.LIST.pack({'side': 'left'})

    def handle_join_game(self):
        new_window = Toplevel(self.master)
        game_view = GameView(new_window)
        thread = threading.Thread(target=connect_to_game, args=[game_view])
        thread.start()

    def connect(self, type):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((SERVER, PORT))

        if type == CREATE_GAME:
            client.send(json.dumps({'req': CREATE_GAME}))
            response = client.recv(BUFFER_SIZE)
            print("Response: " + response)
        elif type == LIST_GAMES:
            client.send(json.dumps({'req': LIST_GAMES}))
            response = client.recv(BUFFER_SIZE)
            print("Response: " + response)
        elif type == JOIN_GAME:
            client.send(json.dumps({'req': JOIN_GAME, 'nickname': "hannes", 'game_id': raw_input("ID? > ")}))
            resp = client.recv(BUFFER_SIZE)
            if resp == JOIN_OK:
                while True:
                    msg_json = json.loads(client.recv(BUFFER_SIZE))
                    if msg_json['req'] == GAME_STATE:
                        print(msg_json['state'])
            else:
                print 'Bad response: ' + resp


class GameView:
    def __init__(self, master):
        self.master = master
        self.frame = Frame(self.master)
        self.state = "0" * 81
        self.buttons = []
        self.latest_guess = ""

        Grid.rowconfigure(self.master, 0, weight=1)
        Grid.columnconfigure(self.master, 0, weight=1)
        self.frame.grid(row=0, column=0, stick=N + S + E + W)

        for row_index in range(9):
            self.buttons.append([])
            Grid.rowconfigure(self.frame, row_index, weight=1)
            for col_index in range(9):
                Grid.columnconfigure(self.frame, col_index, weight=1)
                btn = Button(self.frame, command=lambda i=(row_index, col_index): self.new_guess(i[0], i[
                    1]))  # create a button inside frame
                self.buttons[row_index].append(btn)
                btn.grid(row=row_index, column=col_index, sticky=N + S + E + W)
        self.frame.pack()
        self.periodic_update()

    def new_guess(self, row_index, col_index):
        print(row_index, col_index)
        current = self.buttons[row_index][col_index]["text"]
        print(current)
        if current != "0":
            return
        guess = askstring("Guess", "1-9")
        self.latest_guess = str(row_index)+str(col_index)+str(guess)

    def periodic_update(self):
        for row_index in range(9):
            for col_index in range(9):
                self.buttons[row_index][col_index]["text"] = self.state[row_index * 9 + col_index]
        self.frame.after(1000, self.periodic_update)


def connect_to_game(widget):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((SERVER, PORT))

    game_id = raw_input("ID? > ")  # TODO GAME ID LIST
    nickname = "hannes2"
    client.send(json.dumps({'req': JOIN_GAME, 'nickname': nickname, 'game_id': game_id}))
    resp = client.recv(BUFFER_SIZE)
    if resp == JOIN_OK:
        thread = threading.Thread(target=poll_new_guesses, args=[widget, client])
        thread.start()
        while True:
            msg_json = json.loads(client.recv(BUFFER_SIZE))
            if msg_json['req'] == GAME_STATE:
                widget.state = msg_json['state']
    else:
        print 'Bad response: ' + resp


def poll_new_guesses(widget, client):
    while True:
        if widget.latest_guess != "":
            client.send(json.dumps({'req': NEW_GUESS, 'guess': widget.latest_guess}))
            print "Sent a new guess: " + widget.latest_guess
        widget.latest_guess = ""
        time.sleep(0.2)


def main():
    root = Tk()
    app = Menu(root)
    root.mainloop()


if __name__ == '__main__':
    main()
