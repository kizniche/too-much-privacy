import datetime
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput

from tabbox import TabBox
from utils import TextBoxLabel


# ============================================================================

class MessageTextInput(TextInput):
    """Adapted version of TextInput that handles SHIFT-ENTER and ENTER
    for multi-line input and sending a message."""
    def __init__(self, *args, **kwargs):
        self.register_event_type('on_enter')
        super(MessageTextInput, self).__init__(*args, **kwargs)

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        super(MessageTextInput, self).keyboard_on_key_down(window, keycode, 
            text, modifiers)
        if keycode[1] == 'enter' and not modifiers:
            self.dispatch('on_enter')

    def on_enter(self, *args):
        pass


class MessageBox(BoxLayout):
    def __init__(self, userid, *args, **kwargs):
        self.userid = userid
        super(MessageBox, self).__init__(*args, **kwargs)

        # create a grid for the scroll view to contain things
        self.layout = GridLayout(cols=1, padding=(10, 15), spacing=8,
            size_hint=(1, None))

        self.layout.bind(minimum_height=self.layout.setter('height'))

        self.ids.scroller.add_widget(self.layout)
        self.ids.message_input.bind(on_enter=self.send_message)

    def send_message(self, instance):
        text = self.ids.message_input.text.rstrip('\r\n')
        if text:
            app = App.get_running_app()
            app.root_box.chat_client.send_chat(self.userid, text)
            self.add_message(text)

        self.ids.message_input.text = ''

    def add_message(self, text, msg_from=None):
        if not msg_from:
            msg_from = 'me'
            from_color = 'ff0000'
        else:
            from_color = '00ffff'

        if '\n' in text:
            text = '[{time}] [color={color}]{user}:[/color]\n{text}'.format(
                time=timestamp(), color=from_color, user=msg_from, text=text)
        else:
            text = '[{time}] [color={color}]{user}: [/color]{text}'.format(
                time=timestamp(), color=from_color, user=msg_from, text=text)
        label = TextBoxLabel(text=text, font_name='courier.ttf')
        self.layout.add_widget(label)
        self.ids.scroller.scroll_y = 0

    def add_message_me(self, text):
        self.add_to_chat('[{time}] [color=00ffff]me: [/color]{text}'.format(
            time=timestamp(), text=text))

    def add_message_other(self, text):
        self.add_to_chat('[{time}] {text}'.format(
            time=timestamp(), text=text))

    def add_echo_message(self, text):
        self.add_to_chat('[{time}] [color=ff0000]{text}[/color]'.format(
            time=timestamp(), text=text))

    def add_to_chat(self, text):
        label = TextBoxLabel(text=text, font_name='courier.ttf')
        self.layout.add_widget(label)
        self.ids.scroller.scroll_y = 0


class ChatBox(TabBox):
    def __init__(self, *args, **kwargs):
        super(ChatBox, self).__init__(*args, **kwargs)
        self.chats = {}

    def add_chat(self, friend, switch_to=True):
        # if friend.userid not in self.chats:
        #     mbox = MessageBox(friend.userid)
        #     tab = self.add_tab(friend.userid, friend.name)
        #     tab.bind(on_activate=self.tab_activated)
        #     self.chats[friend.userid] = {
        #         'friend':friend,
        #         'name':friend.name,
        #         'message_box':mbox,
        #     }
        #     friend.bind(name=self.name_changed)
        #
        #     container = self.get_content_widget(friend.userid)
        #     container.add_widget(mbox)
        #
        # if switch_to:
        #     self.switch_tab(friend.userid)
        mbox = MessageBox("TMP")
        tab = self.add_tab("TMP", "nameski")
        tab.bind(on_activate=self.tab_activated)
        self.chats["TMP"] = {
            'friend': "test1",
            'name': "nameski",
            'message_box': mbox,
        }
        # friend.bind(name="name2")

        container = self.get_content_widget("TMP")
        container.add_widget(mbox)

    def remove_tab(self, userid):
        super(ChatBox, self).remove_tab(userid)

        del self.chats[userid]
        if len(self.tabs) == 0:
            app = App.get_running_app()
            app.root_box.menu_remove_chat()

    def tab_activated(self, instance, *args):
        # clear the message counter for the friend that owns this tab
        self.chats[instance.name]['friend'].message_count = 0

    def name_changed(self, instance, *args):
        tab = self.tabs[instance.userid]['tab']
        tab.ids.tab_label.text = instance.name

    def chat_received(self, friend, msg):
        # self.add_chat(friend, switch_to=False)
        # message_box = self.chats[friend.userid]['message_box']
        # message_box.add_message(msg, friend.base_name)
        message_box = self.chats["TMP"]['message_box']
        message_box.add_message(msg, friend)

    def add_message_other(self, msg):
        message_box = self.chats["TMP"]['message_box']
        message_box.add_message_other(msg)

    def echo_in_chat(self, msg):
        message_box = self.chats["TMP"]['message_box']
        message_box.add_echo_message(msg)

    def add_raw_message(self, msg):
        message_box = self.chats["TMP"]['message_box']
        message_box.add_to_chat(msg)


def timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
