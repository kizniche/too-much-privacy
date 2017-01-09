#!/usr/bin/python

import pyaudio
import socket
import select
import Tkinter as tk
from Crypto.Cipher import AES
from threading import *

from gui_pkcs7 import PKCS7Encoder
from too_much_privacy import TooMuchPrivacy


class FrameOne(tk.Frame):
    def __init__(self, parent, name, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.parent.label = tk.Label(self, text="Enter your friend's IP")
        self.parent.label.pack(side=tk.LEFT)
        self.parent.entryhost = tk.Entry(self)
        self.parent.entryhost.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.parent.entryhost.insert(0, "127.0.0.1")
        self.parent.client_host = str(self.parent.entryhost.get())
        self.parent.label = tk.Label(self, text="Username")
        self.parent.label.pack(side=tk.LEFT)
        self.parent.username = tk.Entry(self)
        self.parent.username.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.parent.username.insert(0, name)
        self.parent.connectButton = tk.Button(
            self, text="Connect", command=self.parent.connect_to_server)
        self.parent.connectButton.pack(side=tk.LEFT)

        # self.parent.wm_iconbitmap("shinobi.ico")
        # self.parent.option_readfile("optionDB")


class FrameTwo(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.parent.scrollbar2 = tk.Scrollbar(self)
        self.parent.scrollbar2.pack(side=tk.RIGHT, fill=tk.Y)
        self.parent.listb1 = tk.Text(self)
        self.parent.listb1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.parent.listb1.config(yscrollcommand=self.parent.scrollbar2.set)
        self.parent.scrollbar2.config(command=self.parent.listb1.yview)


class FrameThree(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.parent.textboxsend = tk.Entry(self)
        self.parent.textboxsend.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.parent.textboxsend.bind('<Return>', self.parent.send_id)
        self.parent.textboxsend.focus_set()
        self.parent.label = tk.Label(self, text="Enter to Send")
        self.parent.label.pack(side=tk.LEFT)


class EncryptedChat(tk.Frame):
    """
    Encrypted Text and Audio Chat
    """
    def __init__(self, parent, tmp, pgp_name, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.tmp = tmp
        self.pgp_name = pgp_name
        self.pgp_name = 'User'

        self.parent.option_readfile("gui_options.db")
        self.parent.title("Too Much Privacy")
        self.parent.wm_resizable(0, 0)
        self.parent.minsize(550, 400)
        self.parent.bind_all('<Key>', self.keypress)

        self.frame_one = FrameOne(self, self.pgp_name)
        self.frame_one.pack(fill=tk.X)

        self.frame_two = FrameTwo(self)
        self.frame_two.pack(fill=tk.BOTH, expand=True)

        self.frame_three = FrameThree(self)
        self.frame_three.pack(fill=tk.X)

        # self.main = Main(self)
        # self.main.pack(side="right", fill="both", expand=True)
        # self.statusbar = Statusbar(self, ...)
        # self.toolbar = Toolbar(self, ...)
        # self.navbar = Navbar(self, ...)
        # self.statusbar.pack(side="bottom", fill="x")
        # self.toolbar.pack(side="top", fill="x")
        # self.navbar.pack(side="left", fill="y")

        self.cmd_msg, self.cmd_audio = range(2)
        self.chunk = 512
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 1100
        self.key_their = "ABCDEFGHIJKLMNOP"
        self.key_mine = "ABCDEFGHIJKLMNOP"
        self.server_host = ''
        self.client_host = ''
        self.server_port = 9009
        self.client_port = 9009
        self.s = None
        self.listb1 = None

        # Start Threading
        self.server_thread = Thread(target=self.server)
        self.server_thread.daemon = True
        self.server_thread.start()

    def run(self):
        pass

    def decrypt_my_message(self, encrypted_msg):
        iv = "1234567812345678"
        key = self.key_their
        if len(key) not in (16, 24, 32):
            raise ValueError("Key must be 16, 24, or 32 bytes")
        if (len(encrypted_msg) % 16) != 0:
            raise ValueError("Message must be a multiple of 16 bytes")
        if len(iv) != 16:
            raise ValueError("IV must be 16 bytes")
        cipher = AES.new(key, AES.MODE_CBC, iv)
        plaintext = cipher.decrypt(encrypted_msg)
        return plaintext

    def server(self):
        """Server"""
        # Initialize socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.server_host, self.server_port))
        server_socket.listen(5)
        # Start receive loop
        read_list = [server_socket]
        while True:
            readable, writable, errored = select.select(read_list, [], [])
            for self.s in readable:
                if self.s is server_socket:
                    conn, addr = self.s.accept()
                    read_list.append(conn)
                    print("Connection from {addr}".format(addr=addr))
                else:
                    recv_msg = conn.recv(2024)
                    if recv_msg:
                        cmd, recv_msg = ord(recv_msg[0]), recv_msg[1:]
                        if cmd == self.cmd_msg:
                            self.listb1.insert(tk.END, self.decrypt_my_message(recv_msg.strip()) + "\n")
                            self.listb1.yview(tk.END)
                        elif cmd == self.cmd_audio:
                            # d = speex.Decoder()
                            # d.initialize(speex.SPEEX_MODEID_WB)
                            p = pyaudio.PyAudio()
                            stream = p.open(format=self.format,
                                            channels=self.channels,
                                            rate=self.rate,
                                            input=True,
                                            output=True,
                                            frames_per_buffer=self.chunk)
                            # Write the data back out to the speakers
                            stream.write(self.decrypt_my_message(recv_msg), self.chunk)
                    else:
                        self.s.close()
                        read_list.remove(self.s)

    def encrypt_my_message(self, unencrypted_msg):
        key = self.key_mine
        iv = '1234567812345678'
        aes = AES.new(key, AES.MODE_CBC, iv)
        if len(unencrypted_msg) % 16 != 0:
            unencrypted_msg += ' ' * (16 - len(unencrypted_msg) % 16)
        encrypted_msg = aes.encrypt(unencrypted_msg)
        return encrypted_msg

    def encrypt_my_audio_message(self, unencrypted_audio):
        key = self.key_mine
        iv = '1234567812345678'
        aes = AES.new(key, AES.MODE_CBC, iv)
        encoder = PKCS7Encoder()
        pad_text = encoder.encode(unencrypted_audio)
        encrypted_audio = aes.encrypt(pad_text)
        return encrypted_audio

    def connect_to_server(self,):
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.connect((self.client_host, self.client_port))
            print("Connected\n")
        except Exception as except_msg:
            print("Could not connect: {err}".format(err=except_msg))

    def client(self, cmd, msg):
        try:
            self.s.send(cmd + msg)
        except Exception as except_msg:
            print("You are not connected: {err}".format(err=except_msg))

    def send_audio(self):
        p = pyaudio.PyAudio()
        stream = p.open(format=self.format,
                        channels=self.channels,
                        rate=self.rate,
                        input=True,
                        output=True,
                        frames_per_buffer=self.chunk)
        data = stream.read(self.chunk)
        return self.encrypt_my_audio_message(data)

    #    stream.stop_stream()
    #    stream.close()
    #    p.terminate()
    
    def keypress(self, event):
        if event.keysym == 'Escape':
            self.root.destroy()
        # x = event.char
        if event.keysym == 'Control_L':
            # print("Sending Data...")
            self.client(chr(self.cmd_audio), self.send_audio())
            # print("Data Sent!")
    
    def send_id(self, foo):
        user = self.username.get()
        if user == '':
            user = 'User'
        # Get the message from the entry box
        self.client(chr(self.cmd_msg),
                    self.encrypt_my_message('{user}: {msg}'.format(
                        user=user, msg=str(self.textboxsend.get()))))
        # Insert the message
        self.listb1.insert(tk.END, '{user}: {msg}\n'.format(
            user=user, msg=self.textboxsend.get()))
        self.listb1.yview(tk.END)
        # Delete entry text after sending
        self.textboxsend.delete(0, tk.END)


if __name__ == '__main__':
    # tmp = TooMuchPrivacy()
    # pgp_name = tmp.select_keys_and_passphrase()

    tmp = None
    pgp_name = None

    try:
        root = tk.Tk()
        EncryptedChat(root, tmp, pgp_name).pack(side="top", fill="both", expand=True)
        root.mainloop()
    except KeyboardInterrupt:
        pass
