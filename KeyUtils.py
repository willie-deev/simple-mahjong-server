from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.PublicKey.RSA import RsaKey


class KeyUtils:
	def __init__(self):
		keyPair = RSA.generate(2048)
		self.pubKey: RsaKey = keyPair.publickey()
		self.cryptor = PKCS1_OAEP.new(keyPair)

	def getPublicKeyBytes(self) -> bytes:
		return self.pubKey.exportKey()

	def decryptRsa(self, msg: bytes) -> bytes:
		decrypted = self.cryptor.decrypt(msg)
		return decrypted
