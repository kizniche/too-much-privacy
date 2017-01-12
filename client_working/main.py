
from too_much_privacy import TooMuchPrivacy
tmp = TooMuchPrivacy()
username = tmp.select_keys_and_passphrase()

import kivy
kivy.require('1.9.0')

from Queue import Queue

from kivy.app import App
from kivy.clock import Clock
from kivy.storage.jsonstore import JsonStore
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.settings import SettingsWithSidebar

from kivy.core.window import Window

from chatbox import ChatBox
from chatclient import TMPClient
from friends import FriendBox
from utils import ConfirmPopup, Menu, load_kv_files


# ============================================================================
# GUI
# ============================================================================

class RootBox(BoxLayout):
    def __init__(self, *args, **kwargs):
        super(RootBox, self).__init__(*args, **kwargs)
        self.chat_client = None
        self.receive_queue = Queue()

        # create the confirm box for quitting
        self.quit_confirm = ConfirmPopup(title='Quit?', confirm_text='Quit')
        self.quit_confirm.bind(on_confirm=self.quit_pushed)
        self.quit_confirm.bind(on_cancel=self.cancel_pushed)

        # there is some sort of instantiation order problem where you can't
        # directly refer to custom classes as children in the kv language, so
        # everywhere were we want custom classes there is a BoxLayout which we
        # will now put the custom classes inside
        self.menu = Menu()
        self.menu.hide_item('Chats')
        self.menu.bind(text=self.menu_action)
        self.ids.menu_container.add_widget(self.menu)

        self.chat_box = ChatBox()
        self.ids.chat_box_container.add_widget(self.chat_box)
        
        # don't add friend_box just yet, it has the connection status label in
        # it
        # self.friend_box = FriendBox(self)

        # store = JsonStore('storage.json')
        # try:
        #     userid = store.get('account')['userid']
        #     password = store.get('account')['password']
        #     host = store.get('server')['host']
        #     port = store.get('server')['port']
        # except KeyError as msg:
        #     print("test {}".format(msg))
        #     self.ids.connection_label.text = 'No Username Set'
        # else:
        #     # create the chat client and start processing on separate thread
        #     self.chat_client = ChatClient(self, userid, password)
        #     self.chat_client.connect((host, port))
        #     self.chat_client.process(block=False)

        self.chat_client = TMPClient(self, tmp, username)

    def quit_pushed(self, *args):
        print('Disconnecting...')
        if self.chat_client:
            self.chat_client.disconnect(wait=True)
        quit()

    def cancel_pushed(self, *args):
        # changed their mind about quitting, as our menu is not a real menu
        # but a spinner, we need to reset the display value to be our current
        # screen
        self.menu.text = self.ids.screen_manager.current

    def menu_action(self, spinner, text):
        if text == 'Quit':
            self.quit_confirm.open()
        elif text == 'Settings':
            app = App.get_running_app()
            app.open_settings()

            # settings uses a pop-up, need to set our spinner menu back to
            # wherever we were
            self.menu.text = self.ids.screen_manager.current
        elif text == 'Chats':
            # go to chat screen and clear the current tab's friend's message
            # count
            self.ids.screen_manager.current = text
            current_tab = self.chat_box.ids.tab_content.current
            try:
                self.chat_box.chats[current_tab]['friend'].message_count = 0
            except KeyError:
                # there is no current tab, do nothing
                pass
        else:
            # switch to the screen chosen by the spinner
            self.ids.screen_manager.current = text

    def menu_add_chat(self):
        self.menu.show_item('Chats')

    def menu_remove_chat(self):
        self.menu.hide_item('Chats', select='Contacts')
        self.ids.screen_manager.current = 'Contacts'


# ============================================================================
# TMP App
# ============================================================================

class TMPChatApp(App):
    def build(self):
        self.settings_cls = SettingsWithSidebar
        load_kv_files()
        self.root_box = RootBox()

        Window.bind(on_close=self.pushed_close)

        return self.root_box

    def pushed_close(self, *args):
        # can't trap the window close button, but can force the disconnect
        # when it is pushed
        print('Disconnecting...')
        if self.root_box.chat_client:
            self.root_box.chat_client.disconnect(wait=True)

    def on_resume(self, *args):
        if not hasattr(self, 'root_box'):
            return

        if self.root_box.chat_client:
            self.root_box.chat_client.reconnect()

# ============================================================================

if __name__ == '__main__':
    Clock.max_iteration = 20
    TMPChatApp().run()
