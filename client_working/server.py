#!/usr/bin/python

import datetime
import errno
import sys

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
        print("[{time}] Connection".format(time=timestamp()))
        # self.transport.write('Register your login > ')

    def connectionLost(self, reason):
        print("[{time}] {user} Disconnected".format(time=timestamp(),
                                                    user=self.login))
        self.factory.clients.pop(self.login)
        for login, protocol in self.factory.clients.items():
            protocol.sendLine(
                "[color=f1c40f]{user} quit[/color]{stop}".format(
                    user=self.login, stop=self.stop_str))

    def dataReceived(self, data):
        # print('[{time}] Raw_DATA="{data}"'.format(
        #     time=timestamp(), data=data))
        self.combine_data(data)

    def lineReceived(self, line):
        # print('[{time}] Raw_LINE="{line}"'.format(
        #     time=timestamp(), line=line))
        self.combine_data(line)

    def combine_data(self, data):
        self.total_data.append(data)
        if self.stop_str in data:
            total_data_joined = ''.join(self.total_data).split(self.stop_str)
            print('[{time}] Rec_DATA="{data}"'.format(
                time=timestamp(), data=total_data_joined[0]))
            self.received_data(total_data_joined[0])
            self.total_data = []

    def received_data(self, data):
        if not self.login:
            self.login = data
            print("[{time}] [{user}] joined".format(time=timestamp(),
                                                  user=self.login))
            self.factory.clients[self.login] = self
            for login, protocol in self.factory.clients.items():
                protocol.sendLine(
                    "[color=f1c40f]{user} joined[/color]{stop}".format(
                        user=self.login, stop=self.stop_str))
        elif data == 'exit':
            self.transport.write('Bye!')
            self.transport.loseConnection()
        else:
            for login, protocol in self.factory.clients.items():
                if self.login == login:
                    # print("Self: MSG NOT Sent to {}/{}".format(login,
                    #                                            self.login))
                    # Communicate back to the user that sent the data
                    # protocol.sendLine("Data successfully reached server for "
                    #                   "distribution.".format(data=data))
                    pass
                else:
                    # print("MSG Sent to {}/{}".format(login, self.login))
                    protocol.sendLine("{data}{stop}".format(data=data,
                                                            stop=self.stop_str))
                    # self.transport.write("{data}#####END#####".format(data=data))


class ChatFactory(protocol.Factory):
    def __init__(self):
        self.clients = {}

    def buildProtocol(self, addr):
        return ChatProtocol(self)


def timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


if __name__ == '__main__':
    print("[{time}] Server started".format(time=timestamp()))
    reactor.listenTCP(port, ChatFactory())
    reactor.run()
