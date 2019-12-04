"""TCP-BLE bridge link"""
from __future__ import absolute_import
import socket
from binascii import hexlify
from .base import BaseLink, LinkTimeoutException, LinkOpenException

HOST, PORT = "127.0.0.1", 6000

_write_chunk_size = 20  # 20 as in android dumps


def recvall(sock, size):
    data = ""
    while len(data) < size:
        try:
            pkt = sock.receive(size - len(data))
        except socket.timeout:
            raise LinkTimeoutException()
        data += pkt
    return data


class TCPLink(BaseLink):
    def __init__(self, *args, **kwargs):
        super(TCPLink, self).__init__(*args, **kwargs)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.connected = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def scan(self):
        res = [("Android UART Bridge", HOST + ":" + str(PORT))]
        return res

    def open(self, port):
        p = port.partition(":")
        host = p[0]
        port = int(p[2], 10)
        print(host, port)
        try:
            self.sock.connect((host, port))
        except socket.timeout:
            raise LinkOpenException
        self.connected = True

    def close(self):
        if self.connected:
            self.sock.close()
            self.connected = False

    def read(self, size):
        data = recvall(self.sock, size)
        if data and self.dump:
            print("<", hexlify(data).upper())
        return data

    def write(self, data):
        if self.dump:
            print(">", hexlify(data).upper())
        size = len(data)
        ofs = 0
        while size:
            chunk_sz = min(size, _write_chunk_size)
            self.sock.sendall(data[ofs : ofs + chunk_sz])
            ofs += chunk_sz
            size -= chunk_sz


__all__ = ["TCPLink"]
