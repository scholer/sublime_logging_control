# Logging Control: Logging plugin for Sublime Text
This plugin for Sublime Text provides user-facing commands to enable and adjust
logging output using python's native logging module. Logging only works for
plugins that already uses the standard logging module.

This plugin enables the user to customize:
* How to display logging messages
* Whether to save save logging messages to a file
* What types of logging messages (the severity level) are displayed/written to file (DEBUG/INFO/WARNING/FATAL messages).
The user can adjust the logging level on-the-fly using ctrl+shift+p and selecting the desired level.


### What's the difference between displaying messages with logging library vs normal print()?
Typically, **print()** is intended to show information to the user *right there* in the console,
showing only relevant information to the user.

Logging messages on the other hand is typically created to allow the user (or developer) to figure out
what is going on as part of the normal flow of the program. Logging messages are often used retrospectively,
looking back at the messages prited over time to see what happened when by what piece of code/plugin.
Logging messages should thus have a time-stamp and identifiers to tell where the message originated from (what plugin).
If the user wants to parse logging output, it is convenient if this logging output is formatted the same way.
(Rather than having each plugin developer using his or her own logging format).

Using the logging module is a best-practice for all python code wanting to produce logging messages, especially libraries.
Since plugins for SublimeText can be considered "libraries" (in that they are not intended for direct consumption),
using python's logging library could be an appropriate way to output log messages.


## Use case scenario:
I developed this plugin because I wanted to debug the behaviour of the [auto-save](https://packagecontrol.io/packages/auto-save) plugin.
I was having issues with dropbox conflicts when a file in my dropbox was opened in Sublime Text on two different computers,
both instances having auto-save turned on.
I wanted the plugin to *temporarily* print a (time-stamped) message whenever the auto-save plugin would save the file.
However, I didn't want to modify the plugin to *always* print this message - that would produce way too many messages,
flooding the user's console.


## What this plugin is not
This plugin is not intended to grab *all* console output and save it to a file.
That functionality is provided by e.g. the [SublimeLog](https://packagecontrol.io/packages/SublimeLog) plugin.
*The difference:* Logging Control focuses exclusively on logging messages via the standard python logging library.
Using the logging library developers does not have to worry about whether producing a debug/info message
will flood the user's console. The developer can produce as many logging messages as he/she thinks is needed,
but reserve use of print() to when the developer actually wants to display a message to the user's console.
The user can choose to direct all logging messages to a file, keeping the console output clean.
The user can also choose to output logging messages to the console on a as-needed basis (or permanently, if
the user likes to see what is going on all the time).

Logging Control is also not intended to control logging of *user input*.
User-invoked commands and key-presses can be controlled with the [Verbose](https://packagecontrol.io/packages/Verbose)
plugin, or switched on/off directly through the ```log_*``` API methods.




## Configuration
Settings keys and default values - overview:
```
"logging_root_level": "INFO",
"logging_persist_changes": false,
"logging_enable_on_startup": true,
"logging_use_basicConfig": false,
"logging_console_enabled": true,
"logging_console_fmt": "%(asctime)s %(levelname)-5s %(name)20s:%(lineno)-4s%(funcName)20s() %(message)s",
"logging_console_datefmt": "%H:%M:%S",
"logging_console_level": "DEBUG",
"logging_file_enabled": false,
"logging_file_fmt": "%(asctime)s %(levelname)-6s - %(name)s:%(lineno)s - %(funcName)s() - %(message)s",
"logging_file_datefmt": "%Y%m%d-%H:%M:%S",
"logging_file_level": "DEBUG",
"logging_file_path": "sublime_output.log",
"logging_file_rotating": true,
"logging_file_clear_on_reset": false
```

Controlling output:
* ```logging_console_enabled``` and ```logging_file_enabled``` controls whether logging messages are written to the console and/or file respectively.
* ```logging_console/file_fmt``` setting controls how logging messages are formatted for console and file output respectively.
* ```logging_console/file_datefmt``` setting controls how the timestamps are formatted for console and file output respectively.
* ```logging_file_path``` is used to specify the file to write logging messages to, if logging_file_enabled is set to true.
* ```logging_file_rotating``` can be set to true in order to use a "rotating" log-file scheme.

Controlling behaviour:
* ```logging_persist_changes```: If the user sets logging level (to DEBUG/INFO/etc), remember this level after exit.
* ```logging_enable_on_startup```: Enable logging when the
* ```logging_use_basicConfig```: can be used to ensure that the plugin will not re-set the logging system if the logging system has been initialized by other packages.

Controlling what logging types are printed (what level):
* ```logging_root_level``` controls the lowest severity that is ever considered.
* ```logging_console_level``` can be increased to only print messages with at least this level to the console.
* ```logging_file_level``` can be increased to only print messages with at least this level to the log file.

*Example:* You want to print ALL debug messages to a log file, but only show the most severe messages in the console:
```
"logging_use_basicConfig": false,
"logging_console_enabled": true,
"logging_file_enabled": true,
"logging_root_level": "DEBUG",
"logging_console_level": "WARNING",     # Only print warning log messages in the console.
"logging_file_level": "DEBUG"           # But write DEBUG messages to the log file.
```
*Note:* Using different levels for console and file output is only supported with ```logging_use_basicConfig``` set to false.
Also, if ```logging_root_level``` is set to "INFO", only "INFO" messages are printed, even if ```logging_file_level``` is set to "DEBUG".


You can open the user-editable settings file with:
```
    Preferences -> Package Settings -> Logging Control -> Settings - User
```

## Usage
Press ctrl+shift+p and start typing "Logging". Select the command you wish to invoke.
* ```"Logging: Disable logging"``` - will disable logging (by setting logging_root_level to a very high level).
* ```"Logging: Enable logging"``` - will enable logging, initializing the logging system if it hasn't already been initialized.
* ```"Logging: Toggle logging"``` - will toggle logging on/off.
* ```"Logging: Level = %LEVEL%"``` - will set logging_root_level to %LEVEL%.
* ```"Logging: Reset logging system"``` - will reset the logging system (in case something has gone wrong).


## Key binding
Key bindings can be used to create keyboard shortcuts for your favorite commands.
Open ```Default (Platform).sublime-keymap```, which can be opened with either of:
```
    Preferences -> Package Settings -> Logging Control -> Key Bindings--User
    Preferences -> Key Bindings--User
```

Then edit the file to look similar to the following:
```
[
    { "keys": ["ctrl+alt+shift+t"], "command": "logging_toggle" },
    { "keys": ["ctrl+alt+shift+e"], "command": "logging_toggle", "args": {"enable": false} },
]
```

The commands list can be found in the ```logging_control.sublime-commands``` (next to the default
```logging_control.sublime-settings``` file.)
