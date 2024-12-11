import socket
import threading


class Client:
    socket: socket
    thread: threading.Thread

    def __init__(self, _c):
        self.socket = _c
        self.thread = threading.Thread(target=self.recvThread)
        self.thread.start()

    def sendBytes(self, message: bytes):
        data: bytes = int(1).to_bytes(length=1) + len(message).to_bytes(length=4) + message
        self.socket.sendall(data)

    def sendInt(self, message: int):
        data: bytes = int(2).to_bytes(length=1) + int(4).to_bytes(length=4) + message.to_bytes(length=4)
        self.socket.sendall(data)

    def sendStr(self, message: str):
        data: bytes = int(3).to_bytes(length=1) + len(message.encode('utf-8')).to_bytes(length=4) + message.encode('utf-8')
        self.socket.sendall(data)

    def recvThread(self):
        while True:
            data = self.socket.recv(1024)
            if not data:
                print(str(self.socket.getsockname()) + ' disconnected')
                break
            self.socket.send(data)
        self.socket.close()
