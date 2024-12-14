import secrets
from collections import deque
from random import Random

import Client


class GameManager:
	def __init__(self, main):
		self.main = main
		self.cards: deque[int] = deque()
		for i in range(144):
			self.cards.append(i)
		self.seed = secrets.randbelow(2 ** 32)
		self.random = Random(self.seed)
		self.random.shuffle(self.cards)

	def gameInitialize(self):
		clients: list[Client] = self.main.playerManager.clients
		if self.main.configHandler.getBool("standard", "playerRandomOrder"):
			self.randomSortPlayer(clients)
		for i in range(4):
			client = clients[i]
			client.sendEncryptedBytes(i.to_bytes())

	def takeOneCard(self) -> int:
		return self.cards.pop()

	def randomSortPlayer(self, players):
		self.random.shuffle(players)
