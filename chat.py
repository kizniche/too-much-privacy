#!/usr/bin/python

# gnupg commands:
#
# List secret keys: gpg2 --list-secret-keys
# List public keys: gpg2 --list-keys
#
# Export secret key: gpg2 --export-secret-keys -a "User Name" > secret.asc
# Export public key: gpg2 --export -a "User Name" > public.asc
#
# Import public key: gpg2 --import public.asc
# Import private key: gpg2 --import private.asc

import datetime
import select
import socket
import sys
import urwid
from collections import deque
from threading import Thread
import threading

from too_much_privacy import TooMuchPrivacy

NEWKEY_DIR = './gnupg-key'


class UnknownCommand(Exception):
    def __init__(self, cmd):
        Exception.__init__(self, 'Unknown command: {cmd}'.format(cmd=cmd))


class Command(object):
    """
    Base class to manage commands in commander
    similar to cmd.Cmd in standard library
    just extend with do_something  method to handle your commands
    """

    def __init__(self, soc, nick, quit_commands=['/q', '/quit', '/exit'], help_commands=['/help', '/?', '/h']):
        self._quit_cmd = quit_commands
        self._help_cmd = help_commands
        self.soc = soc
        self.nick = nick

    def __call__(self, line):
        tokens = line.split()
        cmd = tokens[0].lower()
        args = tokens[1:]

        if cmd in self._quit_cmd:
            return Commander.Exit
        elif cmd in self._help_cmd:
            return self.help(args[0] if args else None)
        elif str(cmd)[:1] == '/' and hasattr(self, 'do_' + cmd[1:]):
            return getattr(self, 'do_' + cmd[1:])(*args)
        elif str(cmd)[:1] == '/':
            raise UnknownCommand(cmd[1:])
        else:
            self.soc.send('[{nick}] {line}'.format(nick=self.nick,
                                                   line=tmp.encrypt_string(line)))
            return '[{time}] [{nick}] (*) {line}'.format(
                time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                nick=self.nick,
                line=line)

    def help(self, cmd=None):
        def std_help():
            qc = '|'.join(self._quit_cmd)
            hc = '|'.join(self._help_cmd)
            res = 'Type [{hc}] command_name to get more help about particular ' \
                  'command\n'.format(hc=hc)
            res += 'Type [{qc}] to quit program\n'.format(qc=qc)
            cl = [name[3:] for name in dir(self) if name.startswith('do_') and len(name) > 3]
            res += 'Available commands: {cmd}'.format(cmd=(' '.join(sorted(cl))))
            return res

        if not cmd:
            return std_help()
        else:
            try:
                fn = getattr(self, 'do_' + cmd)
                doc = fn.__doc__
                return doc or 'No documentation available for {cmd}'.format(cmd=cmd)
            except AttributeError:
                return std_help()


class FocusMixin(object):
    def mouse_event(self, size, event, button, x, y, focus):
        if focus and hasattr(self, '_got_focus') and self._got_focus:
            self._got_focus()
        return super(FocusMixin, self).mouse_event(size, event, button, x, y, focus)


class ListView(FocusMixin, urwid.ListBox):
    def __init__(self, model, got_focus, max_size=None):
        urwid.ListBox.__init__(self, model)
        self._got_focus = got_focus
        self.max_size = max_size
        self._lock = threading.Lock()

    def add(self, line):
        with self._lock:
            was_on_end = self.get_focus()[1] == len(self.body) - 1
            if self.max_size and len(self.body) > self.max_size:
                del self.body[0]
            self.body.append(urwid.Text(line))
            last = len(self.body) - 1
            if was_on_end:
                self.set_focus(last, 'above')


class Input(FocusMixin, urwid.Edit):
    signals = ['line_entered']

    def __init__(self, got_focus=None):
        urwid.Edit.__init__(self)
        self.history = deque(maxlen=1000)
        self._history_index = -1
        self._got_focus = got_focus

    def keypress(self, size, key):
        if key == 'enter':
            line = self.edit_text.strip()
            if line:
                urwid.emit_signal(self, 'line_entered', line)
                self.history.append(line)
            self._history_index = len(self.history)
            self.edit_text = u''
        if key == 'up':

            self._history_index -= 1
            if self._history_index < 0:
                self._history_index = 0
            else:
                self.edit_text = self.history[self._history_index]
        if key == 'down':
            self._history_index += 1
            if self._history_index >= len(self.history):
                self._history_index = len(self.history)
                self.edit_text = u''
            else:
                self.edit_text = self.history[self._history_index]
        else:
            urwid.Edit.keypress(self, size, key)


class Commander(urwid.Frame):
    """
    Simple terminal UI with command input on bottom line and display frame above
    similar to chat client etc.
    Initialize with your Command instance to execute commands
    and the start main loop Commander.loop().
    You can also asynchronously output messages with Commander.output('message')
    """

    class Exit(object):
        pass

    PALLETE = [('reversed', urwid.BLACK, urwid.LIGHT_GRAY),
               ('normal', urwid.LIGHT_GRAY, urwid.BLACK),
               ('error', urwid.LIGHT_RED, urwid.BLACK),
               ('green', urwid.DARK_GREEN, urwid.BLACK),
               ('blue', urwid.LIGHT_BLUE, urwid.BLACK),
               ('magenta', urwid.DARK_MAGENTA, urwid.BLACK), ]

    def __init__(self, title,
                 command_caption='Message: (Use [Tab] to switch to upper '
                                 'frame, scroll with arrows and Page Up/Down)',
                 cmd_cb=None, max_size=1000):
        self.header = urwid.Text(title)
        self.model = urwid.SimpleListWalker([])
        self.body = ListView(self.model, lambda: self._update_focus(False), max_size=max_size)
        self.input = Input(lambda: self._update_focus(True))
        foot = urwid.Pile([urwid.AttrMap(urwid.Text(command_caption), 'reversed'),
                           urwid.AttrMap(self.input, 'normal')])
        urwid.Frame.__init__(self,
                             urwid.AttrWrap(self.body, 'normal'),
                             urwid.AttrWrap(self.header, 'reversed'),
                             foot)
        self.set_focus_path(['footer', 1])
        self._focus = True
        urwid.connect_signal(self.input, 'line_entered', self.on_line_entered)
        self._cmd = cmd_cb
        self._output_styles = [s[0] for s in self.PALLETE]
        self.eloop = None

    def loop(self, handle_mouse=False):
        self.eloop = urwid.MainLoop(self, self.PALLETE, handle_mouse=handle_mouse)
        self._eloop_thread = threading.current_thread()
        self.eloop.run()

    def on_line_entered(self, line):
        if self._cmd:
            try:
                res = self._cmd(line)
            except Exception as e:
                self.output('Error: {err}'.format(err=e), 'error')
                return
            if res == Commander.Exit:
                raise urwid.ExitMainLoop()
            elif res:
                self.output(str(res))
        else:
            if line in ('q', 'quit', 'exit'):
                raise urwid.ExitMainLoop()
            else:
                self.output(line)

    def output(self, line, style=None):
        if style and style in self._output_styles:
            line = (style, line)
        self.body.add(line)
        # since output could be called asynchronously form other threads we need to refresh screen in these cases
        if self.eloop and self._eloop_thread != threading.current_thread():
            self.eloop.draw_screen()

    def _update_focus(self, focus):
        self._focus = focus

    def switch_focus(self):
        if self._focus:
            self.set_focus('body')
            self._focus = False
        else:
            self.set_focus_path(['footer', 1])
            self._focus = True

    def keypress(self, size, key):
        if key == 'tab':
            self.switch_focus()
        return urwid.Frame.keypress(self, size, key)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: python chat.py host/IP port')
        sys.exit()

    tmp = TooMuchPrivacy()

    tmp.select_keys_and_passphrase()

    improper_nick = True
    while improper_nick:
        nickname = raw_input("\nNickname:")
        if ' ' in nickname:
            print("Nicknames cannot contain spaces. Try again.")
        else:
            improper_nick = False

    host = sys.argv[1]
    port = int(sys.argv[2])

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)

    class TestCmd(Command):
        def __init__(self):
            Command.__init__(self, s, nickname)

        def do_echo(self, *args):
            """echos arguments"""
            return ' '.join(args)

        def do_raise(self, *args):
            """raises"""
            raise Exception('Some Error')

    c = Commander('Too Much Privacy : {nick} (*=Encrypted)'.format(nick=nickname),
                  cmd_cb=TestCmd())

    # connect to remote host
    try:
        s.connect((host, port))
    except Exception as except_msg:
        c.output('Unable to connect: {err}'.format(err=except_msg))
        sys.exit()

    # Test asynch output -  e.g. coming from different thread
    import time

    def run():
        c.output("Welcome. Type '/help' for a list of commands", 'error')
        while True:
            time.sleep(0.1)
            socket_list = [sys.stdin, s]

            # Get the list sockets which are readable
            read_sockets, write_sockets, error_sockets = select.select(socket_list, [], [])

            for sock in read_sockets:
                if sock == s:
                    # incoming message from remote server, s
                    timeout = 2
                    total_data = [];
                    data = '';
                    # beginning time
                    begin = time.time()
                    while 1:
                        # if you got some data, then break after timeout
                        if total_data and time.time() - begin > timeout:
                            break

                        # if you got no data at all, wait a little longer, twice the timeout
                        elif time.time() - begin > timeout * 2:
                            break

                        # recv something
                        try:
                            data = sock.recv(4096)
                            if data:
                                total_data.append(data)
                                # change the beginning time for measurement
                                begin = time.time()
                            else:
                                # sleep for sometime to indicate a gap
                                time.sleep(0.1)
                        except:
                            pass

                    # join all parts to make final string
                    total_data_joined = ''.join(total_data)

                    if not total_data_joined:
                        c.output('\nDisconnected from chat server')
                        sys.exit()
                    else:
                        # print data
                        if '-----BEGIN PGP MESSAGE-----' in data:
                            c.output('[{time}] {nick} (*) {data}'.format(
                                time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                nick=total_data_joined.split(' ', 1)[0],
                                data=tmp.decrypt_string(data.split(' ', 1)[1].strip('\n'))), 'green')
                        c.output('[{time}] (test) {data}'.format(
                            time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            data=total_data_joined.split(' ', 1)[1].strip('\n')))
    t = Thread(target=run)
    t.daemon = True
    t.start()

    # start main loop
    c.loop()
