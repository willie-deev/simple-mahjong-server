import threading

from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes

from CardActionType import CardActionType
from CardType import CardType
from ClientActionType import ClientActionType
from ServerActionType import ServerActionType
from Wind import Wind


class Client:

	def __init__(self, _c, playerManager):
		self.sendMessageRsaEncrypter = None
		self.clientAesKey = None
		self.playerManager = playerManager
		self.clientPubKey = None
		self.socket = _c
		self.thread = threading.Thread(target=self.recvThread)
		self.thread.start()
		self.cards: list[CardType] = []

		self.clientReceivedCardEvent = threading.Event()
		self.clientReceivedDiscardEvent = threading.Event()
		self.clientDiscardEvent = threading.Event()
		self.clientReceivedOtherPlayerGotCardEvent = threading.Event()
		self.clientActionedEvent = threading.Event()

		self.clientCanAction: bool | None = None

		self.wind: Wind | None = None
		self.discardedCard: CardType | None = None
		self.choseCardActionType: CardActionType | None  = None
		self.choseCardActionCards = None
		self.haveAction = False

	def waitForClientCardActionEvent(self, timeout=10):
		received = self.clientActionedEvent.wait(timeout)
		self.clientActionedEvent.clear()
		if received is True and self.haveAction is True:
			return self.choseCardActionType, self.choseCardActionCards
		self.choseCardActionType = None
		self.choseCardActionCards = None
		return None

	def waitForClientReceivedOtherPlayerGotCard(self, timeout=1):
		if not self.clientReceivedOtherPlayerGotCardEvent.wait(timeout):
			raise Exception("client received other plater got card event timeout")
		self.clientReceivedOtherPlayerGotCardEvent.clear()

	def waitForClientReceivedCard(self, timeout=1):
		if not self.clientReceivedCardEvent.wait(timeout):
			raise Exception("client received card event timeout")
		self.clientReceivedCardEvent.clear()

	def waitForClientDiscard(self, timeout=10):
		received = self.clientDiscardEvent.wait(timeout)
		self.clientDiscardEvent.clear()
		if received:
			return self.discardedCard
		return None

	def waitForClientReceivedDiscard(self, timeout=1):
		if not self.clientReceivedDiscardEvent.wait(timeout):
			raise Exception("client received discard event timeout")
		self.clientReceivedDiscardEvent.clear()
		return self.clientCanAction

	def getCardTypes(self) -> list[CardType]:
		return self.cards

	def addCardType(self, card: CardType):
		self.cards.append(card)

	def addCardTypes(self, cards: list[CardType]):
		for card in cards:
			self.addCardType(card)

	def removeCardType(self, card: CardType):
		self.cards.remove(card)

	def removeCardTypes(self, cards: list[CardType]):
		for card in cards:
			self.removeCardType(card)

	def sendPlayerCount(self):
		self.sendEncryptedBytes(int.to_bytes(len(self.playerManager.clients)))

	def sendPubKey(self):
		self.socket.sendall(self.playerManager.main.keyUtils.getPublicKeyBytes())

	def recvThread(self):
		self.clientPubKey = RSA.importKey(self.receiveData(450))
		self.sendMessageRsaEncrypter = PKCS1_OAEP.new(self.clientPubKey)
		data = self.receiveData(256)
		self.clientAesKey = self.playerManager.main.keyUtils.decryptRsa(data)
		self.playerManager.keyExchangedEvent.set()
		while True:
			receivedList = self.receiveEncryptedMessages()
			clientActionType = None
			for actionType in ClientActionType:
				if receivedList[0].decode() == actionType.name:
					clientActionType = actionType
			print(self.wind, " receivedList: ", receivedList)
			receivedList = receivedList[1:]
			match clientActionType:
				case ClientActionType.RECEIVED_CARDS:
					self.clientReceivedCardEvent.set()
				case ClientActionType.DISCARD:
					cardTypeName = receivedList[0].decode()
					import GameManager
					cardType = GameManager.getCardTypeByName(cardTypeName)
					self.discardedCard = cardType
					self.clientDiscardEvent.set()
					print(self.wind, " discarded: ", " ", cardTypeName)
				case ClientActionType.RECEIVED_DISCARD_ACTION:
					self.clientCanAction = bool.from_bytes(receivedList[0])
					print("self.clientCanAction: ", self.clientCanAction)
					self.clientReceivedDiscardEvent.set()
				case ClientActionType.RECEIVED_OTHER_PLAYER_GOT_CARD:
					self.clientReceivedOtherPlayerGotCardEvent.set()
				case ClientActionType.PERFORM_CARD_ACTION:
					if len(receivedList) != 0:
						import GameManager
						cardActionType = GameManager.getCardActionTypeByName(receivedList[0].decode())
						receivedList = receivedList[1:]
						cardTypes: list[CardType] = []
						for cardNameBytes in receivedList:
							cardTypes.append(GameManager.getCardTypeByName(cardNameBytes.decode()))
						self.choseCardActionType = cardActionType
						self.choseCardActionCards = cardTypes
						self.haveAction = True
					else:
						self.haveAction = False
					self.clientActionedEvent.set()

	def sendServerActionTypeMessage(self, serverActionType: ServerActionType, messages: list):
		newList = [serverActionType.name.encode()] + messages
		self.sendEncryptedByteList(newList)

	def sendEncryptedBytes(self, message: bytes):
		dataLength = self.encryptMessage(int.to_bytes(1))
		self.socket.sendall(dataLength[0])
		self.socket.sendall(dataLength[1])

		data = self.encryptMessage(message)
		self.socket.sendall(data[0])
		self.socket.sendall(data[1])

	def sendEncryptedByteList(self, messages: list):
		dataLength = self.encryptMessage(int.to_bytes(len(messages)))
		sendDatas: bytes = dataLength[0] + dataLength[1]
		for data in messages:
			encryptedData = self.encryptMessage(data)
			sendDatas += encryptedData[0] + encryptedData[1]
		self.socket.sendall(sendDatas)

	def receiveEncryptedMessages(self) -> list:
		iv = self.receiveData(256)
		message = self.receiveData(256)
		dataLength = self.decryptReceivedMessage(iv, message)
		# print(self.wind, " :dataLength: ", dataLength)
		messageList = list()
		for i in range(int.from_bytes(dataLength)):
			iv = self.receiveData(256)
			message = self.receiveData(256)
			data = self.decryptReceivedMessage(iv, message)
			messageList.append(data)
		return messageList

	def encryptMessage(self, message: bytes) -> tuple[bytes, bytes]:
		iv = get_random_bytes(16)
		aesCipher = AES.new(self.clientAesKey, AES.MODE_CFB, iv=iv)
		encryptedIv = self.sendMessageRsaEncrypter.encrypt(iv)
		encryptedMessage = self.sendMessageRsaEncrypter.encrypt((aesCipher.encrypt(message)))
		return encryptedIv, encryptedMessage

	def decryptReceivedMessage(self, iv: bytes, message: bytes) -> bytes:
		decryptedIV = self.playerManager.main.keyUtils.decryptRsa(iv)
		aesCipher = AES.new(self.clientAesKey, AES.MODE_CFB, iv=decryptedIV)
		rsaDecrypted = self.playerManager.main.keyUtils.decryptRsa(message)
		# print("len(decryptedIV), \" \", len(rsaDecrypted): ", len(decryptedIV), " ", len(rsaDecrypted))
		return aesCipher.decrypt(rsaDecrypted)

	def receiveData(self, receiveByteCount: int):
		try:
			receivedData = self.socket.recv(receiveByteCount)
			while len(receivedData) < receiveByteCount:
				if not receivedData:
					print('server disconnected')
					self.socket.close()
					return
				receivedData += self.socket.recv(receiveByteCount - len(receivedData))
			return receivedData
		except Exception as e:
			self.socket.close()
			print(e)