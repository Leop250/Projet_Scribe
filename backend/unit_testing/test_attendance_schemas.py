import base64
import io

import pytest
from PIL import Image
from pydantic import ValidationError

from attendance.schemas import (
    IMAGE_DATA_URL_PREFIX,
    MAX_HEADCOUNT,
    SessionCreateRequest,
    SignRequest,
)


def _valid_image_data_url() -> str:
    """Construit une vraie petite image PNG valide, encodée en data URL."""
    buffer = io.BytesIO()
    Image.new("RGB", (2, 2), color=(255, 0, 0)).save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"{IMAGE_DATA_URL_PREFIX}{encoded}"


# --- SessionCreateRequest.headcount -----------------------------------------


@pytest.mark.parametrize("headcount", [1, 50, MAX_HEADCOUNT])
def test_headcount_accepts_values_within_bounds(headcount):
    request = SessionCreateRequest(headcount=headcount)
    assert request.headcount == headcount


@pytest.mark.parametrize("headcount", [0, -1, MAX_HEADCOUNT + 1])
def test_headcount_rejects_values_outside_bounds(headcount):
    with pytest.raises(ValidationError):
        SessionCreateRequest(headcount=headcount)


# --- SignRequest.nom ----------------------------------------------------------


def test_nom_is_stripped_of_surrounding_whitespace():
    request = SignRequest(nom="  Alice Dupont  ", image=_valid_image_data_url())
    assert request.nom == "Alice Dupont"


def test_nom_rejects_blank_value_after_stripping():
    with pytest.raises(ValidationError):
        SignRequest(nom="   ", image=_valid_image_data_url())


# --- SignRequest.image ---------------------------------------------------------


def test_image_accepts_a_valid_png_data_url():
    data_url = _valid_image_data_url()
    request = SignRequest(nom="Alice", image=data_url)
    assert request.image == data_url


def test_image_rejects_wrong_prefix():
    with pytest.raises(ValidationError):
        SignRequest(nom="Alice", image="data:image/jpeg;base64,abcd")


def test_image_rejects_invalid_base64_payload():
    with pytest.raises(ValidationError):
        SignRequest(nom="Alice", image=f"{IMAGE_DATA_URL_PREFIX}not-valid-base64!!!")


def test_image_rejects_base64_that_is_not_a_real_image():
    garbage = base64.b64encode(b"this is definitely not a png").decode("ascii")
    with pytest.raises(ValidationError):
        SignRequest(nom="Alice", image=f"{IMAGE_DATA_URL_PREFIX}{garbage}")


def test_image_rejects_payload_over_the_size_limit(monkeypatch):
    monkeypatch.setattr("attendance.schemas.MAX_IMAGE_BASE64_CHARS", 10)
    with pytest.raises(ValidationError):
        SignRequest(nom="Alice", image=_valid_image_data_url())
