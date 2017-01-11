#!/usr/bin/python

import datetime

# install_twisted_rector must be called before importing the reactor
from kivy.support import install_twisted_reactor
install_twisted_reactor()

# A simple Client that send messages to the echo server
from twisted.internet import reactor, protocol
from twisted.protocols import basic


class EchoClient(basic.LineReceiver):
    def __init__(self):
        self.total_data = []
        self.stop_str = '#####END#####'

    def connectionMade(self):
        self.factory.app.on_connection(self.transport)
        self.factory.app.print_message("Connection made")

    def lineReceived(self, line):
        print('Raw_LINE="{}"'.format(line))
        self.combine_data(line)

    def dataReceived(self, data):
        print('Raw_DATA="{}"'.format(data))
        self.combine_data(data)

    def combine_data(self, data):
        self.total_data.append(data)
        if self.stop_str in data:
            total_data_joined = ''.join(self.total_data).split(self.stop_str)
            print('Rec_DATA="{}"'.format(total_data_joined[0]))
            self.factory.app.print_message(total_data_joined[0])
            self.total_data = []


class EchoFactory(protocol.ClientFactory):
    protocol = EchoClient

    def __init__(self, app):
        self.app = app

    def clientConnectionLost(self, conn, reason):
        self.app.print_message("[{time}] Connection lost".format(
            time=timestamp()))

    def clientConnectionFailed(self, conn, reason):
        self.app.print_message("[{time}] Connection failed".format(
            time=timestamp()))


from kivy.app import App
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout

from too_much_privacy import TooMuchPrivacy


class TMPClientApp(App):
    def __init__(self):
        App.__init__(self)
        self.tmp = TooMuchPrivacy()
        self.username = self.tmp.select_keys_and_passphrase()
        self.host = 'fungi.kylegabriel.com'
        self.port = 8000
        self.connection = None
        self.command = None
        self.parameters = None

    def build(self):
        root = self.setup_gui()
        self.connect_to_server()
        return root

    def set_focus(self, dt):
        self.textbox.focus = True

    def setup_gui(self):
        self.textbox = TextInput(size_hint_y=.1,
                                 multiline=False)
        self.textbox.bind(on_text_validate=self.send_message)
        Clock.schedule_once(self.set_focus, 0)
        self.label = Label(
            text='[{time}] Connecting to {host}:{port}\n'.format(
                time=timestamp(), host=self.host, port=self.port),
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
        self.connection.write('{user}#####END#####'.format(
            user=self.username))

    def send_message(self, *args):
        if len(str(self.textbox.text)) > 0 and str(self.textbox.text)[0] == '/':
            options = str(self.textbox.text)[1:].split(' ')
            self.command = options[0]
            del options[0]
            self.parameters = options
            self.print_message("[{time}] Got a '/'. Command: '{cmd}', "
                               "Parameters: {param}".format(
                                    time=self.timestamp(),
                                    cmd=self.command,
                                    param=self.parameters))
        else:
            message = '[{user}] {msg}'.format(user=self.username,
                                              msg=str(self.textbox.text))
            if message and self.connection:
                encrypted_msg = self.tmp.encrypt_string(message)
                print('SENT_DATA="{msg}"'.format(msg=encrypted_msg))
                self.label.text += '[{time}] {msg}\n'.format(
                    time=timestamp(), user=self.username, msg=message)
                self.connection.write('{msg}#####END#####'.format(
                    msg=encrypted_msg))
        self.textbox.text = ""
        Clock.schedule_once(self.set_focus, 0)

    def print_message(self, msg):
        send_msg = msg
        if msg.startswith("-----BEGIN PGP MESSAGE-----"):
            decrypted_msg = self.tmp.decrypt_string(msg)
            if decrypted_msg != '###Passphrase unable to decrypt data###':
                send_msg = decrypted_msg
        self.label.text += '[{time}] {msg}\n'.format(
            time=timestamp(), msg=send_msg)


def timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


if __name__ == '__main__':
    TMPClientApp().run()
