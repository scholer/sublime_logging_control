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
* Logging behaviour can be adjusted in the sublime_logging.sublime-settings file.

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
import logging
import logging.handlers
logger = logging.getLogger(__name__)

SETTINGS_NAME = "sublime_logging.sublime-settings"
#on_modified_field = "auto_save_on_modified"
#delay_field = "auto_save_delay_in_seconds"


def plugin_loaded():
    """
    At importing time, plugins may not call any API functions, with the exception of
    sublime.version(), sublime.platform(), sublime.architecture() and sublime.channel().

    If a plugin defines a module level function plugin_loaded(), this will be called when
    the API is ready to use. Plugins may also define plugin_unloaded(), to get notified
    just before the plugin is unloaded.
    """
    if sublime.load_settings(SETTINGS_NAME).get("logging_enable_on_startup"):
        # load_settings doesn't seem to work??
        print("Invoking logging_reset ") #command...")
        #sublime.run_command("logging_reset")  # Commands doesn't work on start-up (at least not yet).
        reset_logging_system()
    else:
        print("Logging system not enabled on startup...")
        print("SETTINGS_NAME:", SETTINGS_NAME)
        settings = sublime.load_settings(SETTINGS_NAME)
        print('settings.has("logging_enable_on_startup"):', settings.has("logging_enable_on_startup"))
        print("Invoking logging_set_level command")
        sublime.run_command("logging_set_level", args={'level': 'DEBUG'})
        print("After")



def set_loglevel(level):
    """
    Set level of logging's root logger.
    level can be an integer or any of '
    """
    #if isinstance(level, str):
    #    level = getattr(logging, level.upper())
    ## Make sure we have an integer:
    #level = int(level)
    ## set root logger's level:
    #logging.getLogger().level = level

    # Edit: Just use logger.setLevel()
    logging.root.setLevel(level)


def reset_logging_system(settings=None):

    logger.info("Resetting logging system...")
    if settings is None:
        settings = sublime.load_settings(SETTINGS_NAME)
    # These SHOULD be available in the default sublime_logging.sublime-settings file, but still...
    defaults = {'logging_root_level': 'DEBUG',
                'logging_console_enabled': True,
                'logging_console_fmt': "%(asctime)s %(levelname)-5s %(name)20s:%(lineno)-4s%(funcName)20s() %(message)s",
                'logging_console_datefmt': "%H:%M:%S",
                'logging_console_level': 'INFO',
                'logging_file_enabled': False,
                'logging_file_fmt': "%(asctime)s %(levelname)-6s - %(name)s:%(lineno)s - %(funcName)s() - %(message)s",
                'logging_file_datefmt': "%Y%m%d-%H:%M:%S",
                'logging_file_level': 'DEBUG',
                'logging_file_path': 'sublime_output.log',
                'logging_file_rotating': True, # True will use RotatingFileHandler, otherwise FileHandler
                'logging_file_clear_on_reset': True,
               }
    def check_logfilepath(logfilepath):
        'logging_file_path'
        logfiledir = os.path.dirname(logfilepath)
        if not logfiledir:
            # os.getcwd() is usually Sublime Text base installation path. This may not be readable.
            packages_dir = sublime.packages_path()
            # Use <sublime-text data dir>/logs/ as default directory for file logs.
            logfiledir = os.path.join(os.path.abspath(os.path.dirname(packages_dir)), 'logs')
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
        settings_key = cfgkeyfmt.format(key)
        return settings.get(settings_key,
                            defaults.get(settings_key, default))

    if settings.get("logging_use_basicConfig"):
        print("Initializing logging system using basicConfig...")
        filepath = (settings.get("logging_file_enabled") and settings.get("logging_file_path")) or None
        if filepath:
            print("Logging output to file:", filepath)
        if logging.root.handlers:
            print("NOTE: logging system already initialized. This command will not have any effect!")
            print("(set logging_use_basicConfig: false if you want this plugin to seize control of logging output configuration)")
        logging.basicConfig(level=settings.get('logging_root_level'),
                            format=settings.get('logging_console_fmt'),
                            datefmt=settings.get('logging_console_datefmt'),
                            filename=filepath)
        logger.info("Logging system has been started using basicConfig.")

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
            cfg = partial(get_config, cfgkeyfmt="logging_%s_{}" % output)
            if not cfg('enabled'):
                continue
            if output == 'console':
                handler = logging.StreamHandler()
            else:
                logfilepath = cfg('path')
                logfilepath = check_logfilepath(logfilepath)
                if cfg('rotating'):
                    # Use rotating file handler with 3 logfiles each maxing out / rotating at 2 MB:
                    handler = logging.handlers.RotatingFileHandler(logfilepath, maxBytes=2*2**20, backupCount=3)
                else:
                    handler = logging.FileHandler(logfilepath)
            formatter = logging.Formatter(fmt=cfg('fmt'), datefmt=cfg('datefmt'))
            handler.setFormatter(formatter)
            # There are two places where the 'level' is evaluated:
            # (a) In the logger.
            # (b) In the handler.
            # If the call's level is >= the logger's level, it is passed to the logger's handlers.
            # If the call's level is >= the handler's level, it is emitted.
            # Typically, the level is adjusted in the logger, and the handler's level is set to 0.
            if cfg('level'):
                handler.setLevel(cfg('level'))
            logging.root.addHandler(handler)

        # Set root logger's level:
        logging.root.setLevel(settings.get('logging_root_level', defaults['logging_root_level']))
        logger.info("Logging system has been reset.")



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
        print('settings.has("logging_enable_on_startup"):', settings.has("logging_enable_on_startup"))
        if enable is None:
            enable = not settings.get('logging_is_enabled', True)

        if enable:
            if logging.root.handlers:
                # We already have loggers defined:
                level = settings.get('logging_root_level', logging.DEBUG)
                logging.root.setLevel(level)
                logger.info("Logging level set to %s", level)
            else:
                # Set up logging: (will run after this command has completed...)
                self.window.run_command("logging_reset")
            sublime.status_message("Logging Turned On (level=%s)" %
                                   logging.getLevelName(level) if isinstance(level, int)
                                   else level)
        else:
            # Uh, how? Probably just increase the root logger's level to sufficiently high number.
            level = 50
            logger.info("Setting logging level to %s", level)
            logging.root.level = level
            sublime.status_message("Logging Turned Off (entirely)")

        settings.set('logging_is_enabled', enable)


class LoggingSetLevelCommand(sublime_plugin.WindowCommand):
    """
    command key: logging_set_level
    """

    def run(self, level):
        """
        Set logging level.
        """
        logging.root.setLevel(level)
        sublime.status_message("Logging level set to %s" % level)
        print("Logging level set to %s" % level)
        logger.info("Logging level set to %s", level)



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
