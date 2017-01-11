from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen

# ============================================================================

TAB_WIDTH = 150

class TabLabel(ButtonBehavior, Label):
    def __init__(self, *args, **kwargs):
        super(TabLabel, self).__init__(*args, **kwargs)
        self.bind(on_release=self.switch_tab)

    def switch_tab(self, *args):
        self.parent.switch_tab()


class Tab(BoxLayout):
    def __init__(self, tab_box, name, has_close):
        self.register_event_type('on_activate')
        super(Tab, self).__init__()
        self.name = name
        self.tab_box = tab_box

        if has_close:
            self.ids.tab_close.bind(on_release=self.tab_close_pushed)
        else:
            self.remove_widget(self.ids.tab_close)

    def tab_close_pushed(self, *args):
        self.tab_box.remove_tab(self.name)

    def switch_tab(self):
        self.tab_box.switch_tab(self.name)
        self.dispatch('on_activate', self)

    def on_activate(self, *args):
        pass


class TabBox(BoxLayout):
    def __init__(self, *args, **kwargs):
        super(TabBox, self).__init__(*args, **kwargs)
        self.tab_holder = GridLayout(rows=1, spacing=5, size_hint=(None, 1))

        self.tab_holder.bind(minimum_width=self.tab_holder.setter('width'))
        self.ids.tab_scroller.add_widget(self.tab_holder)
        self.tabs = {}

        self.scroll_left = None
        self.scroll_right = None

        self.bind(width=self.check_width)
        
    def add_tab(self, name, text, position=0, has_close=True):
        name = name.encode('ascii', 'ignore')
        tab = Tab(self, name, has_close)
        tab.ids.tab_label.text = text
        screen = Screen(name=name)

        self.tabs[name] = {
            'tab':tab,
            'screen':screen,
        }

        self.ids.tab_content.add_widget(screen)
        self.tab_holder.add_widget(tab, position)
        self.check_width()

        if len(self.tabs) == 1:
            self.switch_tab(name)

        return tab

    def check_width(self, *args):
        if len(self.tabs) * TAB_WIDTH > self.width:
            # we're too wide, we should have scroll buttons
            if not self.scroll_left:
                # more tabs than box width, put in the scroller buttons
                self.scroll_left = Button(text='<', width=40, height=40,
                    size_hint=(None, None), disabled=True)
                self.scroll_left.bind(on_release=self.pushed_scroll_left)
                self.ids.tab_header.add_widget(self.scroll_left, 2)

                self.scroll_right = Button(text='>', width=40, height=40,
                    size_hint=(None, None))
                self.scroll_right.bind(on_release=self.pushed_scroll_right)
                self.ids.tab_header.add_widget(self.scroll_right, 0)
        else:
            # we're not wide, remove any scroll buttons
            if self.scroll_left:
                self.ids.tab_header.remove_widget(self.scroll_left)
                self.ids.tab_header.remove_widget(self.scroll_right)
                self.scroll_left = None
                self.scroll_right = None

    def remove_tab(self, name):
        name = name.encode('ascii', 'ignore')
        if self.ids.tab_content.current == name:
            # removing the current tab
            if len(self.tabs) == 1:
                show_tab = '__empty__'
            else:
                show_tab = self.ids.tab_content.previous()
                if not show_tab or show_tab == '__empty__':
                    show_tab = self.ids.tab_content.next()

            self.switch_tab(show_tab)

        self.ids.tab_content.remove_widget(self.tabs[name]['screen'])
        self.tab_holder.remove_widget(self.tabs[name]['tab'])
        del self.tabs[name]
        self.check_width()

    def get_content_widget(self, name):
        return self.tabs[name]['screen']

    def pushed_scroll_left(self, *args):
        scroll_amount = 1.0 / float(len(self.tabs))
        value = self.ids.tab_scroller.scroll_x - scroll_amount
        if value <= 0.0:
            value = 0.0
            self.scroll_left.disabled = True

        self.ids.tab_scroller.scroll_x = value
        self.scroll_right.disabled = False

    def pushed_scroll_right(self, *args):
        scroll_amount = 1.0 / float(len(self.tabs))
        value = self.ids.tab_scroller.scroll_x + scroll_amount
        if value >= 1.0:
            value = 1.0
            self.scroll_right.disabled = True

        self.ids.tab_scroller.scroll_x = value
        self.scroll_left.disabled = False

    def switch_tab(self, name):
        name = name.encode('ascii', 'ignore')
        old = self.ids.tab_content.current
        if old in self.tabs:
            self.tabs[old]['tab'].ids.tab_label.bold = False

        if name != '__empty__':
            self.tabs[name]['tab'].ids.tab_label.bold = True

        self.ids.tab_content.current = name
