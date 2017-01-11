class ChatClient(ClientXMPP):
    def __init__(self, root_box, userid, password):
        # register the callback trigger for when we receive a chat (processing
        # of chat has to happen on kivy's thread)
        self._chat_trigger = Clock.create_trigger(self._sync_receive_chat)

    def receive_chat(self, msg):
        """This call will happen on SleekXMPP's thread"""
        #print '==> rcvd:', msg
        if msg['type'] in ('chat', 'normal', ):
            self.root_box.receive_queue.put(msg)
            self._chat_trigger()

    def _sync_receive_chat(self, delta_time):
        """Should only be called by triggered event on kivy's thread to deal
        with any received messages."""
        try:
            while(True):
                # not an infinite loop, get() throws Empty
                msg = self.root_box.receive_queue.get(block=False)
                self._handle_chat_message(msg)
        except Empty:
            # nothing left to do
            pass
