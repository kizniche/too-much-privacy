#!/usr/bin/python

import sys, errno

if len(sys.argv) != 2:
    print 'Required parameter not passed. Run:\n\n\t./chat-server.py <port>\n'
    sys.exit(errno.EINVAL)

port = int(sys.argv[1])

# simple single-room chat server, derived from publish/subscribe
from twisted.internet import reactor, protocol
from twisted.protocols import basic

class ChatProtocol(basic.LineReceiver):
    def __init__(self, factory):
        self.factory = factory
        self.login = None
        self.total_data = []
        self.stop_str = '#####END#####'

    def connectionMade(self):
        print("Connection")
        # self.transport.write('Register your login > ')

    def connectionLost(self, reason):
        print("{user} disconnected".format(user=self.login))
        self.factory.clients.pop(self.login)
        for login, protocol in self.factory.clients.items():
            protocol.sendLine("{user} has quit#####END#####".format(self.login))

    def dataReceived(self, data):
        print('Raw_DATA="{}"'.format(data))
        self.combine_data(data)

    def lineReceived(self, line):
        print('Raw_LINE="{}"'.format(line))
        self.combine_data(line)

    def combine_data(self, data):
        self.total_data.append(data)
        if self.stop_str in data:
            total_data_joined = ''.join(self.total_data).split(self.stop_str)[0]
            print('Rec_DATA="{}"'.format(total_data_joined))
            self.received_data(total_data_joined)
            self.total_data = []

    def received_data(self, data):
        if not self.login:
            self.login = data
            print("{user} joined".format(user=self.login))
            self.factory.clients[self.login] = self
            for login, protocol in self.factory.clients.items():
                protocol.sendLine("{user} joined#####END#####".format(user=self.login))
        elif data == 'exit':
            self.transport.write('Bye!')
            self.transport.loseConnection()
        else:
            for login, protocol in self.factory.clients.items():
                if self.login == login:
                    # Communicate back to the user that sent the data
                    pass
                protocol.sendLine("{data}#####END#####".format(data=data))
                # self.transport.write("{data}".format(data=data))


class ChatFactory(protocol.Factory):
    def __init__(self):
        self.clients = {}

    def buildProtocol(self, addr):
        return ChatProtocol(self)

print("Server started")
reactor.listenTCP(port, ChatFactory())
reactor.run()
