import secrets
from collections import deque
from random import Random
from time import sleep

import CardUtils
import Client
from CardActionType import CardActionType
from CardType import CardType
from ConfigHandler import DefaultConfig
from ServerActionType import ServerActionType
from Wind import Wind


class GameManager:
	def __init__(self, main):
		self.clients: list[Client] = []
		self.main = main
		self.cards: deque[int] = deque()
		for i in range(144):
			self.cards.append(i)
		self.seed = secrets.randbelow(2 ** 32)
		self.random = Random(self.seed)
		self.random.shuffle(self.cards)


		# eastCards: list[int] = [1,2,3,5,6,7,9,10,11,13,14,15,17,18,19,21]
		# southCards: list[int] = [1,2,3,5,6,7,9,10,11,13,14,15,17,18,19,21]
		# westCards: list[int] = [1,2,3,5,6,7,9,10,11,13,14,15,17,18,19,21]
		# northCards: list[int] = [1,2,3,5,6,7,9,10,11,13,14,15,17,18,19,21]
		# for i in range(4):
		# 	for j in range(4):
		# 		self.cards.append(eastCards[i*4+j])
		# 	for j in range(4):
		# 		self.cards.append(southCards[i*4+j])
		# 	for j in range(4):
		# 		self.cards.append(westCards[i*4+j])
		# 	for j in range(4):
		# 		self.cards.append(northCards[i*4+j])
		# self.cards.append(1)





		self.cardNumberTypeList = list[CardType]()
		self.nextClientIndex = 0
		self.nextClientCardLocation = 1
		for cardType in CardType:
			if cardType.name != "FLOWER":
				for i in range(4):
					self.cardNumberTypeList.append(cardType)
			else:
				for i in range(8):
					self.cardNumberTypeList.append(cardType)
		self.anyClientWon = False

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
		self.nextClientIndex = 0
		self.nextClientCardLocation = 1
		while True:
			client = self.clients[self.nextClientIndex]
			if self.nextClientCardLocation == 1 or self.nextClientCardLocation == -1:
				if self.nextClientCardLocation == 1:
					sentCard = self.sendRandomCards(client, 1, ServerActionType.SEND_CARD)[0]
				else:
					sentCard = self.sendRandomCards(client, 1, ServerActionType.SEND_CARD, fromBack=True)[0]
				self.sendOtherPlayerGotCard(client)
				print("sent: ", sentCard, " to: ", client.wind)
				while CardType.FLOWER in client.cards:
					sleep(1)
					self.sendDiscardMessage(client, CardType.FLOWER)
					sentCard = self.flowerReplacement(client, ServerActionType.FLOWER_REPLACEMENT)[0]
					print("sent: ", sentCard, " to: ", client.wind, " (flower replacement)")
			while True:
				print("wait client discard")
				client.sendServerActionTypeMessage(ServerActionType.WAIT_DISCARD, [])
				if client.ready is True:
					sleep(1)
					result = None
				else:
					result = client.waitForClientDiscard()
				if result is not None:
					discardedCardType = result[0]
					selfCardActionType: CardActionType = result[1]
					if selfCardActionType is not None:
						selfCardActionCards: list[CardType] = result[2]
						if selfCardActionType == CardActionType.CONCEALED_KONG:
							if selfCardActionType == CardActionType.CONCEALED_KONG:
								for i in range(4):
									client.cards.remove(selfCardActionCards[0])
									client.actionedCards.append(selfCardActionCards[0])
								self.clientConcealedKong(client)
								sentCard = self.sendRandomCards(client, 1, ServerActionType.SEND_CARD, fromBack=True)[0]
								while CardType.FLOWER in client.cards:
									sleep(1)
									self.sendDiscardMessage(client, CardType.FLOWER)
									sentCard = self.flowerReplacement(client, ServerActionType.FLOWER_REPLACEMENT)[0]
									print("sent: ", sentCard, " to: ", client.wind, " (flower replacement)")
						elif selfCardActionType == CardActionType.READY:
							testCards: list[CardType] = client.cards[:]
							print("discardedCardType: ", selfCardActionCards[0])
							testCards.remove(selfCardActionCards[0])
							print(CardUtils.calCanReady(testCards))
							testCards.sort(key=lambda v: v.value)
							print(testCards)
							if CardUtils.calCanReady(testCards) == 1:
								discardedCardType = selfCardActionCards[0]
								self.clientReady(client)
								client.ready = True
								break
						elif selfCardActionType == CardActionType.WIN:
							testCards: list[CardType] = client.cards[:]
							testCards.sort(key=lambda v: v.value)
							print("CardUtils.calCanWin(testCards): ", CardUtils.calCanWin(testCards))
							self.clientWon()
							return
					else:
						break
				else:
					discardedCardType = None
					break
			if discardedCardType not in client.cards or discardedCardType is None:
				if self.nextClientCardLocation == 1 or self.nextClientCardLocation == -1:
					discardedCardType = sentCard
				else:
					discardedCardType = client.cards[-1]
			anyClientCanAction = self.sendDiscardMessage(client, discardedCardType)
			client.removeCardType(discardedCardType)
			if anyClientCanAction is True:
				if self.handleAllClientsActions(discardedCardType, client) is True:
					continue
			self.nextClientIndex += 1
			if self.nextClientIndex >= len(self.clients):
				self.nextClientIndex = 0
			self.nextClientCardLocation = 1
			sleep(1)

	def clientReady(self, readyClient: Client):
		for client in self.clients:
			client.sendServerActionTypeMessage(ServerActionType.PLAYER_READY, [readyClient.wind.name.encode()])
		for client in self.clients:
			client.waitClientReceivedPlayerReadyEvent()

	def clientConcealedKong(self, concealedKongClient: Client):
		for client in self.clients:
			client.sendServerActionTypeMessage(ServerActionType.CLIENT_CONCEALED_KONG, [concealedKongClient.wind.name.encode()])
		for client in self.clients:
			client.waitForClientReceivedConcealedKongEvent()

	def handleAllClientsActions(self, discardedCardType: CardType, discardedClient: Client):
		for client in self.clients:
			client.waitingForClientCardActionEvent = True
			client.sendServerActionTypeMessage(ServerActionType.WAIT_CARD_ACTION, [])
		allClientCardActionTypes: dict[Client, CardActionType] = {}
		allClientCardActionCards: dict[Client, list[CardType]] = {}
		for client in self.clients:
			cardActionTypeCardsTuple = client.waitForClientCardActionEvent()
			if cardActionTypeCardsTuple is None:
				continue
			cardActionType, cardActionCards = cardActionTypeCardsTuple[0], cardActionTypeCardsTuple[1]
			allClientCardActionTypes[client] = cardActionType
			allClientCardActionCards[client] = cardActionCards
			print("cardActionType: ", cardActionType, " cardActionCards: ", cardActionCards)
		print("allClientCardActionTypes: ", allClientCardActionTypes, " allClientCardActionCards: ", allClientCardActionCards)
		actionClient: Client = None
		cardActionType: CardActionType | None = None
		if CardActionType.CHOW in allClientCardActionTypes.values():
			for testClient, testCardActionType in allClientCardActionTypes.items():
				if testCardActionType == CardActionType.CHOW:
					if discardedClient.wind.value - testClient.wind.value == -1 or discardedClient.wind.value - testClient.wind.value == 3:
						testCards: list[CardType] = [discardedCardType] + allClientCardActionCards[testClient]
						if CardUtils.checkCanChow(testCards) is True:
							actionClient = testClient
							cardActionType = CardActionType.CHOW
							break
		if CardActionType.PUNG in allClientCardActionTypes.values():
			for testClient, testCardActionType in allClientCardActionTypes.items():
				if testCardActionType == CardActionType.PUNG and testClient.cards.count(discardedCardType) >= 2:
					actionClient = testClient
					cardActionType = CardActionType.PUNG
					break
		if CardActionType.KONG in allClientCardActionTypes.values():
			for testClient, testCardActionType in allClientCardActionTypes.items():
				if testCardActionType == CardActionType.KONG and testClient.cards.count(discardedCardType) == 3:
					actionClient = testClient
					cardActionType = CardActionType.KONG
					break
		if CardActionType.WIN in allClientCardActionTypes.values():
			for testClient, testCardActionType in allClientCardActionTypes.items():
				if testCardActionType == CardActionType.WIN:
					testCards: list[CardType] = testClient.cards[:]
					testCards.append(discardedCardType)
					testCards.sort(key=lambda card: card.value)
					print("CardUtils.calCanWin(testCards): ", CardUtils.calCanWin(testCards))
					if CardUtils.calCanWin(testCards) is True:
						actionClient = testClient
						cardActionType = CardActionType.WIN
						self.anyClientWon = True
		print("actionClient: ", actionClient, " cardActionType: ", cardActionType)
		if actionClient is None or cardActionType is None:
			self.sendNoPlayerPerformedCardAction()
			return
		print(actionClient.wind, " performed: ", cardActionType, " cards: ", allClientCardActionCards[actionClient])
		cardActionType = allClientCardActionTypes[actionClient]
		cardActionCards = allClientCardActionCards[actionClient]
		if cardActionType == CardActionType.CHOW:
			actionClient.cards.remove(cardActionCards[0])
			actionClient.cards.remove(cardActionCards[1])
			actionClient.actionedCards.append(cardActionCards[0])
			actionClient.actionedCards.append(discardedCardType)
			actionClient.actionedCards.append(cardActionCards[1])
			cardActionCards = [
				cardActionCards[0],
				discardedCardType,
				cardActionCards[1]
			]
			self.nextClientCardLocation = 0
		if cardActionType == CardActionType.PUNG:
			actionClient.cards.remove(cardActionCards[0])
			actionClient.cards.remove(cardActionCards[0])
			actionClient.actionedCards.append(cardActionCards[0])
			actionClient.actionedCards.append(cardActionCards[0])
			actionClient.actionedCards.append(cardActionCards[0])
			cardActionCards = [
				cardActionCards[0],
				cardActionCards[0],
				cardActionCards[0]
			]
			self.nextClientCardLocation = 0
		if cardActionType == CardActionType.KONG:
			actionClient.cards.remove(cardActionCards[0])
			actionClient.cards.remove(cardActionCards[0])
			actionClient.cards.remove(cardActionCards[0])
			actionClient.actionedCards.append(cardActionCards[0])
			actionClient.actionedCards.append(cardActionCards[0])
			actionClient.actionedCards.append(cardActionCards[0])
			actionClient.actionedCards.append(cardActionCards[0])
			cardActionCards = [
				cardActionCards[0],
				cardActionCards[0],
				cardActionCards[0],
				cardActionCards[0]
			]
			self.nextClientCardLocation = -1
		self.nextClientIndex = self.clients.index(actionClient)
		self.sendPlayerPerformedCardAction(actionClient, cardActionType, cardActionCards)
		return True
	def clientWon(self):
		for client in self.clients:
			for client2 in self.clients:
				client2: Client = client2
				data: list[bytes] = [client.wind.name.encode()]
				for card in client.cards:
					data.append(card.name.encode())
				client2.sendServerActionTypeMessage(ServerActionType.GAME_OVER, data)

	def sendNoPlayerPerformedCardAction(self):
		for client in self.clients:
			client.sendServerActionTypeMessage(ServerActionType.CLIENT_PERFORMED_CARD_ACTION, [])

	def sendPlayerPerformedCardAction(self, performClient: Client, actionType: CardActionType, cardTypes: list[CardType]):
		performedWindBytes = performClient.wind.name.encode()
		actionTypeBytes = actionType.name.encode()
		dataList = [performedWindBytes, actionTypeBytes]
		for card in cardTypes:
			dataList.append(card.name.encode())

		for client in self.clients:
			client.sendServerActionTypeMessage(ServerActionType.CLIENT_PERFORMED_CARD_ACTION, dataList)

	def sendOtherPlayerGotCard(self, gotCardClient: Client):
		for client in self.clients:
			if gotCardClient != client:
				client.sendServerActionTypeMessage(ServerActionType.OTHER_PLAYER_GOT_CARD, [gotCardClient.wind.name.encode()])
		for client in self.clients:
			if gotCardClient != client:
				client.waitForClientReceivedOtherPlayerGotCard()

	def sendRandomCards(self, client: Client, cardCount: int, serverActionType: ServerActionType, waitForClientReceive=True, fromBack = False):
		cardTypes = list[CardType]()
		for k in range(cardCount):
			if fromBack is True:
				cardType = self.getCardTypeByNumber(self.takeOneCardFromBack())
			else:
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
			if client.waitForClientReceivedDiscard() is True:
				anyClientCanAction = True
		return anyClientCanAction

	def flowerReplacement(self, client: Client, serverActionType: ServerActionType, waitForClientReceive=True):
		newCardTypes = list[CardType]()
		flowerCards = list[CardType]()
		for cardType in client.getCardTypes():
			if cardType == CardType.FLOWER:
				flowerCards.append(cardType)
				newCardType = self.getCardTypeByNumber(self.takeOneCardFromBack())
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

	def takeOneCard(self) -> int:
		return self.cards.pop()

	def takeOneCardFromBack(self) -> int:
		return self.cards.popleft()

	def randomSortPlayer(self, players):
		self.random.shuffle(players)

def getCardActionTypeByName(name: str):
	for cardActionType in CardActionType:
		if cardActionType.name == name:
			return cardActionType

def getCardTypeByName(name: str):
		for card in CardType:
			if card.name == name:
				return card