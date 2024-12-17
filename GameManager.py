import secrets
from collections import deque
from random import Random
from time import sleep

import Client
from CardType import CardType
from ConfigHandler import DefaultConfig
from ServerActionType import ServerActionType
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
					client.sendServerActionType(ServerActionType.CHANGE_WIND, [wind.name.encode()])
					client.wind = wind
		self.waitForAllClientsReceiveCard()
		for i in range(4):
			for j in range(4):
				client = clients[j]
				self.sendRandomCards(client, 4, False)
			self.waitForAllClientsReceiveCard()
			sleep(1)
		sleep(1)
		self.allFlowerReplacement(clients)

	def sendRandomCards(self, client: Client, cardCount: int, waitForClientReceive=True):
		cardTypes = list[CardType]()
		for k in range(cardCount):
			cardType = self.getCardTypeByNumber(self.takeOneCard())
			cardTypes.append(cardType)
		self.sendCardTypeList(client, cardTypes)
		client.addCardTypes(cardTypes)
		if waitForClientReceive:
			client.waitForClientReceivedCard()

	def allFlowerReplacement(self, clients: list[Client]):
		while True:
			for client in clients:
				self.flowerReplacement(client, False)
			self.waitForAllClientsReceiveCard()
			noFlower = True
			for client in clients:
				if CardType.FLOWER in client.getCardTypes():
					noFlower = False
			if noFlower:
				for client in clients:
					for client2 in clients:
						client.sendServerActionType(ServerActionType.FLOWER_COUNT, [client2.wind.name.encode(), client2.flowerCount.to_bytes()])
				self.waitForAllClientsReceiveCard()
				return

	def flowerReplacement(self, client: Client, waitForClientReceive=True):
		newCardTypes = list[CardType]()
		flowerCards = list[CardType]()
		for cardType in client.getCardTypes():
			if cardType == CardType.FLOWER:
				flowerCards.append(cardType)
				newCardType = self.getCardTypeByNumber(self.takeOneCard())
				newCardTypes.append(newCardType)
		self.sendCardTypeList(client, newCardTypes)
		client.removeCardTypes(flowerCards)
		client.addCardTypes(newCardTypes)
		if waitForClientReceive:
			client.waitForClientReceivedCard()

	def cardTypeToBytes(self, cardType: CardType):
		return cardType.name.encode()

	def sendCardTypeList(self, client: Client, cardTypeList: list[CardType]):
		cardBytesList = []
		for cardType in cardTypeList:
			cardBytesList.append(self.cardTypeToBytes(cardType))
		client.sendServerActionType(ServerActionType.START_SEND_CARDS, cardBytesList)

	def waitForAllClientsReceiveCard(self):
		print("waiting for all clients received cards")
		for client in self.main.playerManager.clients:
			client.waitForClientReceivedCard()

	def getCardTypeByNumber(self, number: int):
		return self.cardNumberTypeList[number]

	def takeOneCard(self) -> int:
		return self.cards.pop()

	def takeOneCardFromBack(self) -> int:
		return self.cards.popleft()

	def randomSortPlayer(self, players):
		self.random.shuffle(players)
