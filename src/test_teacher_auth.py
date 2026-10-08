import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException
from starlette.requests import Request

import teacher_auth
from app import require_teacher


class TeacherAuthTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.credentials_file = Path(self.temp_directory.name) / "teachers.json"
        self.secret_file = Path(self.temp_directory.name) / ".session_secret"
        self.secret_file.write_bytes(b"test-only-session-secret")
        self.patches = [
            patch.object(teacher_auth, "TEACHERS_FILE", self.credentials_file),
            patch.object(teacher_auth, "SESSION_SECRET_FILE", self.secret_file),
        ]
        for active_patch in self.patches:
            active_patch.start()
        salt = b"test-salt"
        self.credentials_file.write_text(
            json.dumps(
                {
                    "teacher": {
                        "salt": salt.hex(),
                        "password_hash": teacher_auth.hash_password(
                            "correct horse battery staple", salt
                        ),
                        "iterations": teacher_auth.PASSWORD_HASH_ITERATIONS,
                    }
                }
            ),
            encoding="utf-8",
        )

    def tearDown(self):
        for active_patch in reversed(self.patches):
            active_patch.stop()
        self.temp_directory.cleanup()

    def make_request(self, cookie_value=None):
        headers = []
        if cookie_value is not None:
            headers.append(
                (b"cookie", f"{teacher_auth.SESSION_COOKIE_NAME}={cookie_value}".encode())
            )
        return Request(
            {
                "type": "http",
                "http_version": "1.1",
                "method": "GET",
                "scheme": "http",
                "path": "/",
                "raw_path": b"/",
                "query_string": b"",
                "headers": headers,
                "server": ("testserver", 80),
                "client": ("testclient", 123),
            }
        )

    def test_teacher_password_is_verified(self):
        self.assertTrue(
            teacher_auth.authenticate_teacher(
                "teacher", "correct horse battery staple"
            )
        )
        self.assertFalse(teacher_auth.authenticate_teacher("teacher", "wrong"))

    def test_valid_session_identifies_teacher(self):
        token = teacher_auth.create_session_token("teacher")
        self.assertEqual(require_teacher(self.make_request(token)), "teacher")

    def test_missing_or_tampered_session_is_rejected(self):
        tokens = (None, "not-a-session", teacher_auth.create_session_token("teacher") + "x")
        for token in tokens:
            with self.subTest(token=token):
                with self.assertRaises(HTTPException) as error:
                    require_teacher(self.make_request(token))
                self.assertEqual(error.exception.status_code, 401)


if __name__ == "__main__":
    unittest.main()