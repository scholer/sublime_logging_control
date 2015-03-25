# sublime_loggging
This plugin for Sublime Text provides user-facing commands to enable and adjust
logging output using python's native logging module. Logging only works for
plugins that already uses the standard logging module.


# Configuration
Settings keys and default values:
    "logging_root_level": "DEBUG",
    "logging_console_enabled": True,
    "logging_console_fmt": "%(asctime)s %(levelname)-5s %(name)20s:%(lineno)-4s%(funcName)20s() %(message)s",
    "logging_console_datefmt": "%H:%M:%S",
    "logging_console_level": "INFO",
    "logging_file_enabled": False,
    "logging_file_fmt": "%(asctime)s %(levelname)-6s - %(name)s:%(lineno)s - %(funcName)s() - %(message)s",
    "logging_file_datefmt": "%Y%m%d-%H:%M:%S",
    "logging_file_level": "DEBUG",
    "logging_file_path": "sublime_output.log",
    "logging_file_rotating": True, # True will use RotatingFileHandler, otherwise FileHandler
    "logging_file_clear_on_reset": True,


You can open the settings file with:
    Preferences -> Package Settings -> Sublime Logging -> Settings--User


# Usage
Press ctrl+shift+p and start typing "Logging". Select the command you wish to invoke.


# Key binding
Key bindings can be used to create keyboard shortcuts for your favorite commands.
Open Default (Platform).sublime-keymap, which can be opened with either of:
    Preferences -> Package Settings -> Sublime Logging -> Key Bindings--User
    Preferences -> Key Bindings--User

Then edit the file to look similar to the following:
```
[
    { "keys": ["ctrl+alt+shift+t"], "command": "logging_toggle" },
    { "keys": ["ctrl+alt+shift+e"], "command": "logging_toggle", "args": {"enable": false} },
]
```

The commands list can be found in the Sublime_logging.sublime-commands (next to the default
Sublime_logging.sublime-settings file.)
