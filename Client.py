import threading

from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes

from CardType import CardType
from ClientActionType import ClientActionType
from ServerActionType import ServerActionType


class Client:

	def __init__(self, _c, playerManager):
		self.sendMessageRsaEncrypter = None
		self.clientAesKey = None
		self.playerManager = playerManager
		self.clientPubKey = None
		self.socket = _c
		self.thread = threading.Thread(target=self.recvThread)
		self.thread.start()
		self.cards = list[CardType]()
		self.clientReceivedCardEvent = threading.Event()
		self.clientReceivedFlowerCount = threading.Event()
		self.flowerCount = 0
		self.wind = None

	def waitForClientReceivedCard(self, timeout=1):
		if not self.clientReceivedCardEvent.wait(timeout):
			raise Exception("client received card event timeout")
		self.clientReceivedCardEvent.clear()

	def waitForClientReceivedFlowerCount(self, timeout=1):
		if not self.clientReceivedFlowerCount.wait(timeout):
			raise Exception("client received flower count timeout")
		self.clientReceivedFlowerCount.clear()

	def getCardTypes(self) -> list[CardType]:
		return self.cards

	def addCardType(self, card: CardType):
		self.cards.append(card)

	def addCardTypes(self, cards: list[CardType]):
		for card in cards:
			self.addCardType(card)

	def removeCardType(self, card: CardType):
		if card == CardType.FLOWER:
			self.flowerCount += 1
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
			match clientActionType:
				case ClientActionType.RECEIVED_CARDS:
					self.clientReceivedCardEvent.set()
					print(receivedList)
				case ClientActionType.RECEIVED_FLOWER_COUNT:
					self.clientReceivedFlowerCount.set()

	def sendServerActionType(self, serverActionType: ServerActionType, messages: list):
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
		self.socket.sendall(dataLength[0])
		self.socket.sendall(dataLength[1])

		for data in messages:
			encryptedData = self.encryptMessage(data)
			self.socket.sendall(encryptedData[0])
			self.socket.sendall(encryptedData[1])

	def receiveEncryptedMessages(self) -> list:
		iv = self.receiveData(256)
		message = self.receiveData(256)
		dataLength = self.decryptReceivedMessage(iv, message)
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
		return aesCipher.decrypt(rsaDecrypted)

	def receiveData(self, receiveByteCount: int):
		receivedData = self.socket.recv(receiveByteCount)
		while len(receivedData) < receiveByteCount:
			if not receivedData:
				print('server disconnected')
				self.socket.close()
				return
			receivedData += self.socket.recv(receiveByteCount - len(receivedData))
		return receivedData
