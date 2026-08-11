"""Password strength policy.

Enforced wherever a password is created or changed. A "strong enough" password
scores >= 3 out of 5:
  - at least 8 characters
  - at least one lowercase letter
  - at least one uppercase letter
  - at least one digit
  - at least one symbol
"""

import re

MIN_LENGTH = 8

_CHECKS = [
    ("length", r".{8,}"),
    ("lower", r"[a-z]"),
    ("upper", r"[A-Z]"),
    ("digit", r"[0-9]"),
    ("symbol", r"[^A-Za-z0-9]"),
]


class WeakPasswordError(ValueError):
    """Raised when a password does not meet the minimum strength policy."""


def assess_password_strength(password: str) -> dict:
    """Return {score, passed, missing} for a candidate password.

    score is the number of satisfied criteria (0..5). A score >= 3 passes.
    """
    passed = [name for name, pattern in _CHECKS if re.search(pattern, password)]
    missing = [name for name, _ in _CHECKS if name not in passed]
    return {"score": len(passed), "passed": passed, "missing": missing}


def validate_password(password: str) -> None:
    """Raise WeakPasswordError unless the password meets the policy."""
    if not password or len(password) < MIN_LENGTH:
        raise WeakPasswordError(
            f"Password must be at least {MIN_LENGTH} characters long."
        )
    result = assess_password_strength(password)
    if result["score"] < 3:
        raise WeakPasswordError(
            "Password is too weak. Use at least 8 characters mixing upper and "
            "lowercase letters, numbers and symbols (e.g. 'Demo@2026#X')."
        )
