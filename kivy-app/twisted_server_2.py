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

    def connectionMade(self):
        print("Connection")
        # self.transport.write('Register your login > ')

    def connectionLost(self, reason):
        print("Disconnection")
        self.factory.clients.pop(self.login)
        for login, protocol in self.factory.clients.items():
            protocol.sendLine("%s has quit the chat room" % (self.login,))

    def dataReceived(self, data):
        if not self.login:
            self.login = data
            self.factory.clients[self.login] = self
            for login, protocol in self.factory.clients.items():
                protocol.sendLine("%s has joined the chat room" % (self.login,))
        elif data == 'exit':
            self.transport.write('Bye!\n')
            self.transport.loseConnection()
        else:
            for login, protocol in self.factory.clients.items():
                protocol.sendLine("<%s> %s" % (self.login, data))

    def lineReceived(self, line):
        if len(line) == 0:
            return
        if not self.login:
            self.login = line
            self.factory.clients[self.login] = self
            for login, protocol in self.factory.clients.items():
                protocol.sendLine("%s has joined the chat room" % (self.login,))
        elif line == 'exit':
            self.transport.write('Bye!\n')
            self.transport.loseConnection()
        else:
            for login, protocol in self.factory.clients.items():
                protocol.sendLine("<%s> %s" % (self.login, line))

class ChatFactory(protocol.Factory):
    def __init__(self):
        self.clients = {}

    def buildProtocol(self, addr):
        return ChatProtocol(self)

print("Server started")
reactor.listenTCP(port, ChatFactory())
reactor.run()
