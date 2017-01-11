#!/usr/bin/python

# Requirements
# sudo apt-get install portaudio19-dev python-dev python-tk
# sudo pip install pyaudio pycrypto

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
        self.label = tk.Label(self, text="Enter your friend's IP")
        self.label.pack(side=tk.LEFT)
        self.entryhost = tk.Entry(self)
        self.entryhost.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.entryhost.insert(0, "127.0.0.1")
        self.label = tk.Label(self, text="Username")
        self.label.pack(side=tk.LEFT)
        self.username = tk.Entry(self)
        self.username.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.username.insert(0, name)
        self.connectButton = tk.Button(
            self, text="Connect", command=self.parent.connect_to_server)
        self.connectButton.pack(side=tk.LEFT)

        # self.wm_iconbitmap("shinobi.ico")
        # self.option_readfile("optionDB")


class FrameTwo(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.scrollbar2 = tk.Scrollbar(self)
        self.scrollbar2.pack(side=tk.RIGHT, fill=tk.Y)
        self.listb1 = tk.Text(self)
        self.listb1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.listb1.config(yscrollcommand=self.scrollbar2.set)
        self.scrollbar2.config(command=self.listb1.yview)


class FrameThree(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.textboxsend = tk.Entry(self)
        self.textboxsend.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.textboxsend.bind('<Return>', self.parent.send_id)
        self.textboxsend.focus_set()
        self.label = tk.Label(self, text="Enter to Send")
        self.label.pack(side=tk.LEFT)


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

        # Draw GUI
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

        # Variables
        self.cmd_msg, self.cmd_audio = range(2)
        self.chunk = 512
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 1100
        self.key_their = "ABCDEFGHIJKLMNOP"
        self.key_mine = "ABCDEFGHIJKLMNOP"
        self.server_host = '127.0.0.1'
        self.client_host = ''
        self.server_port = 9009
        self.client_port = 9009
        self.s_server = None
        self.s_client = None
        self.listb1 = None

        # Start server thread
        self.server_thread = Thread(target=self.server)
        self.server_thread.daemon = True
        self.server_thread.start()

    def client(self, cmd, msg):
        try:
            self.s_client.send(cmd + msg)
        except Exception as except_msg:
            self.frame_one.connectButton.config(text="Connect")
            print("You are not connected: {err}".format(err=except_msg))

    def server(self):
        """Server"""
        # Initialize socket
        self.s_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s_client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s_client.bind((self.server_host, self.server_port))
        self.s_client.listen(5)
        self.frame_two.listb1.insert(
            tk.END,
            "Server Started at {ip}:{port}\n".format(ip=self.server_host,
                                                     port=self.server_port))
        print("Server Started at {ip}:{port}".format(ip=self.server_host,
                                                     port=self.server_port))

        # Start receive loop
        read_list = [server_socket]
        while True:
            readable, writable, errored = select.select(read_list, [], [])
            for self.s_server in readable:
                if self.s_server is server_socket:
                    conn, addr = self.s_server.accept()
                    read_list.append(conn)
                    self.frame_two.listb1.insert(
                        tk.END,
                        "Connection from {:s}:{:d}\n".format(*addr))
                    print("Connection from {addr}".format(addr=addr))
                else:
                    recv_msg = conn.recv(2024)
                    if recv_msg:
                        cmd, recv_msg = ord(recv_msg[0]), recv_msg[1:]
                        if cmd == self.cmd_msg:
                            recv_pgp_msg = '{pgp_msg}\n'.format(pgp_msg=self.decrypt_my_message(recv_msg.strip()))
                            decrypted_pgp_msg = self.tmp.decrypt_string(recv_pgp_msg)
                            self.frame_two.listb1.insert(
                                tk.END,
                                '[RECV] {msg}'.format(msg=decrypted_pgp_msg))
                            self.frame_two.listb1.yview(tk.END)
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
                        self.frame_two.listb1.insert(
                            tk.END,
                            "Server Disconnected\n")
                        self.s_server.close()
                        read_list.remove(self.s_server)

    def decrypt_my_message(self, encrypted_msg):
        iv = "1234567812345678"
        if len(self.key_their) not in (16, 24, 32):
            raise ValueError("Key must be 16, 24, or 32 bytes")
        if (len(encrypted_msg) % 16) != 0:
            raise ValueError("Message must be a multiple of 16 bytes")
        if len(iv) != 16:
            raise ValueError("IV must be 16 bytes")
        cipher = AES.new(self.key_their, AES.MODE_CBC, iv)
        plaintext = cipher.decrypt(encrypted_msg)
        return plaintext

    def encrypt_my_message(self, unencrypted_msg):
        iv = '1234567812345678'
        aes = AES.new(self.key_mine, AES.MODE_CBC, iv)
        if len(unencrypted_msg) % 16 != 0:
            unencrypted_msg += ' ' * (16 - len(unencrypted_msg) % 16)
        encrypted_msg = aes.encrypt(unencrypted_msg)
        return encrypted_msg

    def encrypt_my_audio_message(self, unencrypted_audio):
        iv = '1234567812345678'
        aes = AES.new(self.key_mine, AES.MODE_CBC, iv)
        encoder = PKCS7Encoder()
        pad_text = encoder.encode(unencrypted_audio)
        encrypted_audio = aes.encrypt(pad_text)
        return encrypted_audio

    def connect_to_server(self):
        self.client_host = str(self.frame_one.entryhost.get())
        try:
            self.s_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s_client.connect((self.client_host, self.client_port))
            self.frame_one.connectButton.config(text="Disconnect")
            self.frame_two.listb1.insert(
                tk.END,
                "Connected to {ip}:{port}\n".format(ip=self.client_host,
                                                    port=self.client_port))
            print("Connected to {ip}:{port}\n".format(ip=self.client_host,
                                                      port=self.client_port))
        except Exception as except_msg:
            print("Could not connect to {ip}:{port}: {err}".format(
                ip=self.client_host, port=self.client_port, err=except_msg))

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
            self.parent.destroy()
        # x = event.char
        if event.keysym == 'Control_L':
            # print("Sending Data...")
            self.client(chr(self.cmd_audio), self.send_audio())
            # print("Data Sent!")

    def send_id(self, foo):
        user = self.frame_one.username.get()
        if user == '':
            user = 'User'

        # Get the message from the entry box
        message = '[SEND] {user}: {msg}'.format(
            user=user, msg=str(self.frame_three.textboxsend.get()))

        # Double Encrypt It!
        pgp_message = self.tmp.encrypt_string(message)
        encrypted_pgp_message = self.encrypt_my_message(pgp_message)

        # Send encrypted PGP message
        if self.client(chr(self.cmd_msg), encrypted_pgp_message):
            print("Message sent\n")
        else:
            self.frame_two.listb1.insert(tk.END, "Message was not sent\n")

        # Debug messages
        print("PGP Message:\n{pgp_msg}\n".format(pgp_msg=pgp_message))

        # Insert the message into the client chat window
        self.frame_two.listb1.insert(tk.END, '[SEND] {user}: {msg}\n'.format(
            user=user, msg=self.frame_three.textboxsend.get()))
        self.frame_two.listb1.yview(tk.END)

        # Delete entry text after sending
        self.frame_three.textboxsend.delete(0, tk.END)


if __name__ == '__main__':
    tmp = TooMuchPrivacy()
    pgp_name = tmp.select_keys_and_passphrase()

    try:
        root = tk.Tk()
        EncryptedChat(root, tmp, pgp_name).pack(side="top", fill="both", expand=True)
        root.mainloop()
    except KeyboardInterrupt:
        pass
