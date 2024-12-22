import secrets
from collections import deque
from random import Random
from time import sleep

import Client
from CardType import CardType
from ConfigHandler import DefaultConfig
from ServerActionType import ServerActionType
from Wind import Wind


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
			for wind in Wind:
				if wind.value == i:
					client.sendServerActionTypeMessage(ServerActionType.CHANGE_WIND, [wind.name.encode()])
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
				sentCard = self.sendRandomCards(client, 1, ServerActionType.SEND_CARD)[0]
				self.sendOtherPlayerGotCard(client)
				print("sent: ", sentCard, " to: ", client.wind)
				while CardType.FLOWER in client.cards:
					sleep(1)
					self.sendDiscardMessage(client, CardType.FLOWER)
					sentCard = self.flowerReplacement(client, ServerActionType.FLOWER_REPLACEMENT)[0]
					print("sent: ", sentCard, " to: ", client.wind, " (flower replacement)")
				client.sendServerActionTypeMessage(ServerActionType.WAIT_DISCARD, [])
				discardedCardType = client.waitForClientDiscard()
				if discardedCardType is None:
					discardedCardType = sentCard
				self.sendDiscardMessage(client, discardedCardType)
				sleep(1)

	def sendOtherPlayerGotCard(self, gotCardClient: Client):
		for client in self.clients:
			if gotCardClient != client:
				client.sendServerActionTypeMessage(ServerActionType.OTHER_PLAYER_GOT_CARD, [gotCardClient.wind.name.encode()])
		for client in self.clients:
			if gotCardClient != client:
				client.waitForClientReceivedOtherPlayerGotCard()

	def sendRandomCards(self, client: Client, cardCount: int, serverActionType: ServerActionType, waitForClientReceive=True):
		cardTypes = list[CardType]()
		for k in range(cardCount):
			cardType = self.getCardTypeByNumber(self.takeOneCard())
			cardTypes.append(cardType)
		self.sendCardTypeList(client, cardTypes, serverActionType)
		client.addCardTypes(cardTypes)
		if waitForClientReceive:
			client.waitForClientReceivedCard()
		return cardTypes

	def allFlowerReplacement(self, clients: list[Client]):
		noFlower = False
		while not noFlower:
			clientReplacedFlowerCount: dict[Client, int] = {}
			for client in clients:
				clientReplacedFlowerCount[client] = len(self.flowerReplacement(client, ServerActionType.START_FLOWER_REPLACEMENT, False))
			self.waitForAllClientsReceiveCard()
			noFlower = True
			for flowerCount in clientReplacedFlowerCount.values():
				if flowerCount != 0:
					noFlower = False
			for client in clients:
				for i in range(clientReplacedFlowerCount[client]):
					self.sendDiscardMessage(client, CardType.FLOWER)

	def sendDiscardMessage(self, discardedClient: Client, cardType: CardType) ->  bool:
		for client in self.clients:
			client.sendServerActionTypeMessage(ServerActionType.CLIENT_DISCARDED, [discardedClient.wind.name.encode(), cardType.name.encode()])
		anyClientCanAction = False
		for client in self.clients:
			if client.waitForClientReceivedDiscard():
				anyClientCanAction = True
		return anyClientCanAction

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
		return newCardTypes

	def cardTypeToBytes(self, cardType: CardType):
		return cardType.name.encode()

	def sendCardTypeList(self, client: Client, cardTypeList: list[CardType], serverActionType: ServerActionType):
		cardBytesList = []
		for cardType in cardTypeList:
			cardBytesList.append(self.cardTypeToBytes(cardType))
		client.sendServerActionTypeMessage(serverActionType, cardBytesList)

	def waitForAllClientsReceiveCard(self):
		print("waiting for all clients received cards")
		for client in self.main.playerManager.clients:
			client.waitForClientReceivedCard()

	# def waitForAllClientsReceiveFlowerCount(self):
	# 	print("waiting for all clients received flower count")
	# 	for client in self.main.playerManager.clients:
	# 		client.waitForClientReceivedFlowerCount()

	def getCardTypeByNumber(self, number: int):
		return self.cardNumberTypeList[number]

	def getCardTypeByName(self, name: str):
		for card in CardType:
			if card.name == name:
				return card

	def takeOneCard(self) -> int:
		return self.cards.pop()

	def takeOneCardFromBack(self) -> int:
		return self.cards.popleft()

	def randomSortPlayer(self, players):
		self.random.shuffle(players)
