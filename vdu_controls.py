#!/usr/bin/python3
"""
See: https://github.com/digitaltrails/vdu_controls/issues/38
"""
from __future__ import annotations

import argparse
import base64
import configparser
import glob
import inspect
import io
import json
import locale
import math
import os
import pickle
import re
import signal
import socket
import stat
import subprocess
import sys
import syslog
import textwrap
import time
import traceback
import urllib.request
from collections import namedtuple
from datetime import datetime, timedelta, date, timezone
from enum import Enum
from functools import partial
from pathlib import Path
from typing import List, Tuple, Mapping, Type, Dict, Callable
from urllib.error import URLError

from PyQt5 import QtNetwork
from PyQt5.QtCore import Qt, QCoreApplication, QThread, pyqtSignal, QProcess, QRegExp, QPoint, QObject, QEvent, \
    QSettings, QSize, QTimer, QTranslator, QLocale, QT_TR_NOOP
from PyQt5.QtGui import QIntValidator, QPixmap, QIcon, QCursor, QImage, QPainter, QDoubleValidator, QRegExpValidator, \
    QPalette, QGuiApplication, QColor, QValidator, QPen, QFont
from PyQt5.QtSvg import QSvgWidget, QSvgRenderer
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QSlider, QMessageBox, QLineEdit, QLabel, \
    QSplashScreen, QPushButton, QProgressBar, QComboBox, QSystemTrayIcon, QMenu, QStyle, QTextEdit, QDialog, QTabWidget, \
    QCheckBox, QPlainTextEdit, QGridLayout, QSizePolicy, QAction, QMainWindow, QToolBar, QToolButton, QFileDialog, \
    QWidgetItem, QScrollArea, QGroupBox, QFrame, QSplitter

APPNAME = "VDU Controls"
VDU_CONTROLS_VERSION = '1.8.4'


def zoned_now() -> datetime:
    return datetime.now().astimezone()


def proper_name(*args):
    return re.sub(r'[^A-Za-z0-9._-]', '_', '_'.join([arg.strip() for arg in args]))


def tr(source_text: str, disambiguation: str = None):
    """
    This function is named tr() so that it matches what pylupdate5 is looking for.
    If this method is ever renamed to something other than tr(), then you must
    pass -ts-function=new_name to pylupdate5.

    For future internationalization:
    1) Generate template file from this code, for example for French:
       ALWAYS BACKUP THE CURRENT .ts FILE BEFORE RUNNING AN UPDATE - it can go wrong!
           pylupdate5 vdu_controls.py -ts translations/fr_FR.ts
       where translations is a subdirectory of your current working directory.
    2) Edit that using a text editor or the linguist-qt5 utility.
       If using an editor, remove the 'type="unfinished"' as you complete each entry.
    3) Convert the .ts to a binary .qm file
           lrelease-qt5 translations/fr_FR.ts
           mkdir -p $HOME/.config/vdu_controls/translations/
           translations/fr_FR.qm $HOME/.config/vdu_controls/translations/
    4) Test using by setting LC_ALL for python and LANGUAGE for Qt
           LC_ALL=fr_FR LANGUAGE=fr_FR python3 vdu_controls.py
       At startup the app will log several messages as it searches for translation files.
    5) Completed .qm files can reside in $HOME/.config/vdu_controls/translations/
       or  /user/share/vdu_controls/translations/
    """
    # If the source .ts file is newer, we load messages from the XML into ts_translations
    # and use the most recent translations. Using the .ts files in production may be a good
    # way to allow the users to help themselves.
    if ts_translations:
        if source_text in ts_translations:
            return ts_translations[source_text]
    # the context @default is what is generated by pylupdate5 by default
    return QCoreApplication.translate('@default', source_text, disambiguation=disambiguation)


ABOUT_TEXT = f"""

<b>vdu_controls version {VDU_CONTROLS_VERSION}</b>
<p>
A virtual control panel for external Visual Display Units.
<p>
Visit <a href="https://github.com/digitaltrails/vdu_controls">https://github.com/digitaltrails/vdu_controls</a> for
more details.
<p>
Release notes: <a href="https://github.com/digitaltrails/vdu_controls/releases/tag/v{VDU_CONTROLS_VERSION}">
v{VDU_CONTROLS_VERSION}.</a>
<p>
<hr>
<small>
<b>vdu_controls Copyright (C) 2021 Michael Hamilton</b>
<br><br>
This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, version 3.
<br><br>

<bold>
This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
more details.
</bold>
<br><br>
You should have received a copy of the GNU General Public License along
with this program. If not, see <a href="https://www.gnu.org/licenses/">https://www.gnu.org/licenses/</a>.
</small>
<hr>
<p><p>
<quote>
<small>
Vdu_controls relies on <a href="https://www.ddcutil.com/">ddcutil</a>, a robust interface to DDC capable VDU's.
</small>
</quote>
"""

# Use Linux/UNIX signals for interprocess communication to trigger preset changes - 16 presets should be enough
# for anyone.
PRESET_SIGNAL_MIN = 40
PRESET_SIGNAL_MAX = 55

SVG_LIGHT_THEME_COLOR = b"#232629"
SVG_DARK_THEME_COLOR = b"#f3f3f3"

MENU_ICON_SOURCE = b"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
  <defs id="defs3051">
    <style type="text/css" id="current-color-scheme">
      .ColorScheme-Text {
        color:#232629;
      }
      </style>
  </defs>
  <g transform="translate(1,1)">
    <path style="fill:currentColor;fill-opacity:1;stroke:none" d="m3 5v2h16v-2h-16m0 5v2h16v-2h-16m0 5v2h16v-2h-16" class="ColorScheme-Text"/>
  </g>
</svg>
"""

REFRESH_ICON_SOURCE = b"""
<svg xmlns="http://www.w3.org/2000/svg" version="1.1" viewBox="0 0 24 24" width="24" height="24">
  <defs>
    <style type="text/css" id="current-color-scheme">.ColorScheme-Text {
        color:#232629;
      }</style>
  </defs>
  <g transform="translate(1,1)">
    <path class="ColorScheme-Text" fill="currentColor" d="m 19,11 c 0,1.441714 -0.382922,2.789289 -1.044922,3.955078 l -0.738281,-0.738281 c 0,0 0.002,-0.0019 0.002,-0.0019 l -2.777344,-2.779297 0.707032,-0.707031 2.480468,2.482422 C 17.861583,12.515315 18,11.776088 18,11 18,7.12203 14.878,4 11,4 9.8375,4 8.746103,4.285828 7.783203,4.783203 L 7.044922,4.044922 C 8.210722,3.382871 9.5583,3 11,3 c 4.432,0 8,3.568034 8,8 z m -4.044922,6.955078 C 13.789278,18.617129 12.4417,19 11,19 6.568,19 3,15.431966 3,11 3,9.558286 3.382922,8.210711 4.044922,7.044922 l 0.683594,0.683594 0.002,-0.002 2.828125,2.828126 L 6.851609,11.261673 4.373094,8.783157 C 4.139126,9.480503 4,10.221736 4,11 c 0,3.87797 3.122,7 7,7 1.1625,0 2.253897,-0.285829 3.216797,-0.783203 z"/>
  </g>
</svg>
"""

#: Internal special exit code used to signal that the exit handler should restart the program.
EXIT_CODE_FOR_RESTART = 1959


def is_dark_theme():
    # Heuristic for checking for a dark theme.
    # Is the sample text lighter than the background?
    label = QLabel("am I in the dark?")
    text_hsv_value = label.palette().color(QPalette.WindowText).value()
    bg_hsv_value = label.palette().color(QPalette.Background).value()
    dark_theme_found = text_hsv_value > bg_hsv_value
    # debug(f"is_dark_them text={text_hsv_value} bg={bg_hsv_value} is_dark={dark_theme_found}") if debugging else None
    return dark_theme_found


def log_wrapper(severity, *args):
    prefix = {syslog.LOG_INFO: "INFO:", syslog.LOG_ERR: "ERROR:",
              syslog.LOG_WARNING: "WARNING:", syslog.LOG_DEBUG: "DEBUG:"}[severity]
    with io.StringIO() as output:
        print(*args, file=output, end='')
        message = output.getvalue()
        print(prefix, message)


def log_debug(*args):
    log_wrapper(syslog.LOG_DEBUG, *args)


def log_info(*args):
    log_wrapper(syslog.LOG_INFO, *args)


def log_warning(*args):
    log_wrapper(syslog.LOG_WARNING, *args)


def log_error(*args):
    log_wrapper(syslog.LOG_ERR, *args)


def si(widget: QWidget, icon_number: int):
    return widget.style().standardIcon(icon_number)


class DialogSingletonMixin:
    """
    A mixin that can augment a QDialog or QMessageBox with code to enforce a singleton UI.
    For example, it is used so that only ones settings editor can be active at a time.
    """
    _dialogs_map = {}
    debug = False

    def __init__(self) -> None:
        """Registers the concrete class as a singleton, so it can be reused later."""
        super().__init__()
        class_name = self.__class__.__name__
        if class_name in DialogSingletonMixin._dialogs_map:
            raise TypeError(f"ERROR: More than one instance of {class_name} cannot exist.")
        if DialogSingletonMixin.debug:
            log_debug(f'SingletonDialog created for {class_name}')
        DialogSingletonMixin._dialogs_map[class_name] = self

    def closeEvent(self, event) -> None:
        """Subclasses that implement their own closeEvent must call this closeEvent to deregister the singleton"""
        class_name = self.__class__.__name__
        if DialogSingletonMixin.debug:
            log_debug(f'SingletonDialog remove {class_name} '
                      f'registered={class_name in DialogSingletonMixin._dialogs_map}')
        if class_name in DialogSingletonMixin._dialogs_map:
            del DialogSingletonMixin._dialogs_map[class_name]
        event.accept()

    def make_visible(self):
        """
        If the dialog exists(), call this to make it visible by raising it.
        Internal, used by the class method show_existing_dialog()
        """
        # .show() is non-modal, .exec() is modal
        self.show()
        self.raise_()
        self.activateWindow()

    @classmethod
    def show_existing_dialog(cls: Type):
        """If the dialog exists(), call this to make it visible by raising it."""
        class_name = cls.__name__
        if DialogSingletonMixin.debug:
            log_debug(f'SingletonDialog show existing {class_name}')
        instance = DialogSingletonMixin._dialogs_map[class_name]
        instance.make_visible()

    @classmethod
    def exists(cls: Type) -> bool:
        """Returns true if the dialog has already been created."""
        class_name = cls.__name__
        if DialogSingletonMixin.debug:
            log_debug(f'SingletonDialog exists {class_name} {class_name in DialogSingletonMixin._dialogs_map}')
        return class_name in DialogSingletonMixin._dialogs_map

    @classmethod
    def get_instance(cls: Type):
        class_name = cls.__name__
        if class_name in DialogSingletonMixin._dialogs_map:
            return DialogSingletonMixin._dialogs_map[class_name]
        return None


LOCALE_TRANSLATIONS_PATHS = [
    Path.cwd().joinpath('translations')] if os.getenv('VDU_CONTROLS_DEVELOPER', default="no") == 'yes' else [] + [
    Path("/usr/share/vdu_controls/translations"), ]


class ContextMenu(QMenu):

    def __init__(self,
                 main_window,
                 main_window_action,
                 about_action, help_action, chart_action, settings_action,
                 presets_action, refresh_action, quit_action) -> None:
        super().__init__()
        self.main_window = main_window
        if main_window_action is not None:
            self.addAction(si(self, QStyle.SP_ComputerIcon), tr('Control Panel'), main_window_action)
            self.addSeparator()
        self.addAction(si(self, QStyle.SP_ComputerIcon), tr('Presets'), presets_action)
        self.presets_separator = self.addSeparator()

        self.addAction(si(self, QStyle.SP_ComputerIcon), tr('Grey Scale'), chart_action)
        self.addAction(si(self, QStyle.SP_ComputerIcon), tr('Settings'), settings_action)
        self.addAction(si(self, QStyle.SP_BrowserReload), tr('Refresh'), refresh_action)
        self.addAction(si(self, QStyle.SP_MessageBoxInformation), tr('About'), about_action)
        self.addAction(si(self, QStyle.SP_DialogHelpButton), tr('Help'), help_action)
        self.addSeparator()
        self.addAction(si(self, QStyle.SP_DialogCloseButton), tr('Quit'), quit_action)


class BottomToolBar(QToolBar):

    def __init__(self, start_refresh_func, app_context_menu, parent):
        super().__init__(parent=parent)
        self.refresh_action = self.addAction(
            create_icon_from_svg_bytes(REFRESH_ICON_SOURCE), "Refresh settings from monitors", start_refresh_func)
        self.setIconSize(QSize(32, 32))
        self.progress_bar = QProgressBar(self)
        # Disable text percentage label on the spinner progress-bar
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setDisabled(True)
        self.addWidget(self.progress_bar)

        self.menu_button = QToolButton(self)
        self.menu_button.setIcon(create_icon_from_svg_bytes(MENU_ICON_SOURCE))
        self.menu_button.setMenu(app_context_menu)
        self.menu_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.menu_button.setToolTip("Context Menu")

        self.preset_action = self.addAction(QIcon(), "")
        self.preset_action.setVisible(False)
        self.preset_action.triggered.connect(self.menu_button.click)

        self.addWidget(self.menu_button)


class VduControlsMainPanel(QWidget):
    """GUI for detected VDU's, it will construct and contain a control panel for each VDU."""

    def __init__(self) -> None:
        super().__init__()
        self.vdu_controllers = []
        self.bottom_toolbar = None
        self.context_menu = None
        self.setObjectName("vdu_controls_main_panel")
        self.non_standard_enabled = None
        self.vdu_control_panels = []
        self.previously_detected_vdus = []
        self.detected_vdus = []

    def initialise_control_panels(self, app_context_menu: ContextMenu, main_config: None):
        if self.layout():
            # Already laid out, must be responding to a configuration change requiring re-layout.
            # Remove all exisiting widgets.
            for i in range(0, self.layout().count()):
                item = self.layout().itemAt(i)
                if isinstance(item, QWidget):
                    self.layout().removeWidget(item)
                    item.deleteLater()
                elif isinstance(item, QWidgetItem):
                    self.layout().removeItem(item)
                    item.widget().deleteLater()

        layout = QVBoxLayout()
        self.setLayout(layout)
        self.previously_detected_vdus = self.detected_vdus
        self.context_menu = app_context_menu
        controllers_layout = self.layout()
        self.vdu_controllers = []

        if len(self.vdu_control_panels) == 0:
            no_vdu_widget = QWidget()
            no_vdu_layout = QHBoxLayout()
            no_vdu_widget.setLayout(no_vdu_layout)
            no_vdu_text = QLabel('This app does nothing.')
            no_vdu_text.setAlignment(Qt.AlignLeft)
            no_vdu_image = QLabel()
            no_vdu_image.setPixmap(QApplication.style().standardIcon(QStyle.SP_MessageBoxWarning).pixmap(QSize(64, 64)))
            no_vdu_image.setAlignment(Qt.AlignVCenter)
            no_vdu_layout.addSpacing(32)
            no_vdu_layout.addWidget(no_vdu_image)
            no_vdu_layout.addWidget(no_vdu_text)
            no_vdu_layout.addSpacing(32)
            controllers_layout.addWidget(no_vdu_widget)

        self.bottom_toolbar = \
            BottomToolBar(start_refresh_func=self.start_refresh, app_context_menu=app_context_menu, parent=self)
        layout.addWidget(self.bottom_toolbar)
        self.setContextMenuPolicy(Qt.CustomContextMenu)

        def open_context_menu(position: QPoint) -> None:
            self.context_menu.exec(self.mapToGlobal(position))

        self.customContextMenuRequested.connect(open_context_menu)

    def start_refresh(self) -> None:
        print('start_refresh')


class MessageBox(QMessageBox):
    def __init__(self, icon: QIcon, buttons: int = QMessageBox.NoButton, default: int | None = None) -> None:
        super().__init__(icon, APPNAME, '', buttons=buttons)
        if default is not None:
            self.setDefaultButton(default)


def exception_handler(e_type, e_value, e_traceback):
    """Overarching error handler in case something unexpected happens."""
    log_error("\n" + ''.join(traceback.format_exception(e_type, e_value, e_traceback)))
    alert = MessageBox(QMessageBox.Critical)
    alert.setText(tr('Error: {}').format(''.join(traceback.format_exception_only(e_type, e_value))))
    alert.setInformativeText(tr('Is --sleep-multiplier set too low?') +
                             '<br>_______________________________________________________<br>')
    alert.setDetailedText(
        tr('Details: {}').format(''.join(traceback.format_exception(e_type, e_value, e_traceback))))
    alert.exec()
    QApplication.quit()


def handle_theme(svg_str: bytes) -> bytes:
    if is_dark_theme():
        svg_str = svg_str.replace(SVG_LIGHT_THEME_COLOR, SVG_DARK_THEME_COLOR)
    return svg_str


def create_pixmap_from_svg_bytes(svg_bytes: bytes):
    """There is no QIcon option for loading SVG from a string, only from a SVG file, so roll our own."""
    image = create_image_from_svg_bytes(svg_bytes)
    return QPixmap.fromImage(image)


def create_image_from_svg_bytes(svg_bytes):
    renderer = QSvgRenderer(handle_theme(svg_bytes))
    image = QImage(64, 64, QImage.Format_ARGB32)
    image.fill(0x0)
    painter = QPainter(image)
    renderer.render(painter)
    painter.end()
    return image


def create_icon_from_svg_bytes(svg_bytes: bytes) -> QIcon:
    """There is no QIcon option for loading SVG from a string, only from a SVG file, so roll our own."""
    return QIcon(create_pixmap_from_svg_bytes(svg_bytes))


# TODO consider changing to a non-modal QDialog which would also remove the need for a multiple inheritance
class AboutDialog(QMessageBox, DialogSingletonMixin):

    @staticmethod
    def invoke():
        if AboutDialog.exists():
            AboutDialog.show_existing_dialog()
        else:
            AboutDialog()

    def __init__(self):
        super().__init__()
        self.setWindowTitle(tr('About'))
        self.setTextFormat(Qt.AutoText)
        self.setText(tr('About vdu_controls'))
        about_text = ABOUT_TEXT
        self.setInformativeText(about_text)
        self.setIcon(QMessageBox.Information)
        self.exec()


class HelpDialog(QDialog, DialogSingletonMixin):

    @staticmethod
    def invoke():
        if HelpDialog.exists():
            HelpDialog.show_existing_dialog()
        else:
            HelpDialog()

    def __init__(self):
        super().__init__()
        self.setWindowTitle(tr('Help'))
        layout = QVBoxLayout()
        markdown_view = QTextEdit()
        markdown_view.setReadOnly(True)
        markdown_view.setMarkdown(__doc__)
        layout.addWidget(markdown_view)
        close_button = QPushButton(si(self, QStyle.SP_DialogCloseButton), tr("Close"))
        close_button.clicked.connect(self.hide)
        layout.addWidget(close_button, 0, Qt.AlignRight)
        self.setLayout(layout)
        self.make_visible()

    def sizeHint(self) -> QSize:
        return QSize(1200, 768)


class MainWindow(QMainWindow):

    def __init__(self, main_config: None, app: QApplication):
        super().__init__()

        self.app = app
        self.displayed_preset_name = None
        self.setObjectName('main_window')
        self.geometry_key = self.objectName() + "_geometry"
        self.state_key = self.objectName() + "_window_state"
        self.settings = QSettings('vdu_controls.qt.state', 'vdu_controls')
        self.main_control_panel = None
        self.main_config = main_config
        self.weather_cache: QueryWeather = None
        self.daily_schedule_next_update = datetime.today()

        def foobar() -> None:
            print('foobar')

        def quit_app() -> None:
            print('quit_app')
            app.quit()

        self.app_context_menu = ContextMenu(main_window=self,
                                            main_window_action=None,
                                            about_action=AboutDialog.invoke,
                                            help_action=HelpDialog.invoke,
                                            chart_action=foobar,
                                            settings_action=foobar,
                                            presets_action=foobar,
                                            refresh_action=foobar,
                                            quit_action=quit_app)

        self.app_name = "VDU Controls"
        app.setApplicationDisplayName(self.app_name)
        # Make sure all icons use HiDPI - toolbars don't by default, so force it.
        app.setAttribute(Qt.AA_UseHighDpiPixmaps)

        def create_main_control_panel():
            # Call on initialisation and whenever the number of connected VDU's changes.
            existing_width = 0
            if self.main_control_panel:
                # Remove any existing control panel - which may now be incorrect for the config.
                self.main_control_panel.width()
                self.main_control_panel.deleteLater()
            self.main_control_panel = VduControlsMainPanel()
            # Then initialise the control panel display
            self.main_control_panel.initialise_control_panels(self.app_context_menu, main_config)
            self.setCentralWidget(self.main_control_panel)
            self.setMinimumWidth(existing_width)

        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        create_main_control_panel()

        self.show()

    def closeEvent(self, event):
        event.accept()  # let the window close

    # This causes https://github.com/digitaltrails/vdu_controls/issues/38
    #def event(self, event: QEvent) -> bool:
    #    super().event(event)
    #    event.accept()
    #    return True


ts_translations: Mapping[str, str] = {}


def main():
    """vdu_controls application main."""
    # Allow control-c to terminate the program
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    def signal_handler(x, y):
        log_info("signal received", x, y)

    signal.signal(signal.SIGHUP, signal_handler)
    for i in range(PRESET_SIGNAL_MIN, PRESET_SIGNAL_MAX):
        signal.signal(i, signal_handler)

    sys.excepthook = exception_handler

    # This is supposed to set the locale for all categories to the user’s default setting.
    # This can error on some distros when the required language isn't installed, or if LANG
    # is set without also specifying the UTF-8 encoding, so LANG=da_DK might fail,
    # but LANG=da_DK.UTF-8 should work. For our purposes failure is not important.
    try:
        locale.setlocale(locale.LC_ALL, '')
    except locale.Error:
        log_warning("Could not set the default locale - may not be an issue...")
    log_info("Python locale", locale.getlocale())

    # Call QApplication before parsing arguments, it will parse and remove Qt session restoration arguments.
    app = QApplication(sys.argv)

    # Wayland needs this set in order to find/use the app's desktop icon.
    QGuiApplication.setDesktopFileName("vdu_controls")

    main_config = None

    log_info(f"application style is {app.style().objectName()}")

    # Assign to variable to stop it being reclaimed as garbage
    if False:
    #if main_config.is_translations_enabled():
        initialise_locale_translations(app)

    main_window = MainWindow(main_config, app)

    rc = app.exec_()
    log_info(f"app exit rc={rc} {'EXIT_CODE_FOR_RESTART' if rc == EXIT_CODE_FOR_RESTART else ''}")
    sys.exit(rc)


if __name__ == '__main__':
    main()
