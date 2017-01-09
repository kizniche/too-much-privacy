#!/usr/bin/python
#  chat_server.py

import datetime
import json
import select
import socket
import sys
import time

HOST = ''
SOCKET_LIST = []
RECV_BUFFER = 4096
PORT = 9009


def chat_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(10)

    # add server socket object to the list of readable connections
    SOCKET_LIST.append(server_socket)

    print("[{time}] Chat server started on port {port}".format(
        time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        port=str(PORT)))

    while 1:
        time.sleep(1)
        # get the list sockets which are ready to be read through select
        # 4th arg, time_out  = 0 : poll and never block
        ready_to_read, ready_to_write, in_error = select.select(SOCKET_LIST,
                                                                [], [], 0)
        for sock in ready_to_read:
            # a new connection request received
            if sock == server_socket:
                sockfd, addr = server_socket.accept()
                SOCKET_LIST.append(sockfd)
                print_and_broadcast(
                    server_socket,
                    sockfd,
                    '{:s}:{:d}'.format(*addr),
                    'Connected')
                time.sleep(1)

            # a message from a client, not a new connection
            else:
                # process data received from client,
                try:
                    # receiving data from the socket.
                    data = sock.recv(RECV_BUFFER)
                    if data:
                        # there is something in the socket
                        # print('Message="{}"'.format(data_split))
                        broadcast(server_socket, sock, data)

                    else:
                        # remove the socket that's broken
                        if sock in SOCKET_LIST:
                            SOCKET_LIST.remove(sock)

                        # at this stage, no data means probably the
                        # connection has been broken
                        print_and_broadcast(
                            server_socket,
                            sock,
                            '{:s}:{:d}'.format(*addr),
                            'Disconnected')
                except:
                    print_and_broadcast(
                        server_socket,
                        sock,
                        '{:s}:{:d}'.format(*addr),
                        'Disconnected')
                    continue

    server_socket.close()


def print_and_broadcast(server_socket, sock, nick, message):
    print("[{time}] {nick} {message}".format(
        time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        nick=nick,
        message=message))
    broadcast(server_socket, sock, json.dumps({"nick": nick, "data": message}))


# broadcast chat messages to all connected clients
def broadcast(server_socket, sock, message):
    for socket in SOCKET_LIST:
        # send the message only to peer
        if socket != server_socket and socket != sock:
            try:
                socket.send(message)
            except:
                print("except send socket")
                # broken socket connection
                socket.close()
                # broken socket, remove it
                if socket in SOCKET_LIST:
                    SOCKET_LIST.remove(socket)


if __name__ == "__main__":
    sys.exit(chat_server())
