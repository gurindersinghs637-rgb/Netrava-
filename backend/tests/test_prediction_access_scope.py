"""Tests that prediction access checks use the live image-to-screening relation."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from backend.app.services.prediction_service import _verify_image_in_clinic


class _Query:
    def __init__(self, rows):
        self.rows = rows
        self.selected = None
        self.filters = []

    def select(self, fields):
        self.selected = fields
        return self

    def eq(self, field, value):
        self.filters.append((field, value))
        return self

    def execute(self):
        return SimpleNamespace(data=self.rows)


class _Client:
    def __init__(self, rows):
        self.query = _Query(rows)

    def table(self, name):
        assert name == "retinal_images"
        return self.query


def test_prediction_access_uses_related_screening_clinic_filter():
    client = _Client([{"id": "image-1"}])

    _verify_image_in_clinic(client, "image-1", "clinic-1")

    assert client.query.selected == "id,content_sha256,screenings!inner(clinic_id)"
    assert client.query.filters == [
        ("id", "image-1"),
        ("screenings.clinic_id", "clinic-1"),
    ]


def test_prediction_access_hides_images_outside_clinic():
    with pytest.raises(HTTPException) as exc_info:
        _verify_image_in_clinic(_Client([]), "image-1", "other-clinic")

    assert exc_info.value.status_code == 404


def test_prediction_rejects_different_bytes_for_stored_image():
    """An image ID cannot label a prediction computed from another upload."""
    import hashlib
    client = _Client([{"id": "image-1", "content_sha256": hashlib.sha256(b"original").hexdigest()}])
    _verify_image_in_clinic(client, "image-1", "clinic-1", b"original")
    with pytest.raises(HTTPException) as error:
        _verify_image_in_clinic(client, "image-1", "clinic-1", b"different")
    assert error.value.status_code == 422
