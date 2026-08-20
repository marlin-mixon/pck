import argparse
import base64
import json
import os
import sys

import pyperclip


def parse_entry(entry):
    """
    Returns (path, content, encoding)

    Expected object format:
        {
            "path": "...",
            "content": "...",
            "encoding": "base64"
        }

    "encoding" is optional and defaults to "text".
    """
    if isinstance(entry, dict):
        return (
            entry.get("path"),
            entry.get("content"),
            (entry.get("encoding") or "text").strip().lower(),
        )
    return None, None, None


def get_target_path(target_dir, relative_path):
    """
    Normalizes slashes and safely joins target_dir with relative_path,
    ensuring leading slashes do not break out of target_dir.
    """
    clean_rel = relative_path.replace("\\", "/").lstrip("/")
    return os.path.join(target_dir, clean_rel)


def write_entry(target_dir, relative_path, contents, encoding="text"):
    normalized_path = get_target_path(target_dir, relative_path)

    # Directory
    if contents is None:
        os.makedirs(normalized_path.rstrip("/"), exist_ok=True)
        print(f"Created directory: {normalized_path}")
        return

    directory = os.path.dirname(normalized_path)
    if directory:
        os.makedirs(directory, exist_ok=True)

    if encoding == "text":
        with open(
            normalized_path, "w", encoding="utf-8", newline="\n"
        ) as f:
            f.write(contents)
    elif encoding == "base64":
        try:
            binary = base64.b64decode(contents)
        except Exception as ex:
            raise ValueError(
                f"Invalid base64 content for '{normalized_path}': {ex}"
            )

        with open(normalized_path, "wb") as f:
            f.write(binary)
    else:
        raise ValueError(
            f"Unsupported encoding '{encoding}' for '{normalized_path}'"
        )

    print(f"Created: {normalized_path}")


def validate_payload(files_to_create):
    """
    Confirms the parsed JSON is a list of dict entries with a usable
    'path' key. Returns (is_valid, error_message).
    """
    if not isinstance(files_to_create, list):
        return False, "Expected a JSON array at the root."

    if not files_to_create:
        return False, "JSON array is empty - nothing to unpack."

    for entry in files_to_create:
        path, _, _ = parse_entry(entry)
        if not path:
            return False, "Found an entry with no 'path' key."

    return True, None


def summarize_payload(files_to_create):
    """
    Returns (file_paths, dir_paths) for preview/confirmation display.
    """
    file_paths = []
    dir_paths = []

    for entry in files_to_create:
        path, contents, _ = parse_entry(entry)
        if not path:
            continue
        if contents is None:
            dir_paths.append(path)
        else:
            file_paths.append(path)

    return file_paths, dir_paths


def check_overwrites(files_to_create, target_dir, force):
    """
    Checks if any files will be overwritten. If so and force is False,
    prints the list of existing files to stderr and exits with code 2.
    """
    overwrite_list = []

    for file_info in files_to_create:
        path, contents, _ = parse_entry(file_info)

        if not path or contents is None:
            continue

        target_path = get_target_path(target_dir, path)
        if os.path.exists(target_path):
            overwrite_list.append(target_path)

    if overwrite_list and not force:
        print(
            "The following files already exist and would be overwritten:\n",
            file=sys.stderr,
        )
        for filename in overwrite_list:
            print(f"  {filename}", file=sys.stderr)

        print(
            f"\n{len(overwrite_list)} file(s) would be overwritten.",
            file=sys.stderr,
        )
        print(
            "Run again with -f to force overwriting existing files.",
            file=sys.stderr,
        )
        sys.exit(2)


def read_json_from_clipboard():
    """
    Interactive loop: prompts the user to copy JSON to the clipboard,
    reads it on Enter, and validates it. Returns a parsed list, or
    None if the user quits.
    """
    print("pck-utils: waiting for JSON on your clipboard...\n")
    print("  1. Copy your .pck JSON (e.g. from an LLM response)")
    print("  2. Press Enter here to unpack it")
    print("  3. Or type 'q' + Enter to quit\n")

    while True:
        response = input("> ").strip().lower()

        if response in ("q", "quit", "exit"):
            print("Cancelled. Nothing was written.")
            return None

        try:
            raw = pyperclip.paste()
        except Exception as ex:
            print(
                f"Could not read clipboard: {ex}\n"
                "Copy your JSON and press Enter to try again, or 'q' to quit.\n",
                file=sys.stderr,
            )
            continue

        if not raw or not raw.strip():
            print(
                "Clipboard is empty.\n"
                "Copy your JSON and press Enter to try again, or 'q' to quit.\n"
            )
            continue

        try:
            files_to_create = json.loads(raw)
        except json.JSONDecodeError as je:
            print(
                f"Clipboard doesn't look like valid JSON ({je}).\n"
                "Copy your JSON and press Enter to try again, or 'q' to quit.\n"
            )
            continue

        is_valid, error_message = validate_payload(files_to_create)

        if not is_valid:
            print(
                f"Clipboard JSON doesn't look like pck output: {error_message}\n"
                "Copy your JSON and press Enter to try again, or 'q' to quit.\n"
            )
            continue

        return files_to_create


def confirm_unpack(files_to_create, target_dir):
    """
    Shows a preview of what will be created and asks for confirmation.
    Returns True to proceed, False to abort.
    """
    file_paths, dir_paths = summarize_payload(files_to_create)

    total_dirs = len(dir_paths)
    print(
        f"\nFound {len(file_paths)} file(s)"
        + (f" and {total_dirs} director(y/ies)" if total_dirs else "")
        + ":"
    )

    for path in file_paths:
        print(f"  {path}")
    for path in dir_paths:
        print(f"  {path}")

    display_target = target_dir if target_dir != "." else "current directory (.)"
    answer = input(f"\nUnpack into {display_target}? [Y/n]: ").strip().lower()

    return answer in ("", "y", "yes")


def do_unpack(files_to_create, target_dir, force):
    """
    Shared write logic used by both stdin and clipboard modes.
    """
    # Create target directory structure if it doesn't exist
    if not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)
        print(f"Created target directory: {target_dir}")

    # Check overwrites (will exit(2) if files exist and force is False)
    check_overwrites(files_to_create, target_dir, force)

    # Write everything
    for file_info in files_to_create:
        path, content, encoding = parse_entry(file_info)

        if not path:
            continue

        write_entry(target_dir, path, content, encoding)

    print("\nSuccessfully unpacked all project files.")


def unpack_project():
    parser = argparse.ArgumentParser(
        description="Unpack a JSON-formatted project structure from stdin "
        "or your clipboard."
    )
    parser.add_argument(
        "target_dir",
        nargs="?",
        default=".",
        help="Target directory to unpack into (default: current directory)",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Force overwrite of existing files",
    )
    parser.add_argument(
        "-c",
        "--clipboard",
        action="store_true",
        help="Read JSON from the clipboard interactively, even if stdin is piped",
    )
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip the confirmation prompt in clipboard mode",
    )

    args = parser.parse_args()
    target_dir = args.target_dir
    force = args.force

    use_clipboard = args.clipboard or sys.stdin.isatty()

    try:
        if use_clipboard:
            files_to_create = read_json_from_clipboard()

            if files_to_create is None:
                sys.exit(0)

            # Check for existing files BEFORE confirming
            check_overwrites(files_to_create, target_dir, force)

            if not args.yes:
                if not confirm_unpack(files_to_create, target_dir):
                    print("Cancelled. Nothing was written.")
                    sys.exit(0)

        else:
            input_data = sys.stdin.read()

            if not input_data.strip():
                print("Error: No data received via stdin.", file=sys.stderr)
                sys.exit(1)

            try:
                files_to_create = json.loads(input_data)
            except json.JSONDecodeError as je:
                print(f"JSON Parsing Error: {je}", file=sys.stderr)
                sys.exit(1)

            is_valid, error_message = validate_payload(files_to_create)

            if not is_valid:
                print(f"Error: {error_message}", file=sys.stderr)
                sys.exit(1)

        do_unpack(files_to_create, target_dir, force)

    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    unpack_project()