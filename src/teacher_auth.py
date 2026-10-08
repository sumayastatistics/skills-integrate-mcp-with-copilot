import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from pathlib import Path

from fastapi import Request


TEACHERS_FILE = Path(__file__).with_name("teachers.json")
SESSION_SECRET_FILE = Path(__file__).with_name(".session_secret")
SESSION_COOKIE_NAME = "teacher_session"
SESSION_DURATION_SECONDS = 8 * 60 * 60
PASSWORD_HASH_ITERATIONS = 310_000


def load_teacher_records() -> dict:
    if not TEACHERS_FILE.exists():
        return {}

    try:
        records = json.loads(TEACHERS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("Teacher credentials file is unreadable or invalid") from error

    if not isinstance(records, dict):
        raise ValueError("Teacher credentials file must contain a JSON object")
    return records


def hash_password(password: str, salt: bytes) -> str:
    password_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_HASH_ITERATIONS
    )
    return password_hash.hex()


def authenticate_teacher(username: str, password: str) -> bool:
    try:
        record = load_teacher_records().get(username)
        if not isinstance(record, dict):
            return False
        salt = bytes.fromhex(record["salt"])
        expected_hash = record["password_hash"]
        iterations = record.get("iterations", PASSWORD_HASH_ITERATIONS)
        if (
            not isinstance(expected_hash, str)
            or not isinstance(iterations, int)
            or iterations < 1
        ):
            return False
    except (KeyError, TypeError, ValueError):
        return False

    actual_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, iterations
    ).hex()
    return hmac.compare_digest(actual_hash, expected_hash)


def _get_session_secret() -> bytes:
    configured_secret = os.environ.get("SESSION_SECRET")
    if configured_secret:
        return configured_secret.encode("utf-8")

    try:
        return SESSION_SECRET_FILE.read_bytes()
    except FileNotFoundError:
        secret = secrets.token_bytes(32)
        try:
            with SESSION_SECRET_FILE.open("xb") as secret_file:
                secret_file.write(secret)
            SESSION_SECRET_FILE.chmod(0o600)
            return secret
        except FileExistsError:
            return SESSION_SECRET_FILE.read_bytes()


def create_session_token(username: str) -> str:
    expires_at = int(time.time()) + SESSION_DURATION_SECONDS
    payload = f"{username}\n{expires_at}".encode("utf-8")
    encoded_payload = base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")
    signature = hmac.new(
        _get_session_secret(), encoded_payload.encode("ascii"), hashlib.sha256
    ).hexdigest()
    return f"{encoded_payload}.{signature}"


def get_session_teacher(token: str | None) -> str | None:
    if not token:
        return None

    try:
        encoded_payload, signature = token.split(".", 1)
        expected_signature = hmac.new(
            _get_session_secret(), encoded_payload.encode("ascii"), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(signature, expected_signature):
            return None

        padding = "=" * (-len(encoded_payload) % 4)
        username, expires_at = base64.urlsafe_b64decode(
            encoded_payload + padding
        ).decode("utf-8").split("\n", 1)
        if int(expires_at) <= int(time.time()):
            return None
        return username
    except (ValueError, UnicodeDecodeError):
        return None


def session_cookie_secure(request: Request) -> bool:
    return request.url.scheme == "https" or os.environ.get("COOKIE_SECURE") == "true"