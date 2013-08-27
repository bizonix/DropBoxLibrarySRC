#Embedded file name: ui/cocoa/dropbox_menu.py
from AppKit import NSMenu, NSMenuItem
from dropbox.bubble_context import BubbleContext
from dropbox.gui import event_handler
from dropbox.trace import TRACE
import objc

class DropboxNSMenuItem(NSMenuItem):
    pass


class DropboxNSMenu(NSMenu):

    @classmethod
    def menuWithDropboxMenuDescriptor_(klass, descriptor):
        return klass.alloc().init().refreshDropboxMenu_(descriptor)

    def refreshDropboxMenu_(self, items):
        try:
            self.removeAllItems()
        except:
            for i in reversed(xrange(self.numberOfItems())):
                self.removeItemAtIndex_(i)

        for text, func in items:
            if text is None:
                menuitem = NSMenuItem.separatorItem()
            elif type(func) in (list, tuple):
                text = unicode(text)
                menuitem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(text, None, '')
                submenu = DropboxNSMenu.menuWithDropboxMenuDescriptor_(func)
                menuitem.setSubmenu_(submenu)
            else:
                text = unicode(text)
                menuitem = DropboxNSMenuItem.alloc().initWithTitle_action_keyEquivalent_(text, None, '')
                if hasattr(func, '__call__'):
                    menuitem.dropboxFunc = func
                    menuitem.setTarget_(self)
                    menuitem.setAction_('menuAction:')
                else:
                    menuitem.setEnabled_(False)
            self.addItem_(menuitem)

        return self

    @objc.typedSelector('v@:@')
    @event_handler
    def menuAction_(self, menu_item):
        TRACE('menuAction: %s' % menu_item.title())
        try:
            menu_item.dropboxFunc()
        except AttributeError:
            pass
