from operator import attrgetter

from kivy.app import App
from kivy.graphics import Color
from kivy.properties import StringProperty, NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget

from utils import TextBoxLabel, DoubleClickBehavior

# ============================================================================

class Friend(Widget):
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


def sort_by(sort_key, friends, reverse):
    if sort_key == 'status':
        # if sorting by status, sort by display name then by status
        friends.sort(key=attrgetter('name'), reverse=reverse)

    friends.sort(key=attrgetter(sort_key), reverse=reverse)

# ============================================================================
# Widgets
# ============================================================================

class FriendLabel(DoubleClickBehavior, TextBoxLabel):
    def __init__(self, friend, *args, **kwargs):
        self.friend = friend
        super(FriendLabel, self).__init__(*args, **kwargs)
        self.name_changed()
        self.bind(on_release=self.pushed)
        self.friend.bind(name=self.name_changed)

    def name_changed(self, *args):
        self.text = '%s\n%s' % (self.friend.name, self.friend.userid)

    def pushed(self, *args):
        friend = self.parent.friend
        if friend.status != 'online':
            return

        # click means start/switch to a conversation
        self.friend.message_count = 0
        app = App.get_running_app()
        app.root_box.menu.show_item('Chats', select='Chats')
        app.root_box.ids.screen_manager.current = 'Chats'
        app.root_box.chat_box.add_chat(friend)


class FriendRow(BoxLayout):
    def __init__(self, friend, *args, **kwargs):
        self.friend = friend
        super(FriendRow, self).__init__(*args, **kwargs)

        label = FriendLabel(friend)
        label.bind(height=self.text_height_changed)
        self.add_widget(label)

        self.friend.bind(status=self.change_status)
        self.change_status()

    def change_status(self, *args):
        # find the Color object under our status widget and change it
        for instruction in self.ids.status_widget.canvas.before.children: 
            if isinstance(instruction, Color):
                if self.friend.status == 'offline':
                    instruction.r = 1
                    instruction.g = 0
                else:
                    instruction.r = 0
                    instruction.g = 1

                instruction.b = 0

    def text_height_changed(self, instance, value):
        self.height = value + 5

    def __str__(self):
        return 'FriendRow(%s)' % self.friend.name


class FriendBox(BoxLayout):
    def __init__(self, root_box, *args, **kwargs):
        self.root_box = root_box
        super(FriendBox, self).__init__(*args, **kwargs)
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

        # find all the friends in the friend rows
        friends = [row.friend for row in self.layout.children]
        reverse = self.ids.sort_order.text == '^'
        sort_by(sort_key, friends, reverse)

        # remove old widgets, replace with new ones
        self.layout.clear_widgets()
        self.friend_rows = {}
        self.add_friends(friends)

    def change_status(self, userid, status):
        try:
            self.friend_rows[userid].friend.status = status
        except KeyError:
            # no matching userid, probably a chat room, ignore it
            pass

    def add_friend(self, friend):
        if friend.userid in self.friend_rows:
            return

        row = FriendRow(friend)
        self.friend_rows[friend.userid] = row
        self.layout.add_widget(row)

    def add_friends(self, friends):
        for friend in friends:
            self.add_friend(friend)
