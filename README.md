# flow.launcher.plugin.used-by

![./assets/logo.png](./assets/logo.png)

> Find which applications are currently using a path

## Demonstration

![./assets/demo.gif](./assets/demo.gif)

## Installation

```shell
pm install Used-By by isnandar1471
```

## Features

- Find applications with absolute file/folder path or with regular expression (regex)
- Copy Name, CWD, Exe, & Create Time of the application
- Terminate / Kill the application

## How To Use

- `used <full path>`: Find applications using the specified path
- `used :r <regex>`: Find applications using the specified regex
- `used :i <case insensitive path>`: Find applications using the specified path in a case-insensitive manner
- `used :f <folder path>`: Find applications using the specified file/folder path

You can combine the options, for example:
- `used :ri <case insensitive regex>`: Find applications using the specified regex in a case-insensitive manner
- `used :ifr <case insensitive folder regex>`: Find applications using the specified file/folder path or regex in a case-insensitive manner

## Programming Language

- Python

## Dependencies

- flowlauncher
- psutil

## Tested On

- Windows 10
- Windows 11

## License

This project is licensed under the terms of the MIT license. See the [LICENSE](./LICENSE) file for details.
