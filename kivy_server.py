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
        self.received_data(data)

    def lineReceived(self, line):
        self.received_data(line)

    def received_data(self, data):
        if not self.login:
            self.login = data
            self.factory.clients[self.login] = self
            for login, protocol in self.factory.clients.items():
                self.transport.write("{user} joined".format(user=self.login))
        elif data == 'exit':
            self.transport.write('Bye!')
            self.transport.loseConnection()
        else:
            for login, protocol in self.factory.clients.items():
                if self.login == login:
                    # Communicate back to the user that sent the data
                    pass
                protocol.sendLine("{data}".format(data=data))
                # self.transport.write("{data}".format(data=data))


class ChatFactory(protocol.Factory):
    def __init__(self):
        self.clients = {}

    def buildProtocol(self, addr):
        return ChatProtocol(self)

print("Server started")
reactor.listenTCP(port, ChatFactory())
reactor.run()
