from operator import attrgetter

from kivy.app import App
from kivy.graphics import Color
from kivy.properties import StringProperty, NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget

from utils import TextBoxLabel, DoubleClickBehavior


# ============================================================================

class Server(Widget):
    name = StringProperty()
    status = StringProperty()
    message_count = NumericProperty(0)

    def __init__(self, name, userid, status):
        self.userid = userid
        self.status = status

        if not name:
            at_sign = userid.find('@')
            self.name = userid[:at_sign]
        else:
            self.name = name

        self.base_name = self.name
        self.bind(message_count=self.message_count_changed)

    def message_count_changed(self, *args):
        if self.message_count:
            self.name = '%s (%d)' % (self.base_name, self.message_count)
        else:
            self.name = self.base_name


def sort_by(sort_key, servers, reverse):
    if sort_key == 'status':
        # if sorting by status, sort by display name then by status
        servers.sort(key=attrgetter('name'), reverse=reverse)

    servers.sort(key=attrgetter(sort_key), reverse=reverse)

# ============================================================================
# Widgets
# ============================================================================

class ServerLabel(DoubleClickBehavior, TextBoxLabel):
    def __init__(self, server, *args, **kwargs):
        self.server = server
        super(ServerLabel, self).__init__(*args, **kwargs)
        self.name_changed()
        self.bind(on_release=self.pushed)
        self.server.bind(name=self.name_changed)

    def name_changed(self, *args):
        self.text = '%s\n%s' % (self.server.name, self.server.userid)

    def pushed(self, *args):
        server = self.parent.server
        if server.status != 'online':
            return

        # click means start/switch to a conversation
        self.server.message_count = 0
        app = App.get_running_app()
        app.root_box.menu.show_item('Chats', select='Chats')
        app.root_box.ids.screen_manager.current = 'Chats'
        app.root_box.chat_box.add_chat(server)


class FriendRow(BoxLayout):
    def __init__(self, server, *args, **kwargs):
        self.server = server
        super(FriendRow, self).__init__(*args, **kwargs)

        label = ServerLabel(server)
        label.bind(height=self.text_height_changed)
        self.add_widget(label)

        self.server.bind(status=self.change_status)
        self.change_status()

    def change_status(self, *args):
        # find the Color object under our status widget and change it
        for instruction in self.ids.status_widget.canvas.before.children: 
            if isinstance(instruction, Color):
                if self.server.status == 'offline':
                    instruction.r = 1
                    instruction.g = 0
                else:
                    instruction.r = 0
                    instruction.g = 1

                instruction.b = 0

    def text_height_changed(self, instance, value):
        self.height = value + 5

    def __str__(self):
        return 'FriendRow(%s)' % self.server.name


class ServerBox(BoxLayout):
    def __init__(self, root_box, *args, **kwargs):
        self.root_box = root_box
        super(ServerBox, self).__init__(*args, **kwargs)
        self.friend_rows = {}

        # create a grid for the scroll view to contain things
        self.layout = GridLayout(cols=1, padding=(10, 15), size_hint=(1, None))
        self.layout.bind(minimum_height=self.layout.setter('height'))
        self.ids.scroller.add_widget(self.layout)

        # listen for spinner events
        self.ids.sort_by.bind(text=self.change_sort)
        self.ids.sort_order.bind(text=self.change_sort)

    def change_sort(self, spinner, text):
        if text == 'Name':
            sort_key = 'name'
        elif text == 'Userid':
            sort_key = 'userid'
        else:
            sort_key = 'status'

        # find all the servers in the server rows
        servers = [row.server for row in self.layout.children]
        reverse = self.ids.sort_order.text == '^'
        sort_by(sort_key, servers, reverse)

        # remove old widgets, replace with new ones
        self.layout.clear_widgets()
        self.friend_rows = {}
        self.add_servers(servers)

    def change_status(self, userid, status):
        try:
            self.friend_rows[userid].server.status = status
        except KeyError:
            # no matching userid, probably a chat room, ignore it
            pass

    def add_friend(self, server):
        if server.userid in self.friend_rows:
            return

        row = FriendRow(server)
        self.friend_rows[server.userid] = row
        self.layout.add_widget(row)

    def add_servers(self, servers):
        for server in servers:
            self.add_friend(server)
