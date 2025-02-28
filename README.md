vdu_controls - a DDC control panel for monitors
===============================================

A control panel for external monitors (*Visual Display Units*).

Description
-----------

``vdu_controls`` is a virtual control panel for externally connected VDU's.  The application detects 
DVI, DP, HDMI, or USB connected VDU's.  It provides controls for settings such as brightness and contrast.

The application interacts with VDU's via the VESA *Display Data Channel* (*DDC*) *Virtual Control Panel*  (*VCP*) 
commands set.  DDC VCP interactions are mediated by the ``ddcutil`` command line utility.  ``Ddcutil`` provides
a robust interface that is tolerant of the vagaries of the many OEM DDC implementations.

By default ``vdu_controls`` offers a subset of controls including brightness, contrast and audio controls.  Additional
controls can be enabled via the ``Settings`` dialog.  ``vdu_controls`` may optionally run as an entry in the
system tray.

Named ``Preset`` configurations can be saved for later recall. For example, a user could create
presets for night, day, photography, movies, and so forth.  Presets may be automatically triggered
according to solar elevation, and can be further constrained by local weather conditions (as
reported by [https://wttr.in](https://wttr.in)) 

The UI's look-and-feel dynamically adjusts to the desktop theme and desktop environment: light-theme,
dark-theme, KDE, Deepin, GNOME, and others.

![Default](screen-shots/Screenshot_Large-330.png)  ![Custom](screen-shots/Screenshot_Small-227.png) 
![Custom](screen-shots/Screenshot_tray-200.png) ![Custom](screen-shots/Screenshot_settings-300.png)

Getting Started
---------------

To get started with ``vdu_controls``, you only need to download the ``vdu_controls.py`` python script and
check that the dependencies described below are in place.  Alternatively, should you wish to install ``vdu_controls`` 
for all users, rpm's are available for **OpenSUSE**, **Fedora**, and there is an  **archlinux** AUR package
which also works in **Manjaro**.  See the *Install* section below. 


Dependencies
------------

All the following runtime dependencies are likely to be pre-packaged on any modern Linux distribution 
(``vdu_controls`` was originally developed on OpenSUSE Tumbleweed).

* ddcutil: the command line utility that interfaces to VDU's via DDC over i2c-dev or USB.
* i2c-dev: the i2c-dev kernel module normally shipped with all Linux distributions and required by [ddcutil](https://www.ddcutil.com)
* python >=3.8: ``vdu_controls`` is written in python and may depend on some features present only in 3.8 onward.
* python >=3.8 QtPy: the python GUI library used by ``vdu_controls``.

It's best to confirm that ``ddcutil`` is functioning before using ``vdu_controls``:

* See [https://www.ddcutil.com/config/](https://www.ddcutil.com/config/) for instructions on configuring ``ddcutil``.
* See [https://www.ddcutil.com/i2c_permissions/](https://www.ddcutil.com/i2c_permissions/) for instructions on setting 
  and testing the required permissions.  

The steps to obtaining the necessary rw permissions on ``/dev/i2c-[0-9]`` varies from one Linux distribution to 
another. It may be necessary to follow all the steps described at www.ddcutil.com.  

For the impatient the following steps can be followed to perform an insecure quick test (they grant anyone on the 
target machine access to the i2c devices):

1. Load i2c-dev: ``sudo modprobe i2c-dev``
2. Temporarily grant rw to everyone: ``sudo chmod a+rw /dev/i2c-*``
3. See if ddcutil works in a normal user's account: ``ddcutil detect``
4. See if vdu_controls now works in a normal user's account: ``python3 vdu_controls.py``

If this works, then following the longer series of steps detailed by the links in the previous comment 
would be the key to getting permissions set permanently.  

For the record, on my own OpenSUSE systems I diverge a little from the ddcutil documentation and
use a variation of udev based approach described there.  Rather than setting up an i2c
group, I set up udev rules to restrict i2c access to who ever is currently logged in (and 
no one else).  Either approach should work.  These are the steps I employ to set up my own 
local udev rule:

Use an editor, echo, or cat to create a rule file and then activate it:
```
cat > /etc/udev/rules.d/60-ddcutil.rules <<EOF
# local ddcutil udev rules
# User I2C/DDC/CI Access
KERNEL=="i2c-[0-99]*", TAG+="uaccess"
EOF
udevadm control --reload-rules
udevadm trigger
```
Now udevadm should report the uaccess TAG:
```
udevadm info /dev/i2c-1
...
E: TAGS=:uaccess:seat:
```
And getfacl should report an access control list entry for the current graphical session owner:
```
getfacl /dev/i2c-1
...
user:alice:rw-
```
From now on, graphical login and logout will reassign i2c access to the session owner.

Installing
----------

As previously stated, the ``vdu_vontrols.py`` script is only file required beyond the prerequisites. There
are also **OpenSUSE** and **Fedora** rpm's available at: [https://software.opensuse.org/package/vdu_controls](https://software.opensuse.org/package/vdu_controls)
and an **archlinux** (**manjaro** compatible) **AUR** package at: [https://aur.archlinux.org/packages/vdu_controls](https://aur.archlinux.org/packages/vdu_controls)


That makes three options for "installation": 

1. The script can be run without installation by using a python interpreter, for example:
   ```
   % python3 vdu_controls.py
   ```
2. The script can be self installed as desktop application in the current user's desktop menu 
   as *Applications->Settings->VDU Controls* by running:
   ```
    % python3 vdu_controls.py --install
   ```
      Depending on which desktop you're running menu changes may require logout before they become visible.
3. A system-wide installation:
   ```
   sudo rpm --install vdu_controls-1.5.0-17.1.noarch.rpm
   ```
   The rpm will install the following files:
   ```
   /usr/bin/vdu_controls
   /usr/share/applications/vdu_controls.desktop
   /usr/share/licenses/vdu_controls
   /usr/share/licenses/vdu_controls/LICENSE.md
   /usr/share/man/man1/vdu_controls.1.gz
   ```

Please note the first two options only install ``vdu-controls`` for the current user.  The script and desktop-file 
installed for a single user could be modified and copied into /usr or /usr/local hierarchies should you 
wish to do so.

Executing the program
---------------------

* If installed from rpm, **VDU Controls** should be in everyone's application menu under **Settings**. 
  The ``vdu_controls`` command will also be in everyone's ``PATH`` and will be able to be run from the command
  line, for example:
     ```
     % vdu_controls --show brightness --show contrast --show audio-volume
     ```
* If installed by the current user via the ``--install`` option, **VDU Controls** should be in
  the current user's application menu under **Settings**. The ``vdu_controls`` command will be in ``$HOME/bin``.
  If ``$HOME/bin`` is on the user's ``PATH``, ``vdu_controls`` will be also able to be run from the command
  line in the same manner as above.
* If the script has not been installed, it can still be run on the command line via the python interpreter, 
  for example:\
  ``% python3 vdu_controls.py --no-splash --system-tray --show brightness --show contrast``

Help
----

Detailed help can be accessed by using the right mouse-button to bring up a context-menu.  Access to the context-menu
is available in the application-window and in the system-tray icon.

Both brief help and detailed help can also be accessed via the command line:
```
% python3 vdu_controls.py --help
% python3 vdu_controls.py --detailed-help
% python3 vdu_controls.py --detailed-help | pandoc --from markdown --to html > vdu_controls_help.html
# or if installed in $HOME/bin
% vdu_controls --help
% vdu_controls --detailed-help
% vdu_controls --detailed-help --detailed-help | pandoc --from markdown --to html > vdu_controls_help.html
```

Whether run from the desktop application-menu or run from the command line, ``vdu-controls`` behaviour can be altered
in a number of ways:

* The `Settings` item in the context-menu.
* Command line options.
* Configurations files in `$HOME/.config/vdu_controls/`

See the context-menu or the  [man page](https://htmlpreview.github.io/?https://raw.githubusercontent.com/digitaltrails/vdu_controls/master/docs/_build/man/vdu_controls.1.html)
 for details.

VDU controls and optimisations can be specified in the global or VDU-specific config-files.

Development
-----------

I've set up the ``vdu_controls`` source with a typical Python development, but there is only one real source
file, ``vdu_controls.py``, so the file hierarchy is rather over the top.  A standard python distributable 
can be built by issuing the following commands at the top of the project hierarchy:
```
% python3 -m build
...
% ls -1 dist/
total 268
vdu_controls_digitaltrails-1.0.0-py3-none-any.whl
vdu_controls-digitaltrails-1.0.0.tar.gz
```

The source includes configuration files for the 
[Sphinx Python Documentation Generator](https://www.sphinx-doc.org/en/master/index.html). 
The following commands will extract documentation from ``vdu_controls.py``:
```
% cd docs
% make man
% make html
```

My IDE for this project is [PyCharm Community Edition](https://www.jetbrains.com/pycharm/).

My development Linux desktop is [OpenSUSE Tumbleweed](https://get.opensuse.org/tumbleweed/). The python3
interpreter and python3 libraries are from the standard OpenSUSE Tumbleweed repositories (Tumbleweed currently
defaults python3 to [python 3.8](https://www.python.org/downloads/release/python-380/)).

Author
------

Michael Hamilton


Version History
---------------
* 1.8.4
  * Performance enhancements: 
    * speed up initialization and refresh by combining multiple ddcutil getvcp requests; 
    * stop executing a getvcp precheck beofre each setvcp. 
  * _Settings Dialog_ text field validation fixes.
  * _Settings Dialog_ _Settings Enable VCP Codes_ now works again.
  * Fix the monitor specific sleep multipliers (they were not always being used).
  * Treat all monitor detection situations as needing time to stabilise (helps in disconnect situations).
  * Dropped support for pre v1.8.0 config files. To convert from earlier versions, upgrade to v1.8.3 first. 
* 1.8.3
  * Fix for a crash when the network is down and the weather site cannot be contacted. 
* 1.8.2
  * Solar elevation weather requirements.
  * Locale language support and sample AI generated translations.
* 1.8.0
  * Presets can be scheduled to activate according to solar elevation at a given latitude and longitude.
* 1.7.2
  * Better handle monitors being powered off: on set-value errors, check what's connected. 
  * The display ordering of presets can now be manually altered in the Presets dialog.
  * Do not exit if no controllable monitor is found.
* 1.7.1
  * Refactoring in 1.7 broke the signal handling - incorporate fix from Mark Lowne. 
* 1.7.0
  * Presets can now optionally have icons which display in the menu and overlay the tray icon.
  * The Preset-management dialog now includes an icon selection button.
* 1.6.11
  * Display current preset in window and tray title and detect if a preset is in use at startup.
* 1.6.10, 1.6.9
  * Cope better with invalid slider values caused by a monitor being too slow/busy when responding.
  * Wait for monitor detection to stabilise at session restoration (at login time).
* 1.6.8
  * Fix preset restore/save bug introduced in 1.6.7
* 1.6.7
  * Gnome system tray behaviour made consistent with gnome - when in gnome do as the gnomens do.
* 1.6.5
  * Widen handling of pare exceptions for VDU capabilities - catch more exceptions.
* 1.6.4
  * Wait for system tray to become available (for autostart Plasma Wayland).
  * Enable HiDPI icons (for the bottom toolbar) - fix blurred toolbar icons on up-scaled desktops.
* 1.6.3
  * Added a hamburger menu as an obvious alternate path to the context menu.
  * Minor cosmetic UI changes.
* 1.6.2
  * Added a Feature Values: min..max override to optionally restrict brightness and other sliders.
* 1.6.1
  * Alterations for Wayland compatibility (cosmetic)
* 1.6.0
  * Let other processes trigger vdu_controls preset changes and settings refreshes via UNIX/Linux signals.
* 1.5.2
  * ``vdu-controls`` is now feature complete in respect to my own requirements.
  * Raise popup dialogs to the top (in case Qt renders them behind existing windows).
  * Documentation tweaks.
* 1.5.1
  * New grey-scale reference chart for assistance with brightness and contrast adjustment.
  * About/help/settings/presets dialogs are now singletons, only one of each can be visible.
* 1.5.0
  * New presets feature: easily switch between named presets such as *Night*, *Day*, *Overcast*, *Sunny*, 
    *Photography*, and *Video*.
  * ``Presets`` context-menu item for access to the new ``preset management widget``.
  * Context menu shortcuts for quickly accessing presets.
  * INI preset file format for ease of editing.
* 1.4.2
  * Fix increasing indentation of multiline capabilities text on each config file save.
  * Prune the VDU settings-editor control-list to only show controls supported by the VDU.
  * Use grid layout in the ``settings`` editor.
* 1.4.1
  * Internal code cleanups after switching to INI config files (no functional changes).
  * Updated the help.
* 1.4.0
  * Added global and VDU-specific INI style configuration files in `$HOME/.conf/vdu_controls/`.
  * Added a GUI settings-editor as a `settings` menu-item in the context-menu.
* 1.3.1
  * A minor enhancement to ease installation on Ubuntu, create ``$HOME/bin`` if it doesn't exist. 
* 1.3.0
  * Add a CUSTOM::Sleep_Multiplier VDU config-file option to allow VDU specific sleep multipliers.
    This can be used to prevent the slowest VDU from dragging down response time for all connected VDU's.
  * Added a main UI right-mouse action that makes the context menu available in the UI window.
  * Added a help option to context menu, it displays a formatted version of the ``--detailed-help`` text.
  * Added a ``--detailed-help`` command line option to extract the help from the script (in Markdown format).
* 1.2.2
  * Generalise and simplify the error handling changes initiated in v1.2.1.
* 1.2.1
  * Catch ddcutil error exit and offer to try a slower --sleep-multiplier
* 1.2
  * Better handle out of range values.
  * Enable audio-mute,audio-treble,audio-bass,audio-mic-volume.
  * Allow ddcutil to be anywhere on the user's PATH.
  * Improve parsing to ignore laptop non-MCCS displays when present with external monitors. 
  * Improve the documentation.
  * Add an --about command line option and an "about" tray option.
* 1.0
  * Initial Release

License
-------

This project is licensed under the **GNU General Public License Version 3** - see the [LICENSE.md](LICENSE.md) file 
for details

**vdu_controls Copyright (C) 2021 Michael Hamilton**

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, version 3.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
more details.

You should have received a copy of the GNU General Public License along
with this program. If not, see <https://www.gnu.org/licenses/>.

## Acknowledgments

* [ddcutil](https://www.ddcutil.com)
* [pyqt](https://riverbankcomputing.com/software/pyqt/)
* [Sphinx Python Documentation Generator](https://www.sphinx-doc.org/en/master/index.html)
* [PyCharm Community Edition](https://www.jetbrains.com/pycharm/)
* [Pandoc](https://pandoc.org/)
