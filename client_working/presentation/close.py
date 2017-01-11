class KivyChatApp(App):
    def build(self):
        self.root_box = RootBox()
        Window.bind(on_close=self.pushed_close)

        return self.root_box

    def pushed_close(self, *args):
        print 'Disconnecting...'
        if self.root_box.chat_client:
            self.root_box.chat_client.disconnect(wait=True)
