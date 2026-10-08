import argparse
import getpass
import json
import secrets
import sys

from teacher_auth import (
    PASSWORD_HASH_ITERATIONS,
    TEACHERS_FILE,
    hash_password,
    load_teacher_records,
)


def add_teacher(username: str) -> None:
    username = username.strip()
    if not username or any(character.isspace() for character in username):
        raise ValueError("Username must be non-empty and contain no whitespace")

    records = load_teacher_records()
    if username in records:
        raise ValueError(f"Teacher '{username}' already exists")

    password = getpass.getpass("Assigned password (minimum 12 characters): ")
    confirmation = getpass.getpass("Confirm password: ")
    if password != confirmation:
        raise ValueError("Passwords do not match")
    if len(password) < 12:
        raise ValueError("Password must be at least 12 characters")

    salt = secrets.token_bytes(16)
    records[username] = {
        "salt": salt.hex(),
        "password_hash": hash_password(password, salt),
        "iterations": PASSWORD_HASH_ITERATIONS,
    }
    TEACHERS_FILE.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    TEACHERS_FILE.chmod(0o600)
    print(f"Added teacher '{username}' to {TEACHERS_FILE}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage teacher login credentials")
    commands = parser.add_subparsers(dest="command", required=True)
    add_command = commands.add_parser("add", help="assign a password to a teacher")
    add_command.add_argument("username")
    arguments = parser.parse_args()

    try:
        add_teacher(arguments.username)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())