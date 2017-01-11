#!/usr/bin/python

import datetime

# install_twisted_rector must be called before importing the reactor
from kivy.support import install_twisted_reactor
install_twisted_reactor()

# A simple Client that send messages to the echo server
from twisted.internet import reactor, protocol
from twisted.protocols import basic


class EchoClient(basic.LineReceiver):
    def connectionMade(self):
        self.factory.app.on_connection(self.transport)
        self.factory.app.print_message("connection made")

    def lineReceived(self, line):
        self.factory.app.print_message(line)

    def dataReceived(self, data):
        print("DATA: {}".format(data))
        self.factory.app.print_message(data)


class EchoFactory(protocol.ClientFactory):
    protocol = EchoClient

    def __init__(self, app):
        self.app = app

    def clientConnectionLost(self, conn, reason):
        self.app.print_message("connection lost")

    def clientConnectionFailed(self, conn, reason):
        self.app.print_message("connection failed")


# A simple kivy App, with a textbox to enter messages
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout


class TMPClientApp(App):
    def __init__(self):
        App.__init__(self)
        self.username = "User"
        self.host = 'fungi.kylegabriel.com'
        self.port = 8000
        self.connection = None
        self.command = None
        self.parameters = None

    def build(self):
        root = self.setup_gui()
        self.connect_to_server()
        return root

    def setup_gui(self):
        self.textbox = TextInput(size_hint_y=.1, multiline=False)
        self.textbox.bind(on_text_validate=self.send_message)
        self.label = Label(
            text='[{time}] Connecting to {host}:{port}\n'.format(
                time=self.timestamp(), host=self.host, port=self.port),
            halign='left',
            valign='bottom',
            size_hint=(None, None))
        self.label.bind(texture_size=self.label.setter('size'))
        self.layout = BoxLayout(orientation='vertical')
        self.layout.add_widget(self.label)
        self.layout.add_widget(self.textbox)
        return self.layout

    def connect_to_server(self):
        reactor.connectTCP(self.host, self.port, EchoFactory(self))

    def on_connection(self, connection):
        self.print_message("Successfully connected to {host}:{port}".format(
            host=self.host, port=self.port))
        self.connection = connection
        # Login
        self.connection.write('{user}'.format(user=self.username))

    def send_message(self, *args):
        if str(self.textbox.text)[0] == '/':
            options = str(self.textbox.text)[1:].split(' ')
            self.command = options[0]
            del options[0]
            self.parameters = options
            self.print_message("[{time}] Got a '/'. Command: '{cmd}', "
                               "Parameters: {param}".format(
                time=self.timestamp(), cmd=self.command, param=self.parameters))
        else:
            message = '{msg}'.format(msg=str(self.textbox.text))
            if message and self.connection:
                self.connection.write('{msg}'.format(msg=message))
        self.textbox.text = ""

    def print_message(self, msg):
        self.label.text += '[{time}] {msg}\n'.format(
            time=self.timestamp(), msg=msg)

    @staticmethod
    def timestamp():
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


if __name__ == '__main__':
    TMPClientApp().run()
