import pytest
from pydantic import ValidationError

from auth.schemas import ResetPasswordRequest, UserRegister, VerifyCodeRequest

VALID_PASSWORD = "Sup3r$ecret"


def test_email_is_normalized_to_lowercase_and_stripped():
    user = UserRegister(username="alice", email="  Alice@Example.COM ", password=VALID_PASSWORD)
    assert user.email == "alice@example.com"


@pytest.mark.parametrize("code", ["123456", "000000", "999999"])
def test_verification_code_accepts_six_digits(code):
    request = VerifyCodeRequest(email="a@b.com", code=code)
    assert request.code == code


@pytest.mark.parametrize(
    "code",
    [
        "12345",  # trop court
        "1234567",  # trop long
        "abcdef",  # pas des chiffres
        "12 345",  # espace
    ],
)
def test_verification_code_rejects_invalid_formats(code):
    with pytest.raises(ValidationError):
        VerifyCodeRequest(email="a@b.com", code=code)


def test_password_strength_accepts_a_valid_password():
    user = UserRegister(username="alice", email="a@b.com", password=VALID_PASSWORD)
    assert user.password == VALID_PASSWORD


@pytest.mark.parametrize(
    "password",
    [
        "Sh0rt$",  # moins de 8 caractères
        "nouppercase1$",  # pas de majuscule
        "NoSpecialChar1",  # pas de caractère spécial
        "A$" + "a" * 71,  # plus de 72 octets une fois encodé en utf-8
    ],
)
def test_password_strength_rejects_weak_passwords(password):
    with pytest.raises(ValidationError):
        UserRegister(username="alice", email="a@b.com", password=password)


def test_reset_password_request_reuses_the_same_password_strength_rule():
    with pytest.raises(ValidationError):
        ResetPasswordRequest(email="a@b.com", code="123456", new_password="weak")

    request = ResetPasswordRequest(email="a@b.com", code="123456", new_password=VALID_PASSWORD)
    assert request.new_password == VALID_PASSWORD
