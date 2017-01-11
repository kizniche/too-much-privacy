import os
from itertools import cycle
from collections import OrderedDict

from kivy.lang import Builder
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner

# ============================================================================
# Utilities
# ============================================================================

def load_kv_files():
    # search through our kv directory and load all ui files
    dirname = os.path.join(os.path.dirname(__file__), 'kv')
    for root, dirs, files in os.walk(dirname):
        for filename in files:
            f, ext = os.path.splitext(filename)
            if ext != '.kv':
                continue

            full = os.path.join(root, filename)
            Builder.load_file(full)

# ============================================================================
# People Management
# ============================================================================

NAME_COLOURS = (
    '008000',  # Green
    '0000ff',  # Blue
    '8A2BE2',  # BlueViolet
    '008B8B',  # DarkCyan
    'B8860B',  # DarkGoldenRod
    '006400',  # DarkGreen
    '4B0082',  # Indigo
)

COLOUR_CYCLE = cycle(NAME_COLOURS)

class Person(object):
    def __init__(self, nick, userid, colour=None):
        self.userid = userid
        self.nick = nick
        if colour:
            self.colour = colour
        else:
            self.colour = COLOUR_CYCLE.next()


class People(object):
    def __init__(self, multiline=False):
        self.by_nick = {}
        self.by_userid = {}
        self.multiline = multiline

    def add_person(self, nick, userid, colour=None):
        if userid in self.by_userid:
            return self.by_userid[userid]

        if not nick:
            at_sign = userid.find('@')
            nick = userid[:at_sign]

        p = Person(nick, userid, colour)
        self.by_nick[p.nick] = p
        self.by_userid[userid] = p

        return p

    def message_text(self, person, text):
        feed = ''
        if self.multiline:
            feed = '\n'

        result = '[color=%s]%s: [/color]%s%s' % (
            person.colour, person.nick, feed, text)
        return result

# ============================================================================
# Behavio(u)rs
# ============================================================================

class DoubleClickBehavior(ButtonBehavior):
    def on_touch_down(self, touch):
        if not touch.is_double_tap:
            return False

        super(DoubleClickBehavior, self).on_touch_down(touch)

# ============================================================================
# Widgets
# ============================================================================

class ConfirmPopup(Popup):
    """Confirm dialog.  Must provide at least a 'title' attribute.  

    :param title: title of the dialog
    :param confirm_text: text on the "Confirm" button, defaults to "Ok"
    :param cancel_text: text on the "Cancel" button, defaults to "Cancel
    :param message: message to user, defaults to "Are you sure?"

    ConfirmPopup Events
    -------------------

    This popup declares two events: ``on_confirm`` and ``on_cancel`` for the
    respective buttons.  The default behaviour is to dismiss the popup after
    invoking any callbacks associated with these events.  Returning ``False``
    from the callback will stop the popup from dismissing.
    """
    def __init__(self, *args, **kwargs):
        confirm_text = kwargs.pop('confirm_text', 'Ok')
        cancel_text = kwargs.pop('cancel_text', 'Cancel')
        message = kwargs.pop('message', 'Are you sure?')

        self.register_event_type('on_confirm')
        self.register_event_type('on_cancel')
        super(ConfirmPopup, self).__init__(*args, **kwargs)
        self.ids.content.text = message

        self.ids.confirm_button.text = confirm_text
        self.ids.confirm_button.bind(on_release=self._confirm_pushed)

        self.ids.cancel_button.text = cancel_text
        self.ids.cancel_button.bind(on_release=self._cancel_pushed)

    def _confirm_pushed(self, *args):
        if self.dispatch('on_confirm'):
            self.dismiss()

    def _cancel_pushed(self, *args):
        if self.dispatch('on_cancel'):
            self.dismiss()

    def on_confirm(self, *args):
        return True

    def on_cancel(self, *args):
        return True


class TextBoxLabel(Label):
    """This Label class is set to work as box of text that wraps to the
    parent's width."""

    # all attributes defined in kv/utils.kv
    pass


class Menu(Spinner):
    def __init__(self, *args, **kwargs):
        super(Menu, self).__init__(*args, **kwargs)

        self.menu_items = OrderedDict()
        for value in self.values:
            self.menu_items[value] = {
                'show':True,
            }

    def show_item(self, item, select=None):
        if item not in self.values:
            self.menu_items[item]['show'] = True
            self.values = [k for k, v in self.menu_items.items() if v['show']]

        if select:
            self.text = select

    def hide_item(self, item, select=None):
        if item in self.values:
            self.menu_items[item]['show'] = False
            self.values = [k for k, v in self.menu_items.items() if v['show']]

        if select and self.text == item:
            self.text = select
