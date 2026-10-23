"""Tests for the helper functions of the app."""

import pytest

from src.app_fn import convert_input_features, validate_feedback


def make_inputs(trauma: bool = False, cancer: bool = False) -> list:
    return [45, "Asian", "M", 2.0, cancer, "Elective", "Routine", "A", "B", 3, trauma]


def test_convert_input_features_keeps_booleans():
    # bool("False") is True, so strings must never be cast to bool
    data = convert_input_features(make_inputs(trauma=False, cancer=False))
    assert not data["TRAUMA"].iloc[0]
    assert not data["PRIOR_CANCER"].iloc[0]

    data = convert_input_features(make_inputs(trauma=True, cancer=True))
    assert data["TRAUMA"].iloc[0]
    assert data["PRIOR_CANCER"].iloc[0]


def test_convert_input_features_types():
    data = convert_input_features(make_inputs())
    assert data["AGE"].iloc[0] == 45
    assert data["ASA_ORIGINAL"].dtype == float
    assert data["OP_SEVERITY"].iloc[0] == "3"  # Categorical in the model


@pytest.mark.parametrize(
    "email, subject, message, valid",
    [
        ("a@b.co", "Hello", "A message\nover two lines", True),
        ("", "Hello", "A message", False),
        ("not-an-email", "Hello", "A message", False),
        ("a@b.co\nBcc: x@y.z", "Hello", "A message", False),
        ("a@b.co", "Hello\r\nBcc: x@y.z", "A message", False),
        ("a@b.co", "s" * 151, "A message", False),
        ("a@b.co", "Hello", "m" * 2001, False),
    ],
)
def test_validate_feedback(email, subject, message, valid):
    assert (validate_feedback(email, subject, message) is None) == valid
