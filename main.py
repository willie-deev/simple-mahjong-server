import socket

import playerManager


def Main():
	host = "0.0.0.0"
	port = 12345
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.bind((host, port))
	print("socket binded to port", port)
	s.listen()
	print("socket is listening")
	playerManager.waitPlayers(s)


if __name__ == '__main__':
	Main()
