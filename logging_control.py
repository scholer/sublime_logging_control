#!/usr/bin/env python
# -*- coding: utf-8 -*-
##    Copyright 2015 Rasmus Scholer Sorensen, rasmusscholer@gmail.com
##
##    This program is free software: you can redistribute it and/or modify
##    it under the terms of the GNU General Public License as published by
##    the Free Software Foundation, either version 3 of the License, or
##    (at your option) any later version.
##
##    This program is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##    GNU General Public License for more details.
##
##    You should have received a copy of the GNU General Public License
##    along with this program.  If not, see <http://www.gnu.org/licenses/>.

# pylint: disable=C0103,W0232,R0903,R0201

"""
Sublime Logging - Plugin for Sublime Text to enable and adjust logging output.

Usage:
* (a) Use ctrl+shift+p - type "logging" and select a command.
* (b) Bind your favorite commands to keystrokes.

Configuration:
* Logging behaviour can be adjusted in the logging_control.sublime-settings file.

Settings:
* logging_{console/file}_fmt is used to alter how logging messages are displayed in console / log files.
* logging_{console/file}_level default logging level (DEBUG, INFO, WARNING, ERROR).



"""
from __future__ import print_function

# import fails because no sublime_api available.
import sublime          # pylint: disable=F0401
import sublime_plugin   # pylint: disable=F0401

import os
from functools import partial
import json
import logging
import logging.config
import logging.handlers
logger = logging.getLogger(__name__)

SETTINGS_NAME = "logging_control.sublime-settings"

defaults = {
    'logging_root_level': 'DEBUG',
    'logging_console_enabled': True,
    'logging_console_fmt': "%(asctime)s %(levelname)-5s %(name)20s:%(lineno)-4s%(funcName)20s() %(message)s",
    'logging_console_datefmt': "%H:%M:%S",
    'logging_console_level': 'INFO',
    'logging_file_enabled': False,
    'logging_file_fmt': "%(asctime)s %(levelname)-6s - %(name)s:%(lineno)s - %(funcName)s() - %(message)s",
    'logging_file_datefmt': "%Y%m%d-%H:%M:%S",
    'logging_file_level': 'DEBUG',
    'logging_file_path': 'sublime_output.log',
    'logging_file_rotating': True,  # True will use RotatingFileHandler, otherwise FileHandler
    'logging_file_clear_on_reset': True,
    'logging_config_dict_file': None,  # Use logging.config.dictConfig() to configure logging.
    'logging_config_dict': None
}


def plugin_loaded():
    """
    For Sublime Text 3:
    At importing time, plugins may not call any API functions, with the exception of
    sublime.version(), sublime.platform(), sublime.architecture() and sublime.channel().

    If a plugin defines a module level function plugin_loaded(), this will be called when
    the API is ready to use. Plugins may also define plugin_unloaded(), to get notified
    just before the plugin is unloaded.
    """
    if sublime.load_settings(SETTINGS_NAME).get("logging_enable_on_startup"):
        reset_logging_system()
    else:
        print("Logging system not enabled on startup; to display logging messages, start logging manually...")


def get_loglevel(which="root"):
    return logging.getLogger(which).level


def get_level_name(level=None):
    if level is None:
        level = logging.root.level
    if isinstance(level, int):
        return logging.getLevelName(level)
    else:
        return level


def ensure_loglevel_int(level):
    """
    Ensure that level is an appropriate logging level.
    This is only required for python 2.6 and below;
    2.7 and above handles strings and yields ValueErrors when appropriate.
    """
    if isinstance(level, int):
        return level
    return getattr(logging, level.upper())


def set_loglevel(level):
    """
    Set level of logging's root logger.
    """
    # Note: Setting level with a string (e.g. "INFO") does not work for python 2.6!
    # For python 2.6, use getattr(logging, level.upper()) to convert str level to int.
    logging.root.setLevel(level)


def get_default_log_dir():
    """
    :return: A suitable default directory to put logfile in.
    """
    # os.getcwd() is usually Sublime Text base installation path. This may not be readable.
    packages_dir = sublime.packages_path()
    # Use <sublime-text data dir>/logs/ as default directory for file logs.
    logfiledir = os.path.join(os.path.abspath(os.path.dirname(packages_dir)), 'logs')
    return logfiledir


def check_logfilepath(logfilepath):
    """
    :param logfilepath: A logfile name or path. If this is not absolute, a suitable directory will be prepended.
    :return: a valid, absolute file path to use as logfile path.
    """
    logfiledir = os.path.dirname(logfilepath)
    if not logfiledir:
        logfiledir = get_default_log_dir()
        logfilepath = os.path.join(logfiledir, logfilepath)
    if not os.path.exists(logfiledir):
        print("Making log directory:", logfiledir)
        os.mkdir(logfiledir)
    return logfilepath


def get_config(key, cfgkeyfmt, default=None):
    """
    Used to make it easier to get settings keys with long names,
    resorting to defaults for default values.
    E.g.
    >>> get_config(enabled, "logging_console_{}")
    # Will look for logging_console_enabled in settings and then defaults.
    True
    This function can be used together with functools.partial to make it even shorter
    by fixing the cfgkeyfmt argument. See usage below.
    """
    settings = sublime.load_settings(SETTINGS_NAME)
    settings_key = cfgkeyfmt.format(key)
    return settings.get(settings_key,
                        defaults.get(settings_key, default))


def reset_logging_system(settings=None):
    """
    Resets logging systems.
    """

    if settings is None:
        settings = sublime.load_settings(SETTINGS_NAME)
    if settings.get("logging_persist_changes", False) and not settings.get('logging_is_enabled', False):
        print("NOT activating logging system because persist_changes is specified and logging has been disabled.")
        return
    logger.info("Resetting logging system...")

    # These SHOULD be available in the default logging_control.sublime-settings file, but still...
    if settings.get("logging_use_basicConfig"):
        print("Initializing logging system using basicConfig...")
        filepath = (settings.get("logging_file_enabled") and settings.get("logging_file_path")) or None
        if filepath:
            print("Logging output to file:", filepath)
        if logging.root.handlers:
            print("NOTE: logging system already initialized. This command will not have any effect!"
                  "(set ```logging_use_basicConfig: false``` if you want this plugin to seize control"
                  "of logging output configuration).")
        logging.basicConfig(level=settings.get('logging_root_level'),
                            format=settings.get('logging_console_fmt'),
                            datefmt=settings.get('logging_console_datefmt'),
                            filename=filepath)
        logger.info("Logging system has been started using basicConfig.")
    elif settings.get("logging_config_dict_file") or settings.get("logging_config_dict"):
        if settings.get("logging_config_dict_file"):
            dictconfig_fn = settings.get("logging_config_dict_file")
            fnbase, fnext = os.path.splitext(dictconfig_fn)
            if fnext.lower() == ".yaml":
                print("Configuring logging system using dict config from yaml-formatted file:", dictconfig_fn)
                import yaml
                with open(dictconfig_fn) as fp:
                    dictconfig = yaml.load(fp)
            else:
                print("Configuring logging system using dict config from json-formatted file:", dictconfig_fn)
                with open(dictconfig_fn) as fp:
                    dictconfig = json.load(fp)
        else:
            print("Configuring logging system using dict from logging_control settings file")
            dictconfig = settings.get("logging_config_dict")
        logging.config.dictConfig(dictconfig)
        print(" - dictConfig logging setup complete. "
              "Note: Re-setting logging system is not supported for custom/dict-based setup; "
              "If you change the logging configuration, you must restart Sublime Text for changes to take effect.")
    else:
        # Reset logging handlers:
        # Note: This only affects the root logger.
        # Other loggers' handlers are not affected. E.g. specified with:
        # >>> logging.getlogger.info(name).addHandler(myHandler)
        print("Resetting logging system...")
        if logging.root.handlers:
            logger.info("Closing existing handlers: %s", logging.root.handlers)
            for handler in logging.root.handlers:
                handler.close()
        logging.root.handlers = []

        # Create new logging handlers for the root logger:
        for output in ('console', 'file'):
            # Create partial/closure. Usage as cfg('enabled') --> returns logging_console_enabled settings value.
            cfg = partial(get_config, cfgkeyfmt="logging_%s_{0}" % output)
            if not cfg('enabled'):
                continue
            if output == 'console':
                handler = logging.StreamHandler()
            else:
                logfilepath = settings.get("logging_file_path")
                logfilepath = check_logfilepath(logfilepath)
                filehandler_kwargs = settings.get("logging_file_handler_kwargs")
                if settings.get("logging_file_rotating"):
                    # Use rotating file handler with 3 logfiles each maxing out / rotating at 2 MB:
                    if filehandler_kwargs is None:
                        filehandler_kwargs = dict(maxBytes=2*2**20, backupCount=3)
                    handler = logging.handlers.RotatingFileHandler(logfilepath, **filehandler_kwargs)
                else:
                    if filehandler_kwargs is None:
                        filehandler_kwargs = dict()
                    handler = logging.FileHandler(logfilepath, **filehandler_kwargs)
            formatter = logging.Formatter(fmt=cfg('fmt'), datefmt=cfg('datefmt'))
            handler.setFormatter(formatter)
            # There are two places where the 'level' is evaluated:
            # (a) In the logger.
            # (b) In the handler.
            # If the call's level is >= the logger's level, it is passed to the logger's handlers.
            # If the call's level is >= the handler's level, it is emitted.
            # Typically, the level is adjusted in the logger, and the handler's level is set to 0.
            if cfg('level'):
                handler.setLevel(ensure_loglevel_int(cfg('level')))
            logging.root.addHandler(handler)

        # Set root logger's level:
        rootlevel = get_config('level', 'logging_root_{0}')
        consolelevel = get_config('level', 'logging_console_{0}') if get_config('enabled', 'logging_console_{0}') \
                       else "DISABLED"
        if not get_config('enabled', 'logging_file_{0}'):
            filelevel = "is DISABLED"
        else:
            filelevel = get_config('path', 'logging_file_{0}') + " with level " + get_config('level', 'logging_file_{0}')

        logging.root.setLevel(ensure_loglevel_int(rootlevel))
        logger.info("Logging system has been reset; root level is %s; console level is %s; logging to file %s",
                    rootlevel, consolelevel, filelevel)


class LoggingShowDefaultLogFileCommand(sublime_plugin.WindowCommand):
    """
    command key: logging_show_default_log_file
    Will open the default log file.
    """

    def run(self):
        """
        Will open the default log file.
        """
        settings = sublime.load_settings(SETTINGS_NAME)
        logging_file_path = settings.get("logging_file_path") or None
        logging_is_enabled = settings.get("logging_is_enabled")
        logging_file_enabled= settings.get("logging_file_enabled")

        if not logging_file_path:
            print("sublime_logging_control: logging_file_path is set to", logging_file_path, "; cannot open filepath.")
            return

        logging_file_path = check_logfilepath(logging_file_path)

        print("Opening default log file:", logging_file_path)
        sublime.active_window().open_file(logging_file_path)

        if not logging_file_enabled:
            print(" - Note: logging to file is currently DISABLED (logging_file_enabled=%s)." % logging_file_enabled)
        if not logging_is_enabled:
            print(" - note: logging in general is currently DISABLED (logging_is_enabled=%s)." % logging_is_enabled)


class LoggingToggleCommand(sublime_plugin.WindowCommand):
    """
    command key: logging_toggle
    """

    def run(self, enable=None):
        """
        If enable is:
            True - enable logging
            False - disable logging
            None - toggle logging
        """
        settings = sublime.load_settings(SETTINGS_NAME)

        level = logging.root.level
        if enable is None:
            enable = not settings.get('logging_is_enabled', True)

        # Set setting before doing, since logging_reset queries these:
        settings.set('logging_is_enabled', enable)
        if settings.get("logging_persist_changes", False):
            sublime.save_settings(SETTINGS_NAME)
            logger.info("Persisting settings with logging_root_level = %s and logging_is_enabled = %s",
                        level, enable)

        if enable:
            if logging.root.handlers:
                # We already have loggers defined:
                level = settings.get('logging_root_level', logging.DEBUG)
                logging.root.setLevel(ensure_loglevel_int(level))
                logger.info("Logging level set to %s", level)
            else:
                # Set up logging: (will run after this command has completed...)
                self.window.run_command("logging_reset")
            sublime.status_message("Logging Turned On (level=%s)" % get_level_name())
        else:
            # Uh, how? Probably just increase the root logger's level to sufficiently high number.
            level = 50
            logger.info("Setting logging level to %s", level)
            logging.root.setLevel(ensure_loglevel_int(level))
            sublime.status_message("Logging Turned Off (entirely)")


class LoggingSetLevelCommand(sublime_plugin.WindowCommand):
    """
    command key: logging_set_level
    """

    def run(self, level=20):
        """
        Set logging level.
        """
        logging.root.setLevel(ensure_loglevel_int(level))
        sublime.status_message("Logging level set to %s" % level)
        print("Logging level set to %s" % level)
        logger.info("Logging level set to %s", level)

        settings = sublime.load_settings(SETTINGS_NAME)
        if settings.get("logging_persist_changes", False):
            settings.set("logging_root_level", level)
            sublime.save_settings(SETTINGS_NAME)
            logger.info("Persisting settings with logging_root_level = %s", level)


class LoggingResetCommand(sublime_plugin.WindowCommand):
    """
    command key: logging_reset
    """

    def run(self):
        """
        Reset logging to match the logging configuration defined by settings file.
        For info on how logging works:
        * https://docs.python.org/3/howto/logging.html
        * https://docs.python.org/3/library/logging.html
        """
        reset_logging_system()
        sublime.status_message("Logging system has been reset.")


if int(sublime.version()) < 3000:
    # plugin_loaded() is not called automatically for ST 2.
    plugin_loaded()
