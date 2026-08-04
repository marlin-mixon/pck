import sys
import os
import json
import base64


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
            (entry.get("encoding") or "text").strip().lower()
        )

    return None, None, None


def unpack_project():

    force = any(arg.lower() in ("-f", "--force") for arg in sys.argv[1:])

    try:

        input_data = sys.stdin.read()

        if not input_data.strip():
            print("Error: No data received via stdin.", file=sys.stderr)
            sys.exit(1)

        files_to_create = json.loads(input_data)

        if not isinstance(files_to_create, list):
            print("Error: Expected a JSON array at root.", file=sys.stderr)
            sys.exit(1)

        #
        # Pass 1 - validate entries and look for files that already exist
        #

        overwrite_list = []

        for file_info in files_to_create:

            path, contents, encoding = parse_entry(file_info)

            if not path:
                print("Warning: Invalid entry. Skipping.", file=sys.stderr)
                continue

            # Directories don't overwrite files
            if contents is None:
                continue

            normalized = path.replace("\\", "/")

            if os.path.exists(normalized):
                overwrite_list.append(normalized)

        if overwrite_list and not force:

            print(
                "The following files already exist and would be overwritten:\n",
                file=sys.stderr
            )

            for filename in overwrite_list:
                print(f"  {filename}", file=sys.stderr)

            print(
                f"\n{len(overwrite_list)} file(s) would be overwritten.",
                file=sys.stderr
            )

            print(
                "Run again with -f to force overwriting existing files.",
                file=sys.stderr
            )

            sys.exit(2)

        #
        # Pass 2 - write everything
        #

        for file_info in files_to_create:

            path, content, encoding = parse_entry(file_info)

            if not path:
                continue

            write_entry(path, content, encoding)

        print("\nSuccessfully unpacked all project files.")

    except json.JSONDecodeError as je:
        print(f"JSON Parsing Error: {je}", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)


def write_entry(relative_path, contents, encoding="text"):

    normalized_path = relative_path.replace("\\", "/")

    #
    # Directory
    #
    if contents is None:

        os.makedirs(normalized_path.rstrip("/"), exist_ok=True)
        print(f"Created directory: {normalized_path}")
        return

    directory = os.path.dirname(normalized_path)

    if directory:
        os.makedirs(directory, exist_ok=True)

    if encoding == "text":

        with open(
            normalized_path,
            "w",
            encoding="utf-8",
            newline="\n"
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


if __name__ == "__main__":
    unpack_project()
