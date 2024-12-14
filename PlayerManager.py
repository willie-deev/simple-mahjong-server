import socket
import threading
from enum import Enum

from Client import Client


class PlayerManager:
	keyExchangedEvent = threading.Event()

	def __init__(self, main):
		self.clients: list[Client] = []
		self.main = main

	def waitClients(self, s: socket):
		for i in range(0, 4):
			c, addr = s.accept()
			print('Connected to :', addr[0], ':', addr[1])
			player = Client(c, self)
			player.sendPubKey()
			self.clients.append(player)
			self.keyExchangedEvent.wait()
			self.keyExchangedEvent.clear()
			for _p in self.clients:
				_p.sendPlayerCount()

		print("all players connected, starting game")
		self.main.gameManager.gameInitialize()


class ClientState(Enum):
	CONNECTED = 1
	KEY_EXCHANGED = 2
