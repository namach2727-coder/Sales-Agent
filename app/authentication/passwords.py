"""Argon2id password policy and hashing adapter."""

from __future__ import annotations

from argon2 import PasswordHasher, Type
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from app.authentication.exceptions import AuthenticationValidationError


_DEFAULT_HASHER = PasswordHasher(type=Type.ID)
# Created once at process start so unknown-user verification has the same
# computational shape without paying an extra Argon2 hash on every request.
_DEFAULT_DUMMY_HASH = _DEFAULT_HASHER.hash("authentication-dummy-password")


class PasswordService:
    def __init__(
        self,
        *,
        minimum_length: int = 12,
        maximum_length: int = 1024,
        hasher: PasswordHasher | None = None,
    ):
        self.minimum_length = minimum_length
        self.maximum_length = maximum_length
        self._hasher = hasher or _DEFAULT_HASHER
        self._dummy_hash = (
            self._hasher.hash("authentication-dummy-password")
            if hasher is not None
            else _DEFAULT_DUMMY_HASH
        )

    def validate(self, password: str) -> None:
        if not password or not password.strip():
            raise AuthenticationValidationError("password must not be blank")
        if len(password) < self.minimum_length:
            raise AuthenticationValidationError(
                f"password must be at least {self.minimum_length} characters"
            )
        if len(password) > self.maximum_length:
            raise AuthenticationValidationError("password is too long")

    def hash(self, password: str) -> str:
        self.validate(password)
        return self._hasher.hash(password)

    def verify(self, password_hash: str, password: str) -> bool:
        if len(password) > self.maximum_length:
            return False
        try:
            return self._hasher.verify(password_hash, password)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return False

    def verify_dummy(self, password: str) -> None:
        self.verify(self._dummy_hash, password[: self.maximum_length])

    def needs_rehash(self, password_hash: str) -> bool:
        try:
            return self._hasher.check_needs_rehash(password_hash)
        except InvalidHashError:
            return True
