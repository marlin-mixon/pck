# pck

A simple pair of Python utilities that 1. Packs a project directory into a single uncompressed JSON document.  2. Unpacks or reconstructs a project based on the JSON array describing the files and directories.

This tool makes it quick and easy to pass context to and from LLMs.  It is designed for AI-assisted development workflows where an LLM generates an entire project as structured JSON. The json_to_directory utility reads the JSON from **stdin** and recreates the corresponding directory structure and files on disk.  The directory_to_json reverses the process.  It creates a JSON file based on the contents of the starting directory and dives into the directory structure finding all files and stores them in a single JSON file.

## pck command Features

- Creates directories and files from a JSON document
- Automatically creates parent directories as needed
- Uses UTF-8 encoding
- Writes files with Unix (LF) line endings
- Refuses to overwrite existing files by default
- Lists all conflicting files before making any changes
- Supports `-f`, or `--force` options to force overwriting existing files
- Simple, dependency-free implementation using the Python standard library

## unpck command Features

- Creates two types of JSON files based on a directory structure.
- Default format type 1 is JSON array of objects.  This is easiest for humans to read and easily handled by LLMs
- This JSON format is a simple array and is only a single level deep.  Directory structure and depth is implied by the path elements.
- Writes JSON to STDOUT.  Redirect as needed


## JSON Format

Example of pck's JSON object format -- an array of JSON objects:

Each element contains:

- `path` – Relative path to a file or directory
- `content` – File contents (omitted or `null` for directories)
- `encoding` - Optional for identifying binary files.  Only valid entry is case-inensitive "base64".

```json
[
  {
    "path": "README.md",
    "content": "# My Project\n"
  },
  {
    "path": "src/",
    "content": null
  },
  {
    "path": "src/main.py",
    "content": "print('Hello, world!')\n"
  }.
  {
    "path": "assets/image.png",
    "encoding": "base64",
    "content": "iVBORw0KGgoAAAANSUhEUgAA..."
]
```

Directories are identified by a trailing `/`.  Note that defining directories in this way is optional and only required for creating empty directories.


## Usage

### Basic directory creation from a JSON file using JSON array of objects .pck file

```bash
Simplest form:
unpck
```
unpck will use whatever is in your clipboad or let you copy and then paste directly into unpck.

```bash
Simple form:
unpck < project.pck

Provide optional subdirectory to unpack into.  If directory does not exist the path will be created:
unpck sub1/sub2 < project.pck
```

If existing files are found, the utility will stop before writing anything and display a list of conflicts.

Example:

```
ERROR: 4 existing files would be overwritten:

  README.md
  src/main.py
  src/utils.py
  requirements.txt

Nothing has been written.

Run again with -f to overwrite these files.
```
### As above but with force overwrite

```bash
unpck -f < project.pck

(use switches -f, --force as desired)
```

### Basic JSON creation from a directory structure

```bash
Simple form:
pck > project.pck

Provide optional starting directory:
pck sub1/sub2 > project2.pck
```

## Why this exists

Large Language Models often require full directory context in order to assist you in updating existing projects.  However, it can be a pain to hunt down, cut and paste the several files needed for context. The directory_to_json.py helps you do that in one command.  Conversely, when creating new projects like web sites or docker-compose projects, Large Language Models will typically generate a lot of documents that are a pain to copy and paste each into the appropriate directory structure without taking time plus you risk making mistakes. By first requesting the LLM to put the generated files into JSON and then using the json_t_directory.py you can solve this problem with a single command. These utilities provides a safe and simple way to pack and unpack your projects with adequate protections that protect existing work from accidental overwrites. 

## Requirements

- Python 3.7 or later
- No third-party dependencies

## Installation

```bash
pip install pck-utils
```

## Version

0.2.1, 12-Aug-2026

## Release Notes

Added an easy clipboard paste feature for unpck allowing you to go from copying to clibboard to pasting directly into unpck.

## License

MIT License
