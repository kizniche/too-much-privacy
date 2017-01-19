import datetime

from Queue import Empty

from kivy.app import App
from kivy.clock import Clock
from sleekxmpp import ClientXMPP
from servers import Server

from kivy.support import install_twisted_reactor
install_twisted_reactor()

# A simple Client that send messages to the echo server
from twisted.internet import ssl, reactor, protocol
from twisted.protocols import basic


class EchoClient(basic.LineReceiver):
    def __init__(self):
        self.total_data = []
        self.stop_msg = '#####END#####'

    def connectionMade(self):
        pass
        self.factory.app.on_connection(self.transport)
        # self.factory.app.print_message("Connection made")

    def lineReceived(self, line):
        # print('Raw_LINE="{}"'.format(line))
        self.combine_data(line)

    def dataReceived(self, data):
        # print('Raw_DATA="{}"'.format(data))
        self.combine_data(data)

    def combine_data(self, data):
        self.total_data.append(data)
        if self.stop_msg in data:
            total_data_joined = ''.join(self.total_data).split(self.stop_msg)
            # print('Rec_DATA="{}"'.format(total_data_joined[0]))
            # self.factory.aplp.print_message(total_data_joined[0])
            self.factory.app.print_message(total_data_joined[0])
            self.total_data = []


class EchoFactory(protocol.ClientFactory):
    protocol = EchoClient

    def __init__(self, app):
        self.app = app

    def clientConnectionLost(self, conn, reason):
        self.app.root_box.chat_box.echo_in_chat("Connection lost")
        # self.app.print_message("[{time}] Connection lost".format(
        #     time=timestamp()))

    def clientConnectionFailed(self, conn, reason):
        self.app.root_box.chat_box.echo_in_chat("Connection failed")
        # self.app.print_message("[{time}] Connection failed".format(
        #     time=timestamp()))


class TMPClient():
    def __init__(self, root_box, tmp, username):
        self.root_box = root_box
        self.tmp = tmp
        self.username = username
        self.host = None
        self.port = None
        self.connection = None
        self.command = None
        self.parameters = None
        self.stop_msg = '#####END#####'
        self.root_box.menu.show_item('Chats', select='Chats')
        self.root_box.ids.screen_manager.current = 'Chats'
        self.root_box.chat_box.add_cmd_chat("Server Cmd")
        self.root_box.chat_box.add_cmd(
            "Welcome to\n\n"
            "_/_/_/_/_/  _/      _/  _/_/_/\n"
            "   _/      _/_/  _/_/  _/    _/\n"
            "  _/      _/  _/  _/  _/_/_/\n"
            " _/      _/      _/  _/\n"
            "_/      _/      _/  _/\n\n"
            "Too Much Privacy (seriously) version 1.0\n"
            "Copyright (C) 2017 Kyle Gabriel (kylegabriel.com)\n"
            "License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html")
        self.print_cmd("Console initiated. Type 'help' for help.")

    def command_receive(self, userid, text):
        commands = text.split(' ')
        if commands[0] == 'help' and len(commands) == 1:
            self.print_cmd("\nAvailable commands:\n"
                           "connect server port  - connect to server:port\n"
                           "help                 - Display this help")
        elif commands[0] == 'connect' and len(commands) == 3:
            self.host = commands[1]
            self.start_chat(commands[1])
            self.connect(commands[1], int(commands[2]))
        else:
            self.print_cmd('Invalid command: {text}'.format(text=text))

    def print_cmd(self, msg):
        self.root_box.chat_box.add_cmd("[{time}] {msg}".format(
            time=timestamp(), msg=msg))

    def connect(self, host, port):
        self.root_box.chat_box.echo_in_chat(
            "Connecting to {host}:{port} with SSL".format(host=host,
                                                          port=port))
        reactor.connectSSL(host, port, EchoFactory(self),
                           ssl.ClientContextFactory())
        return True

    def disconnect(self, wait):
        print("Disconnect called")

    def start_chat(self, host):
        self.root_box.menu.show_item('Chats', select='Chats')
        self.root_box.ids.screen_manager.current = 'Chats'
        self.root_box.chat_box.add_chat(host)

    def on_connection(self, connection):
        self.root_box.chat_box.echo_in_chat(
            "Successfully connected to {host}:{port}".format(host=self.host,
                                                             port=self.port))
        self.connection = connection
        # Login
        self.connection.write('{user}{stop}'.format(
            user=self.username, stop=self.stop_msg))

    def send_chat(self, user, text):
        if '\n' in text:
            message = '[color=27ae60]{user}[/color]:\n{msg}'.format(
                user=self.username, msg=text)
        else:
            message = '[color=27ae60]{user}[/color]: {msg}'.format(
                user=self.username, msg=text)
        if message and self.connection:
            encrypted_msg = self.tmp.encrypt_string(message)
            # print('PGP_DATA="{msg}"'.format(msg=encrypted_msg))
            self.connection.write('{msg}{stop}'.format(
                msg=encrypted_msg, stop=self.stop_msg))

    def print_message(self, msg):
        send_msg = msg
        if msg.startswith("-----BEGIN PGP MESSAGE-----"):
            decrypted_msg = self.tmp.decrypt_string(msg)
            if decrypted_msg != '###Passphrase unable to decrypt data###':
                send_msg = decrypted_msg
        self.root_box.chat_box.add_message_other(send_msg)


def timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# class ChatClient(ClientXMPP):
#     def __init__(self, root_box, userid, password):
#         self.userid = userid
#         self.root_box = root_box
#         at_sign = userid.find('@')
#         self.nick = userid[:at_sign]
#         super(ChatClient, self).__init__(userid, password)
#         self.message_count = 0
#
#         # register some XMPP plug ins
#         self.register_plugin('xep_0030')  # service discovery
#         self.register_plugin('xep_0199')  # ping
#
#         self.add_event_handler('session_start', self.start)
#         self.add_event_handler('no_auth', self.auth_failed)
#
#         self.add_event_handler('got_online', self.status_change)
#         self.add_event_handler('got_offline', self.status_change)
#         self.add_event_handler('changed_status', self.status_change)
#         self.add_event_handler('message', self.receive_chat)
#
#         # register the callback trigger for when we receive a chat (processing
#         # of chat has to happen on kivy's thread)
#         self._chat_trigger = Clock.create_trigger(self._sync_receive_chat)
#
#     def start(self, event):
#         # retrieve our buddies and populate
#         iq = self.get_roster()
#         servers = []
#         for key, value in iq['roster']['items'].items():
#             servers.append(Server(value['name'], key.bare, 'offline'))
#
#         if servers:
#             # we're connected and we have servers, get rid of the connection
#             # label and insert the actual server box
#             self.root_box.ids.server_list_container.clear_widgets()
#             self.root_box.ids.server_list_container.add_widget(
#                 self.root_box.server_list)
#             self.root_box.server_list.add_servers(servers)
#         else:
#             self.root_box.ids.connection_label.text = ('Connected\n'
#                 'You have no servers')
#
#         # tell the world we're here, this will also trigger getting our
#         # server's statuses back
#         self.send_presence()
#
#     def auth_failed(self, event):
#         self.root_box.ids.connection_label.text = ('Connection Failed\n'
#             'Check your settings')
#
#     def status_change(self, event):
#         status = event.get_type()
#         who = event.get_from().bare
#         if status == 'available':
#             self.root_box.server_list.change_status(who, 'online')
#         elif status == 'unavailable':
#             self.root_box.server_list.change_status(who, 'offline')
#         else:
#             print '=> ignoring presence type of ', status
#
#     def send_chat(self, msg_to, msg, mtype='chat'):
#         msg = self.make_message(mto=msg_to, mbody=msg, mtype=mtype)
#         self.message_count += 1
#         msg['id'] = 'spakr%d' % self.message_count
#         msg.send()
#
#     def receive_chat(self, msg):
#         """This call will happen on SleekXMPP's thread"""
#         #print '==> rcvd:', msg
#         if msg['type'] in ('chat', 'normal', ):
#             self.root_box.receive_queue.put(msg)
#             self._chat_trigger()
#
#     def _sync_receive_chat(self, delta_time):
#         """Should only be called by triggered event on kivy's thread to deal
#         with any received messages."""
#         try:
#             while(True):
#                 # not an infinite loop, get() throws Empty
#                 msg = self.root_box.receive_queue.get(block=False)
#                 self._handle_chat_message(msg)
#         except Empty:
#             # nothing left to do
#             pass
#
#     def _handle_chat_message(self, msg):
#         userid = msg.get_from().bare
#         try:
#             server = self.root_box.server_list.friend_rows[userid].server
#             self.root_box.chat_box.chat_received(server, msg['body'])
#             self.root_box.menu.show_item('Chats')
#
#             # only increment the chat counter if the tab for this chat
#             # isn't showing
#             current_tab = self.root_box.chat_box.ids.tab_content.current
#             if self.root_box.ids.screen_manager.current != 'Chats' \
#                     or current_tab != server.userid:
#                 server.message_count += 1
#         except KeyError:
#             print '=> ignoring message from non-server ', userid
