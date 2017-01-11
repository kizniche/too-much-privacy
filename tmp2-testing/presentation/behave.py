class DoubleClickBehavior(ButtonBehavior):
    def on_touch_down(self, touch):
        if not touch.is_double_tap:
            return False

        super(DoubleClickBehavior, self).on_touch_down(touch)




class FriendLabel(DoubleClickBehavior, TextBoxLabel):
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
