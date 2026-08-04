import os
import json
import sys
import base64
import argparse


def scan_directory(target_dir, base_dir=None, minimize=False):
    result = []

    ignored_dirs = {
        ".git",
        "__pycache__",
        "node_modules",
        ".venv",
        "venv"
    }

    if base_dir is None:
        base_dir = os.getcwd()

    for root, dirs, files in os.walk(target_dir):

        # Skip ignored directories
        dirs[:] = [d for d in dirs if d not in ignored_dirs]

        # Record empty directories
        if not dirs and not files:
            dir_path = (
                os.path.relpath(root, base_dir)
                .replace(os.sep, "/")
                + "/"
            )

            if minimize:
                result.append([dir_path])
            else:
                result.append({
                    "path": dir_path,
                    "content": None
                })

        # Record files
        for file in files:

            full_path = os.path.join(root, file)

            path = os.path.relpath(
                full_path,
                base_dir
            ).replace(os.sep, "/")

            try:
                with open(full_path, "rb") as f:
                    data = f.read()

                text = None

                # Files containing NUL bytes are almost certainly binary.
                if b"\x00" in data:
                    is_binary = True
                else:
                    try:
                        text = data.decode("utf-8")

                        # Normalize all line endings to Unix format.
                        text = text.replace("\r\n", "\n").replace("\r", "\n")

                        is_binary = False
                    except UnicodeDecodeError:
                        is_binary = True

                if is_binary:
                    encoded = base64.b64encode(data).decode("ascii")

                    if minimize:
                        result.append([path, "b", encoded])
                    else:
                        result.append({
                            "path": path,
                            "encoding": "base64",
                            "content": encoded
                        })
                else:
                    if minimize:
                        result.append([path, text])
                    else:
                        result.append({
                            "path": path,
                            "content": text
                        })

            except PermissionError:
                print(
                    f"Warning: Permission denied reading '{path}'. Skipping.",
                    file=sys.stderr
                )

            except OSError as ex:
                print(
                    f"Warning: Could not read '{path}': {ex}",
                    file=sys.stderr
                )

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Recursively convert a directory into JSON."
    )

    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to scan (default: current directory)"
    )

    parser.add_argument(
        "-m",
        "--minimize",
        action="store_true",
        help="Minimize JSON for LLM consumption."
    )

    args = parser.parse_args()

    project_dir = args.directory

    if not os.path.exists(project_dir):
        print(
            f"Error: The directory '{project_dir}' does not exist.",
            file=sys.stderr
        )
        sys.exit(1)

    file_data = scan_directory(
        project_dir,
        os.getcwd(),
        minimize=args.minimize
    )

    if args.minimize:
        print(json.dumps(file_data, separators=(",", ":")))
    else:
        print(json.dumps(file_data, indent=2))


if __name__ == "__main__":
    main()
