# Usage

On startup Enki will connect to the specified broker and subscribe to spBv1.0/#.

Enki will then monitor the EoNs and devices that get born or die on the broker.

## Command line options

Command line options are self documented.
Their help can be seen by running enki with the option```-h``` or ```--help```.

## Basic commands
The list of available commands can be accessed with the command ```help```.

Additional help on each command can be seen with ```help <command>```.

## Advanced usage
### Sending null metrics
When prompted for a metric value, you can specify you want to send the metric with the null flag set to true,
by pressing ```Ctrl-d```.

### Application Settings
The following settings can be set with the command ```set <setting_name> <value>```.

- **byte_data_display_mode** _list_ or _hexdump_:
  - _list_: The bytes will be displayed as a python list (e.g. [0x01, 0x02, 0x03])
  - _hexdump_: The bytes will be displayed using a hexadecimal dump format, similar to the output of the xxd command
- **byte_data_max_len**: The maximum number of bytes to display for either display mode. Set this to 0 to remove the limit and display all bytes.
