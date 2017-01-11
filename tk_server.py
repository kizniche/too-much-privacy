#!/usr/bin/python

import datetime
import json
import select
import socket
import time
from threading import Thread


class TMPServer(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.server_host = '127.0.0.1'
        self.server_port = 9009
        self.s_server = None
        self.read_list = None
        self.running = False

    def run(self):
        self.running = True
        self.s_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s_server.bind((self.server_host, self.server_port))
        self.s_server.listen(5)
        print("[{time}] Server Started at {ip}:{port}".format(
            time=timestamp(), ip=self.server_host, port=self.server_port))

        # Start receive loop
        self.read_list = [self.s_server]
        while self.running:
            readable, writable, errored = select.select(self.read_list, [], [])
            for sock in readable:
                # a new connection request received
                if sock == self.s_server:
                    sockfd, addr = self.s_server.accept()
                    self.read_list.append(sockfd)
                    self.print_and_broadcast(
                        self.s_server,
                        sockfd,
                        '{:s}:{:d} Connected'.format(*addr))
                    time.sleep(1)

                # a message from a client, not a new connection
                else:
                    recv_msg = sock.recv(2024)
                    if recv_msg:
                        self.broadcast(self.s_server, sock, recv_msg)
                    else:
                        self.s_server.close()
                        self.read_list.remove(self.s_server)
                        print("[Server] {:s}:{:d} Disconnected\n".format(*addr))

    def print_and_broadcast(self, server_socket, sock, message):
        print("[{time}] {message}".format(time=timestamp(),
                                          message=message))
        self.broadcast(server_socket, sock, json.dumps({"data": message}))

    # broadcast chat messages to all connected clients
    def broadcast(self, server_socket, sock, message):
        for each_socket in self.read_list:
            # send the message only to peer
            if each_socket != server_socket and each_socket != sock:
                try:
                    each_socket.send(message)
                except:
                    print("except send socket")
                    # broken socket connection
                    each_socket.close()
                    # broken socket, remove it
                    if each_socket in self.read_list:
                        self.read_list.remove(each_socket)

    def terminate(self):
        print("[{time}] [Server] Terminating Server".format(time=timestamp()))
        self.running = False


def timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


if __name__ == '__main__':
    tmp_server = TMPServer()
    tmp_server.setName('TMP Server 1')
    tmp_server.daemon = True
    tmp_server.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[{time}] Keyboard Interrupt received".format(
            time=timestamp()))
        tmp_server.terminate()
