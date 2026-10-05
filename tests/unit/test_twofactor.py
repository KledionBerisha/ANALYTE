"""
TOTP (RFC 6238) dhe kodet e rimëkëmbjes (ADR 0018).

Vektorët janë ata të shtojcës B të RFC 6238 për SHA-1 (sekreti ASCII «12345678901234567890», tetë shifra); gjashtë
shifrat e aplikacioneve janë tetë shifrat e prera, prandaj të njëjtat vektorë i provojnë të dyja.
"""

from __future__ import annotations

import base64
import re

import pytest

from analyte import twofactor

RFC_KEY = b"12345678901234567890"
RFC_SECRET = base64.b32encode(RFC_KEY).decode().rstrip("=")

RFC_6238_SHA1 = [
    (59, "94287082"),
    (1111111109, "07081804"),
    (1111111111, "14050471"),
    (1234567890, "89005924"),
    (2000000000, "69279037"),
    (20000000000, "65353130"),
]


@pytest.mark.parametrize(("time_s", "expected"), RFC_6238_SHA1)
def test_rfc_6238_vectors_with_eight_digits(time_s, expected):
    assert twofactor.code_at(RFC_SECRET, twofactor.step_of(time_s), digits=8) == expected


@pytest.mark.parametrize(("time_s", "expected"), RFC_6238_SHA1)
def test_six_digit_code_is_the_truncation_of_the_eight_digit_one(time_s, expected):
    assert twofactor.code_at(RFC_SECRET, twofactor.step_of(time_s)) == expected[-6:]


def test_rfc_4226_hotp_vectors():
    # RFC 4226, shtojca D: sekreti i njëjtë, numëruesit 0..4, gjashtë shifra.
    expected = ["755224", "287082", "359152", "969429", "338314"]
    assert [twofactor.hotp(RFC_KEY, counter) for counter in range(5)] == expected


def test_match_accepts_the_current_step_and_one_either_side_but_no_more():
    now = 1111111111.0
    current = twofactor.step_of(now)
    for offset in (-1, 0, 1):
        assert twofactor.match(RFC_SECRET, twofactor.code_at(RFC_SECRET, current + offset), now) == current + offset
    for offset in (-2, 2):
        assert twofactor.match(RFC_SECRET, twofactor.code_at(RFC_SECRET, current + offset), now) is None


def test_match_reports_the_step_so_the_caller_can_refuse_a_replay():
    now = 1234567890.0
    code = twofactor.code_at(RFC_SECRET, twofactor.step_of(now))
    assert twofactor.match(RFC_SECRET, code, now) == twofactor.step_of(now)
    # i njëjti kod pas 30 sekondash: ende brenda dritares, por hapi është i njëjti, jo më i madh
    assert twofactor.match(RFC_SECRET, code, now + 30) == twofactor.step_of(now)


def test_codes_with_spaces_are_accepted_and_malformed_ones_are_not():
    now = 59.0
    code = twofactor.code_at(RFC_SECRET, twofactor.step_of(now))
    spaced = f"{code[:3]} {code[3:]}"
    assert twofactor.match(RFC_SECRET, spaced, now) == twofactor.step_of(now)
    for bad in ("", "12345", "1234567", "abcdef", "١٢٣٤٥٦", "12 34 5"):
        assert twofactor.match(RFC_SECRET, bad, now) is None


def test_a_new_secret_is_160_bits_base32_without_padding():
    secret = twofactor.new_secret()
    assert re.fullmatch(r"[A-Z2-7]{32}", secret)
    assert twofactor.new_secret() != secret
    assert len(base64.b32decode(secret)) == 20


def test_otpauth_uri_has_the_fields_authenticator_apps_read():
    uri = twofactor.otpauth_uri("ABCDEFGH", "viktima@shembull.al", "ANALYTE")
    assert uri.startswith("otpauth://totp/ANALYTE%3Aviktima%40shembull.al?")
    for part in ("secret=ABCDEFGH", "issuer=ANALYTE", "algorithm=SHA1", "digits=6", "period=30"):
        assert part in uri


def test_recovery_codes_have_the_shape_and_entropy_claimed():
    codes = {twofactor.new_recovery_code() for _ in range(200)}
    assert len(codes) == 200
    for code in codes:
        assert re.fullmatch(r"[0-9a-hjkmnp-tv-z]{5}-[0-9a-hjkmnp-tv-z]{5}", code)
        assert twofactor.normalize_recovery_code(code) == code.replace("-", "")


def test_recovery_code_normalization_ignores_case_dashes_and_spaces_only():
    assert twofactor.normalize_recovery_code("ABCDE-23456") == "abcde23456"
    assert twofactor.normalize_recovery_code(" abcde 23456 ") == "abcde23456"
    for bad in ("abcde-2345", "abcde-234567", "abcdi-23456", "abcde-2345!"):
        assert twofactor.normalize_recovery_code(bad) is None
