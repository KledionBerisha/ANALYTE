"""
Rivendosja e fjalëkalimit (ADR 0018).

"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

import analyte.api.auth as auth_module
from analyte.persistence.tables import PasswordResetRow
from analyte.security import keyed_hash
from tests.fixtures.accounts import EMAIL, NEW_PASSWORD, PASSWORD, SECRET, World
from tests.fixtures.mailbox import reset_token_in, token_in

SUBJECT_RESET = "Rivendosni fjalëkalimin tuaj në ANALYTE"
SUBJECT_CONFIRM = "Konfirmoni email-in tuaj në ANALYTE"


@pytest.fixture
def world(tmp_path):
    w = World(tmp_path)
    w.confirmed()
    return w


def _reset_token(world: World, email: str = EMAIL) -> str:
    assert world.forgot(email).status_code == 202
    return reset_token_in(world.outbox.to(email)[-1])


# Rruga e zakonshme


def test_forgot_then_reset_replaces_the_password(world):
    token = _reset_token(world)
    assert world.outbox.to(EMAIL)[-1].subject == SUBJECT_RESET
    assert world.reset(token).status_code == 204
    assert world.login(EMAIL, PASSWORD).status_code == 401
    assert world.login(EMAIL, NEW_PASSWORD).status_code == 200


def test_the_link_works_once(world):
    token = _reset_token(world)
    assert world.reset(token).status_code == 204
    again = world.reset(token, "fjalekalim-i-tretë-i-gjate")
    assert again.status_code == 400
    assert world.login(EMAIL, NEW_PASSWORD).status_code == 200  # nuk u ndryshua sërish


def test_a_new_request_cancels_the_previous_link(world):
    first = _reset_token(world)
    second = _reset_token(world)
    assert world.reset(first).status_code == 400
    assert world.reset(second).status_code == 204


def test_expired_unknown_and_used_links_get_the_same_error(tmp_path):
    w = World(tmp_path, reset_token_minutes=0)  # skadon në çast
    w.confirmed()
    expired = w.reset(_reset_token(w))
    unknown = w.reset("x" * 43)
    assert expired.status_code == unknown.status_code == 400
    assert expired.json()["title"] == unknown.json()["title"]
    assert w.login(EMAIL, PASSWORD).status_code == 200  # fjalëkalimi nuk ndryshoi


def test_a_short_password_is_refused_without_spending_the_link(world):
    token = _reset_token(world)
    short = world.reset(token, "shkurtër")
    assert short.status_code == 422
    assert world.reset(token).status_code == 204  # lidhja ishte ende e vlefshme


def test_the_token_is_never_stored_in_clear(world):
    token = _reset_token(world)
    with world.db() as db:
        row = db.scalars(select(PasswordResetRow)).one()
        assert token not in row.token_key
        assert row.token_key == keyed_hash(SECRET, "password-reset", token)
        # e njëjta vlerë si token konfirmimi nuk jep këtë çelës
        assert row.token_key != keyed_hash(SECRET, "email-confirm", token)


def test_a_confirmation_token_does_not_reset_a_password(world):
    world.register("tjeter@shembull.al")
    confirmation = token_in(world.outbox.to("tjeter@shembull.al")[-1])
    assert world.reset(confirmation).status_code == 400


# Nuk tregon nëse email-i ka llogari


def test_every_kind_of_email_gets_the_same_response(world):
    world.register("pakonfirmuar@shembull.al")
    known = world.forgot(EMAIL)
    pending = world.forgot("pakonfirmuar@shembull.al")
    unknown = world.forgot("askush@shembull.al")
    assert known.status_code == pending.status_code == unknown.status_code == 202
    assert known.json() == pending.json() == unknown.json() == {"message": auth_module.RESET_REPLY}
    assert (
        known.headers["content-type"]
        == pending.headers["content-type"]
        == unknown.headers["content-type"]
    )
    assert world.outbox.to("askush@shembull.al") == []  # asgjë te kutia e dikujt që s'ka llogari


def test_argon2_is_spent_in_every_forgot_branch_so_timing_does_not_show_which(world, monkeypatch):
    world.register("pakonfirmuar@shembull.al")
    calls: list[str] = []
    real = auth_module.hash_password
    monkeypatch.setattr(auth_module, "hash_password", lambda p: calls.append(p) or real(p))
    for email in (EMAIL, "pakonfirmuar@shembull.al", "askush@shembull.al"):
        before = len(calls)
        world.forgot(email)
        assert len(calls) == before + 1, email


def test_reset_spends_argon2_before_looking_at_the_token(world, monkeypatch):
    valid = _reset_token(world)
    calls: list[str] = []
    real = auth_module.hash_password
    monkeypatch.setattr(auth_module, "hash_password", lambda p: calls.append(p) or real(p))
    world.reset("x" * 43)  # token i panjohur
    world.reset(valid)  # token i vlefshëm
    assert len(calls) == 2


def test_an_invalid_email_address_is_refused_before_anything_is_sent(world):
    assert world.client.post("/auth/forgot-password", json={"email": "jo-email"}).status_code == 422
    injected = world.client.post("/auth/forgot-password", json={"email": "a@b.al\nBcc: x@y.al"})
    assert injected.status_code == 422


# Seancat


def test_a_reset_revokes_every_session(world):
    first, second = world.tokens(), world.tokens()
    assert world.me(first["access_token"]).status_code == 200
    assert world.reset(_reset_token(world)).status_code == 204
    for tokens in (first, second):
        assert world.me(tokens["access_token"]).status_code == 401
        refreshed = world.client.post(
            "/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        )
        assert refreshed.status_code == 401
    assert [e.payload for e in world.audit("auth.sessions_revoked_all")] == [{"count": 2}]
    assert world.audit("auth.password_reset")[0].payload == {}


def test_a_reset_does_not_touch_another_users_sessions(world):
    world.confirmed("tjeter@shembull.al")
    other = world.tokens("tjeter@shembull.al")
    world.reset(_reset_token(world))
    assert world.me(other["access_token"]).status_code == 200


# Rivendosja nuk është rrugë anash konfirmimit


def test_an_unconfirmed_account_gets_a_confirmation_link_not_a_reset_link(world):
    world.register("pakonfirmuar@shembull.al")
    before = len(world.outbox.to("pakonfirmuar@shembull.al"))
    assert world.forgot("pakonfirmuar@shembull.al").status_code == 202
    sent = world.outbox.to("pakonfirmuar@shembull.al")
    assert len(sent) == before + 1
    assert sent[-1].subject == SUBJECT_CONFIRM
    assert "/reset-password" not in sent[-1].body
    with world.db() as db:
        assert db.scalars(select(PasswordResetRow)).all() == []


def test_a_reset_token_for_an_unconfirmed_account_changes_nothing(world):
    """Mbrojtje në thellësi: edhe nëse një token ekziston për një llogari të pakonfirmuar, ai nuk e ndryshon as nuk e konfirmon."""
    world.register("pakonfirmuar@shembull.al", PASSWORD)
    user = world.user("pakonfirmuar@shembull.al")
    planted = "q" * 43
    with world.db() as db:
        db.add(
            PasswordResetRow(
                id=uuid.uuid4(),
                user_id=user.id,
                token_key=keyed_hash(SECRET, "password-reset", planted),
                created_at=datetime.now(UTC),
                expires_at=datetime.now(UTC) + timedelta(hours=1),
            )
        )
        db.commit()
    assert world.reset(planted).status_code == 400
    after = world.user("pakonfirmuar@shembull.al")
    assert after.email_confirmed_at is None
    assert after.password_hash == user.password_hash
    assert world.login("pakonfirmuar@shembull.al", NEW_PASSWORD).status_code == 401
    assert world.login("pakonfirmuar@shembull.al", PASSWORD).status_code == 403  # ende pa konfirmim


def test_a_reset_leaves_a_confirmed_account_confirmed_with_the_same_timestamp(world):
    before = world.user().email_confirmed_at
    assert before is not None
    world.reset(_reset_token(world))
    assert world.user().email_confirmed_at == before


# Kufizimi


def test_one_address_gets_at_most_three_reset_requests_an_hour(world):
    for _ in range(3):
        assert world.forgot().status_code == 202
    blocked = world.forgot()
    assert blocked.status_code == 429
    assert 1 <= int(blocked.headers["retry-after"]) <= 3600
    reset_mails = [m for m in world.outbox.to(EMAIL) if m.subject == SUBJECT_RESET]
    assert len(reset_mails) == 3


def test_the_reset_limit_does_not_depend_on_whether_the_email_has_an_account(world):
    for email in (EMAIL, "askush@shembull.al"):
        for _ in range(3):
            world.forgot(email)
    known, unknown = world.forgot(EMAIL), world.forgot("askush@shembull.al")
    assert known.status_code == unknown.status_code == 429
    assert known.json()["title"] == unknown.json()["title"]


def test_reset_requests_do_not_use_up_the_registration_limit(world):
    for _ in range(3):
        world.forgot()
    assert world.register("i-ri@shembull.al").status_code == 202


def test_one_ip_cannot_mail_many_addresses_through_forgot(tmp_path):
    w = World(tmp_path, trusted_proxy_hops=1, register_max_per_ip=3)
    for i in range(3):
        assert w.forgot(f"p{i}@shembull.al", ip="203.0.113.7").status_code == 202
    assert w.forgot("p9@shembull.al", ip="203.0.113.7").status_code == 429
    assert w.forgot("p9@shembull.al", ip="203.0.113.8").status_code == 202


def test_submissions_are_throttled_per_ip_before_the_token_is_checked(tmp_path):
    w = World(tmp_path, trusted_proxy_hops=1, reset_submit_max_per_ip=3)
    w.confirmed()
    token = _reset_token(w)
    for _ in range(3):
        assert w.reset("x" * 43, ip="203.0.113.7").status_code == 400
    # e katërta refuzohet edhe me tokenin e saktë: kufizimi vjen para kontrollit të tokenit
    assert w.reset(token, ip="203.0.113.7").status_code == 429
    assert w.reset(token, ip="203.0.113.8").status_code == 204  # IP tjetër


# Çfarë mbetet te baza, te auditimi dhe te mesazhi


def test_the_message_carries_the_link_and_no_secret(world):
    world.forgot()
    message = world.outbox.to(EMAIL)[-1]
    assert "http://localhost:3000/reset-password?token=" in message.body
    assert "60 minuta" in message.body
    assert PASSWORD not in message.body


def test_audit_and_attempt_tables_hold_no_email(world):
    world.forgot()
    world.reset(reset_token_in(world.outbox.to(EMAIL)[-1]))
    from analyte.persistence.tables import AuditEventRow, RegistrationAttemptRow

    with world.db() as db:
        dump = str([e.payload for e in db.scalars(select(AuditEventRow))])
        assert "viktima" not in dump and "shembull" not in dump
        for row in db.scalars(select(RegistrationAttemptRow)):
            assert "viktima" not in row.email_key and "shembull" not in row.email_key
        assert any(
            row.email_key == keyed_hash(SECRET, "reset-email", EMAIL)
            for row in db.scalars(select(RegistrationAttemptRow))
        )


def test_a_reset_mail_failure_does_not_change_the_response(tmp_path):
    class Broken:
        def send(self, to, subject, body):
            raise ConnectionRefusedError(f"SMTP i pakapshëm për {to}")

    w = World(tmp_path, mailer=Broken())
    # llogaria krijohet drejtpërdrejt: me postë të prishur nuk ka lidhje konfirmimi për t'u hapur
    from analyte.persistence.tables import UserRow
    from analyte.security import hash_password

    with w.db() as db:
        db.add(
            UserRow(
                email=EMAIL,
                password_hash=hash_password(PASSWORD),
                email_confirmed_at=datetime.now(UTC),
            )
        )
        db.commit()
    response = w.forgot()
    assert response.status_code == 202
    assert response.json() == {"message": auth_module.RESET_REPLY}
    assert [e.payload for e in w.audit("mail.failed")] == [{"error_type": "ConnectionRefusedError"}]
