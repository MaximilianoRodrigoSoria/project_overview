"""Utility helpers for reporting domain."""

import re
from uuid import uuid4

from .exceptions import ValidationError


RUN_ID_MAX_LENGTH = 64
RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


def generate_run_id(length: int = 12) -> str:
	"""Generate a short run_id for tracing."""
	return uuid4().hex[:length]


def validate_run_id(run_id: str) -> None:
	"""Validate run_id format and length."""
	if not run_id or not run_id.strip():
		raise ValidationError("run_id cannot be empty")

	if len(run_id) > RUN_ID_MAX_LENGTH:
		raise ValidationError("run_id is too long")

	if not RUN_ID_PATTERN.match(run_id):
		raise ValidationError("run_id contains invalid characters")

