import socket

import Client

def waitPlayers(s: socket):
    players: list[Client.Client] = []
    for i in range(0, 4):
        c, addr = s.accept()
        print('Connected to :', addr[0], ':', addr[1])
        player = Client.Client(c)
        players.append(player)
        for _p in players:
            _p.sendInt(len(players))
    print("all players connected, starting game")