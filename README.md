This is modified and extended version of https://github.com/guax/slackpkg-notifier

**Modifications:**
- Added supporting slackpkg+
- Added Hide icon option in tray
- Notifier automatically checking for updates available for your own system
- If you have installed packages coming from no-official repository, you can mark them and will not be checking anymore. System MUST be upgraded before running thin option.
- Left click on 'U' icon in tray makes run updating and upgrading system - if available

**Requirements:**
- Installed xterm
- Add this line to /etc/sudoers : 'account_name ALL=(ALL) NOPASSWD: /usr/sbin/slackpkg' where 'account_name' is your own linux account ;)
