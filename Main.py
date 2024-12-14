import socket

from ConfigHandler import ConfigHandler
from GameManager import GameManager
from KeyUtils import KeyUtils
from PlayerManager import PlayerManager


class Main:
	def __init__(self):
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.keyUtils = KeyUtils()
		self.playerManager = PlayerManager(self)
		self.gameManager = GameManager(self)
		self.configHandler = ConfigHandler(self)

	def main(self):
		print(self.gameManager.cards)
		self.configHandler.setDefaults()
		host = "0.0.0.0"
		port = 12345
		self.socket.bind((host, port))
		print("socket binded to port", port)
		self.socket.listen()
		print("socket is listening")
		self.playerManager.waitClients(self.socket)
		self.socket.close()


if __name__ == '__main__':
	main = Main()
	main.main()
