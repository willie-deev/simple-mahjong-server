import secrets
from collections import deque
from random import Random
from time import sleep

import Client
from CardType import CardType
from ConfigHandler import DefaultConfig
from Winds import Winds


class GameManager:
	def __init__(self, main):
		self.main = main
		self.cards: deque[int] = deque()
		for i in range(144):
			self.cards.append(i)
		self.seed = secrets.randbelow(2 ** 32)
		self.random = Random(self.seed)
		self.random.shuffle(self.cards)
		self.cardNumberTypeList = list[CardType]()
		for cardType in CardType:
			if cardType.name != "FLOWER":
				for i in range(4):
					self.cardNumberTypeList.append(cardType)
			else:
				for i in range(8):
					self.cardNumberTypeList.append(cardType)

	def gameInitialize(self):
		clients: list[Client] = self.main.playerManager.clients
		if self.main.configHandler.get(DefaultConfig.SERVERSIDE_RANDOM_PLAYER_ORDER) == "True":
			self.randomSortPlayer(clients)
		for i in range(4):
			client = clients[i]
			for wind in Winds:
				if wind.value == i:
					client.sendEncryptedBytes(wind.name.encode())
		for i in range(4):
			for j in range(4):
				client = clients[j]
				cards = list[bytes]()
				for k in range(4):
					cards.append(self.getCardTypeByNumber(self.takeOneCard()).name.encode())
				client.sendEncryptedByteList(cards)
				client.addCards(cards)
			sleep(1)
		sleep(1)

	def getCardTypeByNumber(self, number: int):
		return self.cardNumberTypeList[number]

	def takeOneCard(self) -> int:
		return self.cards.pop()

	def takeOneCardFromBack(self) -> int:
		return self.cards.popleft()

	def randomSortPlayer(self, players):
		self.random.shuffle(players)
