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
		self.clients = None
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
		self.clients: list[Client] = self.main.playerManager.clients
		if self.main.configHandler.get(DefaultConfig.SERVERSIDE_RANDOM_PLAYER_ORDER) == "True":
			self.randomSortPlayer(self.clients)
		for i in range(4):
			client = self.clients[i]
			for wind in Winds:
				if wind.value == i:
					client.sendServerActionType(ServerActionType.CHANGE_WIND, [wind.name.encode()])
					client.wind = wind
		self.waitForAllClientsReceiveCard()
		for i in range(4):
			for j in range(4):
				client = self.clients[j]
				self.sendRandomCards(client, 4, ServerActionType.START_SEND_CARDS, False)
			self.waitForAllClientsReceiveCard()
			sleep(1)
		self.allFlowerReplacement(self.clients)
		print("mainGame")
		self.mainGame()
		print("end")

	def mainGame(self):
		while True:
			for client in self.clients:
				self.sendRandomCards(client, 1, ServerActionType.SEND_CARD)

	def sendRandomCards(self, client: Client, cardCount: int, serverActionType: ServerActionType, waitForClientReceive=True):
		cardTypes = list[CardType]()
		for k in range(cardCount):
			cardType = self.getCardTypeByNumber(self.takeOneCard())
			cardTypes.append(cardType)
		self.sendCardTypeList(client, cardTypes, serverActionType)
		client.addCardTypes(cardTypes)
		if waitForClientReceive:
			client.waitForClientReceivedCard()

	def allFlowerReplacement(self, clients: list[Client]):
		while True:
			for client in clients:
				self.flowerReplacement(client, ServerActionType.START_FLOWER_REPLACEMENT, False)
			self.waitForAllClientsReceiveCard()
			noFlower = True
			for client in clients:
				if CardType.FLOWER in client.getCardTypes():
					noFlower = False
			if noFlower:
				for client in clients:
					for client2 in clients:
						client.sendServerActionType(ServerActionType.FLOWER_COUNT, [client2.wind.name.encode(), client2.flowerCount.to_bytes()])
				self.waitForAllClientsReceiveFlowerCount()
				return
			self.waitForAllClientsReceiveCard()

	def flowerReplacement(self, client: Client, serverActionType: ServerActionType, waitForClientReceive=True):
		newCardTypes = list[CardType]()
		flowerCards = list[CardType]()
		for cardType in client.getCardTypes():
			if cardType == CardType.FLOWER:
				flowerCards.append(cardType)
				newCardType = self.getCardTypeByNumber(self.takeOneCard())
				newCardTypes.append(newCardType)
		self.sendCardTypeList(client, newCardTypes, serverActionType)
		client.removeCardTypes(flowerCards)
		client.addCardTypes(newCardTypes)
		if waitForClientReceive:
			client.waitForClientReceivedCard()

	def cardTypeToBytes(self, cardType: CardType):
		return cardType.name.encode()

	def sendCardTypeList(self, client: Client, cardTypeList: list[CardType], serverActionType: ServerActionType):
		cardBytesList = []
		for cardType in cardTypeList:
			cardBytesList.append(self.cardTypeToBytes(cardType))
		client.sendServerActionType(serverActionType, cardBytesList)

	def waitForAllClientsReceiveCard(self):
		print("waiting for all clients received cards")
		for client in self.main.playerManager.clients:
			client.waitForClientReceivedCard()

	def waitForAllClientsReceiveFlowerCount(self):
		print("waiting for all clients received flower count")
		for client in self.main.playerManager.clients:
			client.waitForClientReceivedFlowerCount()

	def getCardTypeByNumber(self, number: int):
		return self.cardNumberTypeList[number]

	def takeOneCard(self) -> int:
		return self.cards.pop()

	def takeOneCardFromBack(self) -> int:
		return self.cards.popleft()

	def randomSortPlayer(self, players):
		self.random.shuffle(players)
