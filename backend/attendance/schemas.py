import base64
import binascii
import io
from typing import Annotated

from PIL import Image
from pydantic import BaseModel, Field, field_validator

MAX_NOM_LENGTH = 100
MAX_HEADCOUNT = 1000
IMAGE_DATA_URL_PREFIX = "data:image/png;base64,"
MAX_IMAGE_BASE64_CHARS = 2_500_000


class SessionCreateRequest(BaseModel):
    headcount: Annotated[int, Field(ge=1, le=MAX_HEADCOUNT)]


class SessionCreateResponse(BaseModel):
    session_token: str
    sign_url: str
    headcount: int


class SessionStatusResponse(BaseModel):
    confirmed_count: int
    headcount: int
    ready: bool
    recap_id: int | None


class PublicSessionResponse(BaseModel):
    headcount: int
    confirmed_count: int
    status: str


class SignRequest(BaseModel):
    nom: Annotated[str, Field(min_length=1, max_length=MAX_NOM_LENGTH)]
    image: str

    @field_validator("nom")
    @classmethod
    def strip_nom(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Le nom ne peut pas être vide.")
        return value

    @field_validator("image")
    @classmethod
    def validate_image(cls, value: str) -> str:
        if not value.startswith(IMAGE_DATA_URL_PREFIX):
            raise ValueError("Format d'image invalide.")
        payload = value[len(IMAGE_DATA_URL_PREFIX) :]
        if len(payload) > MAX_IMAGE_BASE64_CHARS:
            raise ValueError("Image trop volumineuse.")
        try:
            decoded = base64.b64decode(payload, validate=True)
        except (binascii.Error, ValueError):
            raise ValueError("Image invalide.")
        try:
            Image.open(io.BytesIO(decoded)).verify()
        except Exception:
            raise ValueError("Image invalide.")
        return value
