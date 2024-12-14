import socket

import PlayerManager
from KeyUtils import KeyUtils


class Main:
	def __init__(self):
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.keyUtils = KeyUtils()
		self.playerManager = PlayerManager.PlayerManager(self)

	def main(self):
		host = "0.0.0.0"
		port = 12345
		self.socket.bind((host, port))
		print("socket binded to port", port)
		self.socket.listen()
		print("socket is listening")
		self.playerManager.waitPlayers(self.socket)
		self.socket.close()


if __name__ == '__main__':
	main = Main()
	main.main()
