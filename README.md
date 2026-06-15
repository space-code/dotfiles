<h1 align="center" style="margin-top: 0px;">dotfiles</h1>

<p align="center">
<a href="https://github.com/space-code/dotfiles/blob/main/LICENSE"><img alt="Licence" src="https://img.shields.io/cocoapods/l/service-core.svg?style=flat"></a> 
</p>

## Description
Dotfiles are a collection of configuration files used to customize the command-line environment and development tools.

## 📋 Table of Contents

- [LLDB Commands](#lldb-commands)
    - [Custom Python Commands](#custom-python-commands)
    - [Useful Aliases & Regex Commands](#useful-aliases--regex-commands)
    - [Command Infrastructure](#command-infrastructure)
- [Installation](#installation)
- [Author](#author)
- [License](#license)

## LLDB Commands

This project enhances the LLDB debugging experience with custom Python commands, aliases, and a structured infrastructure.

### Custom Python Commands

| Command | Description | Arguments & Options |
| :--- | :--- | :--- |
| **`alcheck`** | Highlights `UIViews` with Auto Layout issues by outlining them in red. | `[-c color] [-w width]` |
| **`pdefaults`** | Dumps `NSUserDefaults` contents as a formatted key-value table. | `[-s suite] [-f filter] [-o]` |

### Useful Aliases & Regex Commands

A collection of shortcuts for common debugging tasks (defined in `cmds.txt`):

| Command | Description |
| :--- | :--- |
| **`reload_lldbinit`** | Reloads the `~/.lldbinit` file to apply changes without restarting LLDB. |
| **`rlook <regex>`** | Performs a regex-based image lookup (e.g., `rlook UIViewController`). |
| **`cp` / `cpo`** | Executes Objective-C expressions (with optional `-O` optimization). |
| **`sp` / `spo`** | Executes Swift expressions (with optional `-O` optimization). |
| **`lp` / `lpo` / `lpn`** | Executes expressions with a specified language (e.g., `lp swift <expr>`). |
| **`cpx` / `spx`** | Prints values in hexadecimal format for ObjC and Swift respectively. |
| **`doc <class>`** | Opens the official LLDB documentation for the specified class in your browser. |
| **`cpd` / `cpb` / `cpoo`** | Prints values in decimal, binary, or octal formats. |

### Command Infrastructure

The following files manage the loading and execution of custom commands:

| File | Description |
| :--- | :--- |
| **`lldbinit.py`** | The main entry point that dynamically registers Python commands and sources configuration files. |
| **`lldbbase.py`** | Provides the `BaseCommand` abstract class and expression evaluation utilities used by all custom commands. |
| **`cmds.txt`** | A plain text file containing LLDB alias and regex command definitions. |
| **`settings.txt`** | Contains global LLDB settings (e.g., `skip-prologue`). |

## Installation

```bash
./bootstrap.sh
```

## Author

**Nikita Vasilev**
- Email: [nv3212@gmail.com](mailto:nv3212@gmail.com)
- GitHub: [@ns-vasilev](https://github.com/ns-vasilev)

## License

dotfiles is available under the MIT license. See the LICENSE file for more info.

---

<div align="center">

**[⬆ back to top](#description)**

Made with ❤️ by [space-code](https://github.com/space-code)

</div>