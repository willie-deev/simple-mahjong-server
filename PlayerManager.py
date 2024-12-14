import socket
from enum import Enum

import Client


class PlayerManager:
	def __init__(self, main):
		self.players: list[Client.Client] = []
		self.main = main

	def waitPlayers(self, s: socket):
		for i in range(0, 4):
			c, addr = s.accept()
			print('Connected to :', addr[0], ':', addr[1])
			player = Client.Client(c, self)
			player.sendPubKey()
			for _p in self.players:
				_p.sendEncryptedBytes(int.to_bytes(len(self.players) + 1))
			self.players.append(player)
		print("all players connected, starting game")


class ClientState(Enum):
	CONNECTED = 1
	KEY_EXCHANGED = 2
