"""
Hapi i dytë i hyrjes: TOTP dhe kodet e rimëkëmbjes (ADR 0018).

Pohimet më të rëndësishme:

  - **Hyrja me hap të dytë nuk jep tokenë pas fjalëkalimit**, por një sfidë; vetëm një kod i vlefshëm hap seancën.
  - **Asgjë nuk tregohet para fjalëkalimit të saktë**: email-i i panjohur dhe fjalëkalimi i gabuar japin të njëjtën 401,
    me ose pa hap të dytë.
  - **Një kod nuk përdoret dy herë** (rilojimi), kodet e rimëkëmbjes vlejnë një herë.
  - **Kodet e gabuara kufizohen para se kodi të kontrollohet.**
  - **Sfida pushon** pas ndryshimit të fjalëkalimit ose çaktivizimit të hapit të dytë, dhe nuk është token aksesi.
  - **Sekreti ruhet i koduar**, kodet e rimëkëmbjes vetëm si HMAC.
"""

from __future__ import annotations

import jwt
import pytest
from sqlalchemy import select

from analyte.persistence.tables import RecoveryCodeRow
from analyte.security import keyed_hash
from tests.fixtures.accounts import (
    EMAIL,
    NEW_PASSWORD,
    PASSWORD,
    SECRET,
    World,
    code_for,
    wrong_code,
)
from tests.fixtures.mailbox import reset_token_in


@pytest.fixture
def world(tmp_path):
    w = World(tmp_path)
    w.confirmed()
    return w


def _challenge(world: World) -> str:
    response = world.login()
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["mfa_required"] is True and "access_token" not in body
    return body["challenge"]


# Regjistrimi


def test_enrolment_returns_the_secret_and_uri_once_and_activates_only_with_a_valid_code(world):
    access = world.tokens()["access_token"]
    assert world.authed(access, "GET", "/auth/2fa").json() == {
        "enabled": False,
        "recovery_codes_remaining": 0,
    }

    enrolled = world.authed(access, "POST", "/auth/2fa/enroll").json()
    secret = enrolled["secret"]
    assert enrolled["otpauth_uri"].startswith("otpauth://totp/ANALYTE%3Aviktima%40shembull.al?")
    assert f"secret={secret}" in enrolled["otpauth_uri"]
    # ende jo aktiv: hyrja nuk kërkon hap të dytë derisa kodi i parë të konfirmohet
    assert world.login().json().get("access_token")

    wrong = world.authed(access, "POST", "/auth/2fa/confirm", json={"code": wrong_code(secret)})
    assert wrong.status_code == 400  # jo 401: klienti do ta merrte për seancë të humbur
    assert world.user().totp_enabled_at is None

    confirmed = world.authed(access, "POST", "/auth/2fa/confirm", json={"code": code_for(secret)})
    assert confirmed.status_code == 200
    codes = confirmed.json()["recovery_codes"]
    assert len(codes) == 8 and len(set(codes)) == 8
    assert world.authed(access, "GET", "/auth/2fa").json() == {
        "enabled": True,
        "recovery_codes_remaining": 8,
    }
    assert [e.event_type for e in world.audit("auth.two_factor_enabled")] == [
        "auth.two_factor_enabled"
    ]


def test_the_secret_cannot_be_read_again_once_active_and_enrolling_twice_is_refused(world):
    secret, _, tokens = world.enable_two_factor()
    again = world.authed(tokens["access_token"], "POST", "/auth/2fa/enroll")
    assert again.status_code == 409
    assert secret not in again.text
    assert (
        world.authed(
            tokens["access_token"], "POST", "/auth/2fa/confirm", json={"code": code_for(secret)}
        ).status_code
        == 409
    )


def test_confirming_without_starting_is_refused(world):
    access = world.tokens()["access_token"]
    assert (
        world.authed(access, "POST", "/auth/2fa/confirm", json={"code": "123456"}).status_code
        == 409
    )


def test_enrolment_endpoints_need_a_session(world):
    for method, path in (
        ("GET", "/auth/2fa"),
        ("POST", "/auth/2fa/enroll"),
        ("POST", "/auth/2fa/confirm"),
        ("POST", "/auth/2fa/disable"),
    ):
        assert (
            world.client.request(method, path, json={"code": "1", "password": "x"}).status_code
            == 401
        )


def test_the_secret_is_stored_encrypted_and_recovery_codes_only_as_keyed_hashes(world):
    secret, codes, _ = world.enable_two_factor()
    stored = world.user().totp_secret_encrypted
    assert stored is not None and secret.encode() not in stored
    assert world.services.store.decrypt_text(stored) == secret
    with world.db() as db:
        keys = {row.code_key for row in db.scalars(select(RecoveryCodeRow))}
    assert len(keys) == 8
    for code in codes:
        assert code not in keys and code.replace("-", "") not in keys
        assert (
            keyed_hash(SECRET, "recovery-code", f"{world.user().id}\0{code.replace('-', '')}")
            in keys
        )


def test_the_code_that_confirmed_the_enrolment_cannot_be_reused_to_sign_in(world):
    # `enable_two_factor` e konfirmoi me kodin e hapit të tanishëm
    secret, _, _ = world.enable_two_factor()
    challenge = _challenge(world)
    assert world.verify(challenge, code_for(secret)).status_code == 401
    assert world.verify(challenge, code_for(secret, +1)).status_code == 200  # hapi tjetër vlen


def test_enabling_revokes_the_other_sessions_but_keeps_the_one_that_enabled_it(world):
    other = world.tokens()
    _, _, enabling = world.enable_two_factor()
    assert world.me(other["access_token"]).status_code == 401
    assert world.me(enabling["access_token"]).status_code == 200


# Hyrja


def test_login_with_two_factor_returns_a_challenge_and_verify_opens_the_session(world):
    secret, _, _ = world.enable_two_factor()
    challenge = _challenge(world)
    opened = world.verify(challenge, code_for(secret, +1))
    assert opened.status_code == 200
    tokens = opened.json()
    assert world.me(tokens["access_token"]).json()["email"] == EMAIL
    assert (
        world.client.post(
            "/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        ).status_code
        == 200
    )


def test_before_the_password_is_checked_nothing_shows_whether_an_account_has_two_factor(world):
    world.enable_two_factor()
    world.confirmed("pa-hap-te-dyte@shembull.al")
    wrong_password = world.login(EMAIL, "fjalekalim-i-gabuar-xyz")
    unknown = world.login("askush@shembull.al", "fjalekalim-i-gabuar-xyz")
    plain_wrong = world.login("pa-hap-te-dyte@shembull.al", "fjalekalim-i-gabuar-xyz")
    assert wrong_password.status_code == unknown.status_code == plain_wrong.status_code == 401
    assert wrong_password.json()["title"] == unknown.json()["title"] == plain_wrong.json()["title"]
    for response in (wrong_password, unknown, plain_wrong):
        assert "mfa_required" not in response.text and "challenge" not in response.text


def test_a_replayed_code_is_refused(world):
    secret, _, _ = world.enable_two_factor()
    code = code_for(secret, +1)
    assert world.verify(_challenge(world), code).status_code == 200
    assert world.verify(_challenge(world), code).status_code == 401  # i njëjti kod, hap i njëjtë
    # hap më i vjetër se i pranuari
    assert world.verify(_challenge(world), code_for(secret, 0)).status_code == 401


def test_a_wrong_code_gives_the_same_error_as_a_bad_challenge(world):
    secret, _, _ = world.enable_two_factor()
    wrong = world.verify(_challenge(world), wrong_code(secret))
    garbage = world.verify("jo-një-sfidë-e-vërtetë-" * 3, code_for(secret, +1))
    assert wrong.status_code == garbage.status_code == 401
    assert wrong.json()["title"] == garbage.json()["title"]


def test_recovery_codes_work_once(world):
    _, codes, _ = world.enable_two_factor()
    assert world.verify(_challenge(world), codes[0]).status_code == 200
    assert world.verify(_challenge(world), codes[0]).status_code == 401
    # forma e shkruar me dorë
    assert world.verify(_challenge(world), codes[1].upper().replace("-", " ")).status_code == 200
    assert world.verify(_challenge(world), codes[2]).status_code == 200
    events = world.audit("auth.recovery_code_used")
    assert [e.payload for e in events] == [{"remaining": 7}, {"remaining": 6}, {"remaining": 5}]


def test_a_recovery_code_of_another_account_does_not_work(world):
    _, codes, _ = world.enable_two_factor()
    world.confirmed("tjeter@shembull.al")
    other_secret, _, _ = world.enable_two_factor("tjeter@shembull.al")
    other = world.login("tjeter@shembull.al").json()["challenge"]
    assert world.verify(other, codes[0]).status_code == 401
    assert world.verify(other, code_for(other_secret, +1)).status_code == 200


def test_a_code_for_another_account_does_not_open_this_one(world):
    world.enable_two_factor()
    world.confirmed("tjeter@shembull.al")
    other_secret, _, _ = world.enable_two_factor("tjeter@shembull.al")
    assert world.verify(_challenge(world), code_for(other_secret, +1)).status_code == 401


# Kufizimi i kodeve të gabuara


def test_the_sixth_wrong_code_is_throttled_even_when_the_next_one_is_right(world):
    secret, _, _ = world.enable_two_factor()
    challenge = _challenge(world)
    for _ in range(5):
        assert world.verify(challenge, wrong_code(secret)).status_code == 401
    blocked = world.verify(challenge, code_for(secret, +1))
    assert blocked.status_code == 429  # kodi i saktë refuzohet: kufizimi vjen para kontrollit
    assert 1 <= int(blocked.headers["retry-after"]) <= 15 * 60
    assert [e.payload for e in world.audit("auth.login_throttled")] == [{"bucket": "mfa_pair"}]


def test_wrong_codes_are_counted_per_user_across_addresses(tmp_path):
    w = World(tmp_path, trusted_proxy_hops=1, mfa_max_failures_user=3)
    w.confirmed()
    secret, _, _ = w.enable_two_factor()
    challenge = w.login().json()["challenge"]
    for i in range(3):
        assert w.verify(challenge, wrong_code(secret), ip=f"203.0.113.{i + 1}").status_code == 401
    # një IP e katërt, pa asnjë dështim të vetin, refuzohet nga kova e përdoruesit
    assert w.verify(challenge, code_for(secret, +1), ip="203.0.113.99").status_code == 429


def test_wrong_codes_are_counted_per_address_across_users(tmp_path):
    w = World(
        tmp_path,
        trusted_proxy_hops=1,
        mfa_max_failures_ip=3,
        mfa_max_failures_pair=50,
        mfa_max_failures_user=50,
    )
    users = ["a@shembull.al", "b@shembull.al", "c@shembull.al", "d@shembull.al"]
    secrets_ = {}
    for email in users:
        w.confirmed(email)
        secrets_[email], _, _ = w.enable_two_factor(email)
    for email in users[:3]:
        challenge = w.login(email).json()["challenge"]
        assert w.verify(challenge, wrong_code(secrets_[email]), ip="203.0.113.7").status_code == 401
    challenge = w.login(users[3]).json()["challenge"]
    assert (
        w.verify(challenge, code_for(secrets_[users[3]], +1), ip="203.0.113.7").status_code == 429
    )


def test_mfa_failures_do_not_fill_the_password_buckets_and_the_reverse(world):
    secret, _, _ = world.enable_two_factor()
    challenge = _challenge(world)
    for _ in range(5):
        world.verify(challenge, wrong_code(secret))
    assert world.login().status_code == 200  # fjalëkalimi i saktë mbetet i hapur
    for _ in range(5):
        assert world.login(EMAIL, "fjalekalim-i-gabuar-xyz").status_code == 401
    assert world.login(EMAIL, "fjalekalim-i-gabuar-xyz").status_code == 429


def test_a_good_code_clears_the_pair_counter(world):
    secret, _, _ = world.enable_two_factor()
    challenge = _challenge(world)
    for _ in range(4):
        world.verify(challenge, wrong_code(secret))
    assert world.verify(challenge, code_for(secret, +1)).status_code == 200
    for _ in range(4):
        # numërimi nisi nga e para
        assert world.verify(challenge, wrong_code(secret)).status_code == 401


# Sfida


def test_a_challenge_dies_when_the_password_is_reset(world):
    secret, _, _ = world.enable_two_factor()
    challenge = _challenge(world)
    world.forgot()
    assert world.reset(reset_token_in(world.outbox.to(EMAIL)[-1])).status_code == 204
    assert world.verify(challenge, code_for(secret, +1)).status_code == 401
    # hapi i dytë mbeti: me fjalëkalimin e ri hyrja kërkon prapë kod
    assert world.login(EMAIL, NEW_PASSWORD).json()["mfa_required"] is True


def test_a_challenge_dies_when_two_factor_is_disabled(world):
    secret, codes, tokens = world.enable_two_factor()
    challenge = _challenge(world)
    disabled = world.authed(
        tokens["access_token"],
        "POST",
        "/auth/2fa/disable",
        json={"password": PASSWORD, "code": codes[0]},
    )
    assert disabled.status_code == 204
    assert world.verify(challenge, code_for(secret, +1)).status_code == 401


def test_a_challenge_dies_when_two_factor_is_disabled_and_enabled_again(world):
    _secret, codes, tokens = world.enable_two_factor()
    challenge = _challenge(world)
    world.authed(
        tokens["access_token"],
        "POST",
        "/auth/2fa/disable",
        json={"password": PASSWORD, "code": codes[0]},
    )
    new_secret, _, _ = world.enable_two_factor()
    assert world.verify(challenge, code_for(new_secret, +1)).status_code == 401


def test_an_expired_challenge_is_refused(tmp_path):
    w = World(tmp_path, mfa_challenge_minutes=0)
    w.confirmed()
    secret, _, _ = w.enable_two_factor()
    challenge = w.login().json()["challenge"]
    assert w.verify(challenge, code_for(secret, +1)).status_code == 401


def test_a_challenge_is_not_an_access_token_and_an_access_token_is_not_a_challenge(world):
    secret, _, tokens = world.enable_two_factor()
    challenge = _challenge(world)
    assert world.me(challenge).status_code == 401
    assert world.client.post("/auth/refresh", json={"refresh_token": challenge}).status_code == 401
    assert world.verify(tokens["access_token"], code_for(secret, +1)).status_code == 401
    assert world.verify(tokens["refresh_token"], code_for(secret, +1)).status_code == 401


def test_a_challenge_signed_with_another_key_is_refused(world):
    secret, _, _ = world.enable_two_factor()
    forged = jwt.encode(
        {"sub": str(world.user().id), "typ": "mfa", "cv": "x", "exp": 9999999999},
        "k" * 48,
        algorithm="HS256",
    )
    assert world.verify(forged, code_for(secret, +1)).status_code == 401


def test_the_challenge_carries_no_email(world):
    world.enable_two_factor()
    payload = jwt.decode(_challenge(world), options={"verify_signature": False})
    assert "viktima" not in str(payload) and "shembull" not in str(payload)
    assert set(payload) == {"sub", "typ", "cv", "iat", "exp"}


def test_an_unconfirmed_password_login_still_gets_403_before_any_challenge(world):
    world.register("pakonfirmuar@shembull.al")
    assert world.login("pakonfirmuar@shembull.al").status_code == 403


# Çaktivizimi


def test_disabling_needs_the_password_and_a_valid_code(world):
    secret, codes, tokens = world.enable_two_factor()
    access = tokens["access_token"]

    def disable(**body):
        return world.authed(access, "POST", "/auth/2fa/disable", json=body)

    assert disable(password="fjalekalim-i-gabuar-xyz", code=codes[0]).status_code == 400
    assert disable(password=PASSWORD, code=wrong_code(secret)).status_code == 400
    assert world.user().totp_enabled_at is not None
    # fjalëkalimi i gabuar nuk shpenzoi kodin e rimëkëmbjes
    assert disable(password=PASSWORD, code=codes[0]).status_code == 204


def test_after_disabling_login_gives_tokens_again_and_the_material_is_gone(world):
    secret, _codes, tokens = world.enable_two_factor()
    code = code_for(secret, +1)
    assert (
        world.authed(
            tokens["access_token"],
            "POST",
            "/auth/2fa/disable",
            json={"password": PASSWORD, "code": code},
        ).status_code
        == 204
    )
    assert "access_token" in world.login().json()
    user = world.user()
    assert (
        user.totp_secret_encrypted is None
        and user.totp_enabled_at is None
        and user.totp_last_step is None
    )
    with world.db() as db:
        assert db.scalars(select(RecoveryCodeRow)).all() == []
    assert world.authed(tokens["access_token"], "GET", "/auth/2fa").json()["enabled"] is False
    assert (
        world.authed(
            tokens["access_token"],
            "POST",
            "/auth/2fa/disable",
            json={"password": PASSWORD, "code": code},
        ).status_code
        == 409
    )
    assert [e.event_type for e in world.audit("auth.two_factor_disabled")] == [
        "auth.two_factor_disabled"
    ]


def test_a_stolen_access_token_cannot_disable_two_factor_without_the_password(world):
    secret, _, tokens = world.enable_two_factor()
    attempt = world.authed(
        tokens["access_token"],
        "POST",
        "/auth/2fa/disable",
        json={"password": "fjalekalim-i-gabuar-xyz", "code": code_for(secret, +1)},
    )
    assert attempt.status_code == 400
    assert world.user().totp_enabled_at is not None


def test_disable_attempts_are_throttled_like_login_codes(world):
    secret, _, tokens = world.enable_two_factor()
    for _ in range(5):
        assert (
            world.authed(
                tokens["access_token"],
                "POST",
                "/auth/2fa/disable",
                json={"password": PASSWORD, "code": wrong_code(secret)},
            ).status_code
            == 400
        )
    blocked = world.authed(
        tokens["access_token"],
        "POST",
        "/auth/2fa/disable",
        json={"password": PASSWORD, "code": code_for(secret, +1)},
    )
    assert blocked.status_code == 429


# Dil kudo dhe rivendosja mbeten të sakta


def test_logout_all_still_revokes_sessions_opened_through_verify(world):
    secret, _, _ = world.enable_two_factor()
    tokens = world.verify(_challenge(world), code_for(secret, +1)).json()
    assert world.authed(tokens["access_token"], "POST", "/auth/logout-all").status_code == 204
    assert world.me(tokens["access_token"]).status_code == 401
    assert (
        world.client.post(
            "/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        ).status_code
        == 401
    )


def test_a_stolen_mailbox_alone_cannot_get_in_through_a_reset(world):
    _secret, _, _ = world.enable_two_factor()
    world.forgot()
    assert (
        world.reset(
            reset_token_in(world.outbox.to(EMAIL)[-1]), "fjalekalim-i-sulmuesit"
        ).status_code
        == 204
    )
    attacker = world.login(EMAIL, "fjalekalim-i-sulmuesit").json()
    assert attacker["mfa_required"] is True and "access_token" not in attacker


def test_audit_never_holds_an_email_or_a_code(world):
    secret, codes, _ = world.enable_two_factor()
    world.verify(_challenge(world), codes[0])
    world.verify(_challenge(world), wrong_code(secret))
    from analyte.persistence.tables import AuditEventRow

    with world.db() as db:
        dump = str([(e.event_type, e.payload) for e in db.scalars(select(AuditEventRow))])
    assert "viktima" not in dump and "shembull" not in dump
    assert secret not in dump and codes[0] not in dump and codes[0].replace("-", "") not in dump
