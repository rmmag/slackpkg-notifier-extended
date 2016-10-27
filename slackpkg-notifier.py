#!/usr/bin/env python

""" slackpkg-notifier - update notification icon for slackware gnu/linux

This small and simple application aims to notificate the user when updates
happens on slackware's mirrors he's using with slackpkg.

"""

#   This code is strongly based upon wicd tray icon client so im keeping the
#   copyright notice and adding the note for my modifications.
#   I am not a python programmer. So don't blame me for my crap identation or
#   code here.
#
#
#
#   Big modification and extension by:
#   Copyright (c) - rmmag
#
#
#   Huge cut in code and modifications by:
#   Copyright (C) 2009 - Henrique Grolli Bassotto
#
#   Original wicd tray source coded by:
#   Copyright (C) 2007 - 2008 Adam Blackburn
#   Copyright (C) 2007 - 2008 Dan O'Reilly
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License Version 2 as
#   published by the Free Software Foundation.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import sys
import gtk
import gobject
import getopt
import os
import time
import re
from threading import Thread
import platform

# Internal specific imports
import wpath

ICON_AVAIL = True

gtk.gdk.threads_init()

if __name__ == '__main__':
    wpath.chdir(__file__)

'''
Function used to print text inside the thread. (this kludge fix a anoying bug
with locks in gobject, or something like that).
'''
def printInThread (texto):
    print texto

checker = None
check_u = -1
disconnect = -1
t = 3599

'''
Class that triggers the periodic check for updates.
ps. I should use different files for different classes.
'''
class PeriodicChecker(Thread):
    def __init__(self,tray):
        Thread.__init__(self)
        self.tray = tray
    def run(self):
        self.tray.check()
        while 1:
            time.sleep(wpath.checker_time * t)
            gobject.idle_add(printInThread, "Starting scheduled checking.")
            self.tray.check()

'''
The big baby.
'''
class TrayIcon:
    """ Base Tray Icon class.
    
    Base Class for implementing a tray icon to display network status.
    
    """
    def __init__(self, use_tray):
        self.tr = self.StatusTrayIconGUI(use_tray)
        
    class TrayIconGUI:
        """ Base Tray Icon UI class.
        
        Implements methods and variables used by StatusIcon
        tray icons.

        """
        
        class Checker(Thread):
            def __init__(self,tray):
                Thread.__init__(self)
                self.tray = tray
                
            def run(self):
                # Lets determine the slackpkg results
                global check_u
                no_permission = "\nOnly root can install, upgrade, or remove packages.\nPlease log in as root or contact your system administrator.\n\n\n";
                #no_answer = "\n";
                #have_updates = "\nNews on ChangeLog.txt\n\n";
		locked = "AnotherinstanceofslackpkgisrunningIfthisisnotcorrectyoucanremovevarlockslackpkgfilesandrunslackpkgagainlh"
                no_updates_plus = "SearchingforupdateslNonewsisgoodnewslhlh"
                no_updates = "Nonewsisgoodnewslh"
                gobject.idle_add(printInThread, "Checking...")
                # You must have slackpkg 2.71 or above
                # Thanks PiterPunk to add the check function :*
                check_result = os.popen("sudo /usr/sbin/slackpkg -checkgpg=off check-updates").read()
                check_result = re.sub('[^a-zA-Z]', '', check_result) #re.sub(r'[^a-zA-Z\.\s]+','',res).strip()
                check_u = check_result.find('NewsonChangeLogtxt')
                disconnect = check_result.find('WARNINGOneormoreerror')
                if check_u >= 0:
                    t = 3599
                    self.tray.need_update()
                    gobject.idle_add(printInThread, "Done. We got updates.")
                elif check_result == no_updates or check_result == no_updates_plus:
                    t = 3599
                    self.tray.no_update()
                    gobject.idle_add(printInThread, "Done. No updates.")
                elif check_result == no_permission:
                    self.tray.no_update()
                    gobject.idle_add(printInThread, "You don't have permission to run slackpkg =(")
                elif disconnect >= 0:
                    t = 300
                    self.tray.no_connected()
                    gobject.idle_add(printInThread, "Something wrong when checking for updates. No Internet connection or slackpkg servers not response.")
                elif check_result == locked:
                    self.tray.no_update()
                    gobject.idle_add(printInThread, "Another instance of slackpkg is running.")
                else:
                    self.tray.no_update()
                    gobject.idle_add(printInThread, "Unexpected answer from slackpkg: " + check_result)
        
        def __init__(self, use_tray):
            menu = """
                    <ui>
                    <menubar name="Menubar">
                    <menu action="Menu">
                    <separator/>
                    <menuitem action="About"/>
                    <menuitem action="Mark"/>
                    <menuitem action="Update"/>
                    <menuitem action="Hide"/>
                    <menuitem action="Quit"/>
                    </menu>
                    </menubar>
                    </ui>
            """
            actions = [
                    ('Menu',  None, 'Menu'),
                    ('About', gtk.STOCK_ABOUT, '_About...', None,
                     'About slackpkg-notifier', self.on_about),
		    ('Mark', gtk.STOCK_CLEAR, '_Mark PKG\'s as Non-Repo', None, 'NonRepo',
		     self.on_mark_nonrepo),
		    ('Update',gtk.STOCK_GO_DOWN,'_Check updates',None,'Check',
                     self.on_check),
		    ('Hide',gtk.STOCK_CANCEL,'_Hide icon',None,'Hide slackpkg-notifier',
                     self.on_hide),
                    ('Quit',gtk.STOCK_QUIT,'_Quit',None,'Quit slackpkg-notifier',
                     self.on_quit),
                    ]
            actg = gtk.ActionGroup('Actions')
            actg.add_actions(actions)
            self.manager = gtk.UIManager()
            self.manager.insert_action_group(actg, 0)
            self.manager.add_ui_from_string(menu)
            self.menu = (self.manager.get_widget('/Menubar/Menu/About').props.parent)
            self.gui_win = None
            self.current_icon_path = None
            self.use_tray = use_tray

        def get_repo(self):


            if not os.path.isdir('repo/'):
                os.makedirs('repo/')

            if platform.architecture()[0] == '32bit':
                arch = 'x86'
            else:
                arch = 'x86_64'

            slackrepo = None
            f = open('/etc/slackpkg/mirrors', 'r')
            for line in f:
                x = line.find('#')
                if x == -1:
                    slackrepo = line[:-2]
            f.close()

            gobject.idle_add(printInThread, 'Download pkg')
            os.popen('wget -q '+slackrepo+'/PACKAGES.TXT -O repo/slackware.txt')
            os.popen('wget -q ' + slackrepo + '/extra/PACKAGES.TXT -O repo/slackware_extra.txt')
            os.popen('wget -q ' + slackrepo + '/pasture/PACKAGES.TXT -O repo/slackware_pasture.txt')
            os.popen('wget -q ' + slackrepo + '/patches/PACKAGES.TXT -O repo/slackware_patches.txt')
            os.popen('wget -q ' + slackrepo + '/testing/PACKAGES.TXT -O repo/slackware_testing.txt')
            os.popen('wget -q http://bear.alienbase.nl/mirrors/people/alien/sbrepos/'+platform.dist()[1]+'/'+arch+'/PACKAGES.TXT -O repo/alien.txt')
            #    os.popen('wget -q http://www.slackware.com/~alien/slackbuilds/PACKAGES.TXT -O repo/slackbuild_alien.txt') # non-official repo
            os.popen('wget -q http://bear.alienbase.nl/mirrors/people/alien/restricted_sbrepos/'+platform.dist()[1]+'/'+arch+'/PACKAGES.TXT -O repo/alien_restricted.txt')
            os.popen('wget -q http://repository.slacky.eu/slackware-'+platform.dist()[1]+'/PACKAGES.TXT -O repo/slacky.txt')
            os.popen('wget -q http://slakfinder.org/slackpkg+/PACKAGES.TXT -O repo/slackpkg_plus.txt')

        def search_pkg_type(self, dane):
            installed_pkg = os.popen('ls /var/log/packages').read().split()
            if len(installed_pkg) == 0:
                gobject.idle_add(printInThread, 'PACKAGES LIST NOT FOUND in /var/log/packages')
                self.no_update()

            pkg_list = []
            for pkg in installed_pkg:
                x = pkg.find(dane)
                if x >= 0:
                    pkg_list.append(pkg)
            return pkg_list

        def cnv_repo_to_list(self, repo):
            aln_pkg = []
            f = open('repo/'+repo, 'r')
            for line in f:
                x = line.find('PACKAGE NAME:')
                if x >= 0:
                    aln_pkg.append(line[15:-5])
            f.close()
            return aln_pkg

        def to_update(self):
            self.get_repo()
            l1 = self.search_pkg_type('')
            l2 = self.search_pkg_type('alien')
            l3 = self.search_pkg_type('SBo')

            my_slackware_list = list(set(l1) - set(l2))
            my_slackware_list = sorted(list(set(my_slackware_list) - set(l3)))

            to_upgrade = list(set(my_slackware_list) - set(self.cnv_repo_to_list('slackware.txt')))
            to_upgrade = list(set(to_upgrade) - set(self.cnv_repo_to_list('slackware_extra.txt')))
            to_upgrade = list(set(to_upgrade) - set(self.cnv_repo_to_list('slackware_pasture.txt')))
            to_upgrade = list(set(to_upgrade) - set(self.cnv_repo_to_list('slackware_patches.txt')))
            to_upgrade = list(set(to_upgrade) - set(self.cnv_repo_to_list('slackware_testing.txt')))
            to_upgrade = list(set(to_upgrade) - set(self.cnv_repo_to_list('slacky.txt')))
            to_upgrade = list(set(to_upgrade) - set(self.cnv_repo_to_list('slackpkg_plus.txt')))
            # to_upgrade = list(set(to_upgrade) - set(self.cnv_repo_to_list('slackbuild_alien.txt'))) # non-official repo

            to_upgrade_alien = list(set(l2) - set(self.cnv_repo_to_list('alien.txt')))
            to_upgrade_alien = list(set(to_upgrade_alien) - set(self.cnv_repo_to_list('alien_restricted.txt')))
            # to_upgrade_alien = list(set(to_upgrade_alien) - set(self.cnv_repo_to_list('slackbuild_alien.txt'))) # non-official repo

            out = to_upgrade + to_upgrade_alien
            if os.path.isfile('repo/non_repo_pkg.txt') and len('repo/non_repo_pkg.txt') > 0:
                f = open('repo/non_repo_pkg.txt', 'r')
                nonrepo_pkg = f.read().splitlines()
                f.close()
                out = list(set(out) - set(nonrepo_pkg))
            return out

        def mark_nonrepo(self):
            nonrepo_pkg = []
            if os.path.isfile('repo/non_repo_pkg.txt') and len('repo/non_repo_pkg.txt') > 0:
                f = open('repo/non_repo_pkg.txt', 'r')
                nonrepo_pkg = f.read().splitlines()
                f.close()

            gobject.idle_add(printInThread, 'Start marking ...')

            list_pkg = self.to_update()
            list_pkg = list_pkg + nonrepo_pkg
            if (list_pkg != []):
                f = open('repo/non_repo_pkg.txt', 'w+')
                f.write("\n".join(list_pkg))
                f.close()
                gobject.idle_add(printInThread, 'Unidentified packages marked as NonRepo')
                str = '\n'.join(list_pkg)
                self.marked_info(str+'\n\nUpdates for this packages will not be checking anymore.')
            else:
                self.marked_info('\"Non-Repo\" packages not found in your system.')
                gobject.idle_add(printInThread, 'Marking packages not needed')

        def need_update(self):
	        #if self.set_visible(1) == False:
	    self.set_visible(True)
            self.current_icon_path = wpath.images
            os.popen("sudo /usr/sbin/slackpkg update")
            #self.set_blinking(True)
            if (self.to_update() != []):
                self.set_tooltip("Updating available...")
                gtk.StatusIcon.set_from_file(self, wpath.images + "update.png")
            else:
                check_u = -1

        def no_update(self):
            self.current_icon_path = wpath.images
            gtk.StatusIcon.set_from_file(self, wpath.images + "icon.png")
            self.set_blinking(False)
            self.set_tooltip("No update.")
        
        def no_connected(self):
            self.current_icon_path = wpath.images
            gtk.StatusIcon.set_from_file(self, wpath.images + "disconnected.png")
            self.set_blinking(True)
            self.set_tooltip("Something wrong when checking for updates. No Internet connection or slackpkg servers not response.")

        def on_activate(self, data=None):
            if (check_u >= 0):
                width = gtk.gdk.screen_width()/15
                height = gtk.gdk.screen_height()/30
                os.popen("xterm -T \"UPGRADING PACKAGES ...\" -fa 'Monospace' -fs 10 -geometry "+str(width)+"x"+str(height)+" -e sudo /usr/sbin/slackpkg upgrade-all")
                os.popen("xterm -T \"INSTALLING NEW ...\" -fa 'Monospace' -fs 10 -geometry "+str(width)+"x"+str(height)+" -e sudo /usr/sbin/slackpkg install-new")
                #self.set_visible(False)
                gtk.StatusIcon.set_from_file(self, wpath.images + "icon.png")
                #self.check()
            
        def check(self):
            global checker
            self.set_blinking(False)
            self.current_icon_path = wpath.images
            gtk.StatusIcon.set_from_file(self, wpath.images + "checking.png")
            self.set_tooltip("Checking for updates.")
            checker = self.Checker(self)
            checker.start()

        def on_mark_nonrepo(self, data=None):
            self.mark_nonrepo()

        def on_check(self, widget=None):
	    self.check()

        def on_quit(self, widget=None):
            """ Closes the tray icon. """
            import signal
            os.kill(os.getpid(), signal.SIGTERM) 
            #sys.exit(0)
	
	def on_hide(self, widget=None):
            self.set_visible(False)
            
        def on_about(self, data=None):
            """ Opens the About Dialog. """
            dialog = gtk.AboutDialog()
            dialog.set_name('Slackware Update Notifier - extended')
            # VERSIONNUMBER
            dialog.set_version(wpath.version)
            dialog.set_comments('An icon that shows if you need to update. (slackpkg based)')
            #dialog.set_website('http://www.guax.com.br/')
            dialog.run()
            dialog.destroy()

        def marked_info(self, lista):
            dialog = gtk.MessageDialog(parent=None, flags=0, type=gtk.MESSAGE_INFO, buttons=gtk.BUTTONS_OK)
            dialog.set_title('Marked as NonRepo')
            dialog.set_markup('Packages marked as Non-Official Repo:')
            dialog.format_secondary_text(lista)
            dialog.add_button('DELETE List',-8)
            response = dialog.run()
            if response == -8 and os.path.isfile('repo/non_repo_pkg.txt'):
                os.popen('rm -rf repo/non_repo_pkg.txt')
                gobject.idle_add(printInThread, '\"NonRepo\" list deleted.')
            dialog.destroy()

    if hasattr(gtk, "StatusIcon"):
        class StatusTrayIconGUI(gtk.StatusIcon, TrayIconGUI):
            """ Class for creating the wicd tray icon on gtk > 2.10.
            
            Uses gtk.StatusIcon to implement a tray icon.
            
            """
            def __init__(self, use_tray=True):
                TrayIcon.TrayIconGUI.__init__(self, use_tray)
                self.use_tray = use_tray
    
                gtk.StatusIcon.__init__(self)
    
                self.current_icon_path = ''
                self.set_visible(True)
                #self.check()
                self.connect('activate', self.on_activate)
                self.connect('popup-menu', self.on_popup_menu)
                self.current_icon_path = wpath.images
                gtk.StatusIcon.set_from_file(self, wpath.images + "icon.png")
                self.set_tooltip("No updates")
    
            def on_popup_menu(self, status, button, timestamp):
                """ Opens the right click menu for the tray icon. """
                self.menu.popup(None, None, None, button, timestamp)

def usage():
    # VERSIONNUMBER
    """ Print usage information. """
    print """
slackpkg-notifier """ + wpath.version + """
An icon that shows if you need to update. (slackpkg based).

Arguments:
\t-h\t--help\t\tPrint this help information.
"""

def main(argv):
    """ The main frontend program.

    Keyword arguments:
    argv -- The arguments passed to the script.

    """
    use_tray = True
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'h', ['help'])
    except getopt.GetoptError:
        # Print help information and exit
        usage()
        sys.exit(2)

    for opt, a in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit(0)
        else:
            usage()
            sys.exit(2)

    # Set up the tray icon GUI
    tray_icon = TrayIcon(use_tray)
    checker = PeriodicChecker(tray_icon.tr)
    checker.start()
    mainloop = gobject.MainLoop()
    mainloop.run()


if __name__ == '__main__':
    main(sys.argv)