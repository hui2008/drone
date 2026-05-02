# VS Code `launch.json` Notes for GDB

## Contents

- [References](#references)
- [How This Debug Setup Works](#how-this-debug-setup-works)
- [glibc Source Warning](#glibc-source-warning)
- [Fix Options](#fix-options)
- [`launch.json` Field Reference](#launchjson-field-reference)
- [Common `setupCommands`](#common-setupcommands)
- [Recommendation](#recommendation)

## References

- VS Code C/C++ `launch.json` reference: <https://code.visualstudio.com/docs/cpp/launch-json-reference>
- Related Visual Studio C++ launch schema reference: <https://learn.microsoft.com/en-us/cpp/build/launch-vs-schema-reference-cpp>

## How This Debug Setup Works

`launch.json` is a VS Code debug configuration file. Each object in `configurations` appears as a selectable debug target in the Run and Debug dropdown.

This configuration uses:

```json
"type": "cppdbg"
```

That tells VS Code to use the Microsoft C/C++ debugger extension. The extension then launches GDB because the config also uses:

```json
"MIMode": "gdb",
"miDebuggerPath": "/usr/bin/gdb"
```

## glibc Source Warning

You may see:

```text
Could not load source './csu/../sysdeps/nptl/libc_start_call_main.h':
'SourceRequest' not supported.
```

This means GDB stopped inside glibc startup code, but VS Code/GDB cannot find the matching glibc source file.

### What `csu` and `nptl` Mean

`csu` means C startup. It is glibc code that runs before your program's `main`.

`nptl` means Native POSIX Thread Library. It is glibc's POSIX thread implementation, used by APIs such as `pthread_create`, `pthread_mutex_lock`, and `pthread_join`.

This path:

```text
./csu/../sysdeps/nptl/libc_start_call_main.h
```

resolves to:

```text
glibc/sysdeps/nptl/libc_start_call_main.h
```

That file is part of glibc's path for calling your program's `main`.

## Fix Options

### Option 1: Avoid glibc Startup Code

For normal application debugging, do not stop before `main`:

```json
"stopAtEntry": false
```

Then set breakpoints in your own source files.

### Option 2: Install glibc Source

Use this only if you specifically want to step into glibc internals.

```bash
sudo apt update
sudo apt install glibc-source
cd /usr/src/glibc
sudo tar xf glibc-*.tar.xz
```

Then add this to `setupCommands`:

```json
{
  "description": "Find glibc sources",
  "text": "set directories /usr/src/glibc/glibc-2.39:/usr/src/glibc/glibc-2.39/csu:/usr/src/glibc/glibc-2.39/sysdeps/nptl:$cdir:$cwd",
  "ignoreFailures": true
}
```

## `launch.json` Field Reference

### Top-Level Fields

| Field | Meaning |
| --- | --- |
| `version` | VS Code debug configuration schema version. Usually `0.2.0`. |
| `configurations` | List of debug configurations shown in the Run and Debug dropdown. |

### General Debug Fields

These are common VS Code debug fields.

| Field | Example | Meaning |
| --- | --- | --- |
| `name` | `"(gdb) Launch"` | Display name in VS Code's debug dropdown. |
| `type` | `"cppdbg"` | Selects the Microsoft C/C++ debugger extension. |
| `request` | `"launch"` | Starts a new debugged process. Use `attach` to connect to an already-running process. |
| `program` | `"${workspaceFolder}/my/basic/build/hello-world"` | Executable to debug. |
| `args` | `[]` | Command-line arguments passed to the program. |
| `cwd` | `"${workspaceFolder}/my/basic/build"` | Working directory for the debugged program. Relative paths resolve from here. |
| `environment` | `[]` | Environment variables for the debugged program. |

`${workspaceFolder}` expands to the workspace root, here `/workspaces/uav`.

Example `args`:

```json
"args": ["--verbose", "input.txt"]
```

Example `environment`:

```json
"environment": [
  {
    "name": "DEBUG",
    "value": "1"
  }
]
```

### C/C++ Extension Fields

These fields are interpreted by the Microsoft C/C++ debugger extension because `type` is `cppdbg`.

| Field | Example | Meaning |
| --- | --- | --- |
| `stopAtEntry` | `false` | If `true`, pauses as soon as the process starts, often before `main`. |
| `externalConsole` | `false` | If `false`, use VS Code's integrated console or terminal. If `true`, open a separate console. |
| `MIMode` | `"gdb"` | Selects the Machine Interface debugger backend. `MI` means Machine Interface, not Microsoft. GDB/MI is the structured protocol VS Code uses to control GDB. Common values are `gdb` and `lldb`. |
| `miDebuggerPath` | `"/usr/bin/gdb"` | Path to the actual debugger executable. |
| `setupCommands` | `[]` | Commands sent to GDB before debugging starts. |

### `setupCommands` Shape

Each setup command can contain:

```json
{
  "description": "Human-readable label",
  "text": "GDB or GDB/MI command",
  "ignoreFailures": true
}
```

| Field | Meaning |
| --- | --- |
| `description` | Label for humans reading the config. |
| `text` | The command sent to GDB. |
| `ignoreFailures` | If `true`, continue debugging even if this setup command fails. |

## Common `setupCommands`

### Pretty Printing

```json
{
  "description": "Enable pretty-printing for gdb",
  "text": "-enable-pretty-printing",
  "ignoreFailures": true
}
```

Improves display of C++ types like `std::string`, `std::vector`, and `std::map`.

### Intel Disassembly Syntax

```json
{
  "description": "Set Disassembly Flavor to Intel",
  "text": "-gdb-set disassembly-flavor intel",
  "ignoreFailures": true
}
```

Shows assembly in Intel syntax instead of AT&T syntax.

## Recommendation

For normal C/C++ application debugging:

```json
"stopAtEntry": false
```

Set breakpoints in your own source files. Configure glibc sources only if you specifically need to step into system startup code.
