"""
Dërgimi i email-eve (ADR 0016).

"""

from __future__ import annotations

import logging
import smtplib
import ssl
from dataclasses import dataclass, field
from email.message import EmailMessage
from typing import Protocol

from analyte.config import Settings

log = logging.getLogger("analyte.mail")


class Mailer(Protocol):
    def send(self, to: str, subject: str, body: str) -> None: ...


class MailConfigError(ValueError):
    """Konfigurimi i postës nuk është i plotë: shërbimi nuk nis në heshtje pa email."""


class SmtpMailer:
    def __init__(
        self,
        host: str,
        port: int,
        sender: str,
        *,
        username: str = "",
        password: str = "",
        security: str = "starttls",
        timeout: float = 10.0,
    ) -> None:
        self.host, self.port, self.sender = host, port, sender
        self.username, self.password = username, password
        self.security, self.timeout = security, timeout

    def send(self, to: str, subject: str, body: str) -> None:
        message = EmailMessage()
        message["From"] = self.sender
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)

        context = ssl.create_default_context()
        if self.security == "ssl":
            connection: smtplib.SMTP = smtplib.SMTP_SSL(
                self.host, self.port, timeout=self.timeout, context=context
            )
        else:
            connection = smtplib.SMTP(self.host, self.port, timeout=self.timeout)
        with connection as smtp:
            if self.security == "starttls":
                smtp.starttls(context=context)
            if self.username:
                smtp.login(self.username, self.password)
            smtp.send_message(message)


class ConsoleMailer:
    def send(self, to: str, subject: str, body: str) -> None:
        log.warning("EMAIL (konsolë, vetëm zhvillim) për %s | %s\n%s", to, subject, body)


@dataclass(frozen=True, slots=True)
class Message:
    to: str
    subject: str
    body: str


@dataclass(slots=True)
class OutboxMailer:
    sent: list[Message] = field(default_factory=list)

    def send(self, to: str, subject: str, body: str) -> None:
        self.sent.append(Message(to, subject, body))

    def to(self, address: str) -> list[Message]:
        return [m for m in self.sent if m.to == address]


def build_mailer(settings: Settings) -> Mailer:
    if settings.mail_backend == "console":
        return ConsoleMailer()
    if not settings.smtp_host:
        raise MailConfigError(
            "ANALYTE_SMTP_HOST mungon. Vendosni kredencialet e kutisë së provës (Mailtrap) te `.env`, "
            "ose ANALYTE_MAIL_BACKEND=console për zhvillim pa SMTP."
        )
    password = settings.smtp_password.get_secret_value() if settings.smtp_password else ""
    return SmtpMailer(
        settings.smtp_host,
        settings.smtp_port,
        settings.mail_from,
        username=settings.smtp_username,
        password=password,
        security=settings.smtp_security,
    )


# Mesazhet


def confirmation_message(link: str, hours: int) -> tuple[str, str]:
    return (
        "Konfirmoni email-in tuaj në ANALYTE",
        "Përshëndetje,\n\n"
        "Dikush krijoi një llogari në ANALYTE me këtë email. Për ta aktivizuar, hapni lidhjen:\n\n"
        f"{link}\n\n"
        f"Lidhja vlen {hours} orë dhe përdoret një herë.\n\n"
        "Nëse nuk e keni kërkuar ju, mos e hapni lidhjen: llogaria nuk aktivizohet pa të.\n",
    )


def password_reset_message(link: str, minutes: int) -> tuple[str, str]:
    return (
        "Rivendosni fjalëkalimin tuaj në ANALYTE",
        "Përshëndetje,\n\n"
        "Dikush kërkoi të rivendosë fjalëkalimin e llogarisë suaj në ANALYTE. Për të vendosur një të ri, hapni lidhjen:\n\n"
        f"{link}\n\n"
        f"Lidhja vlen {minutes} minuta dhe përdoret një herë. Pasi ta përdorni, të gjitha seancat e hapura mbyllen.\n\n"
        "Nëse nuk e keni kërkuar ju, mos e hapni lidhjen: fjalëkalimi juaj nuk ka ndryshuar dhe nuk nevojitet asnjë veprim.\n",
    )


def already_registered_message(login_link: str) -> tuple[str, str]:
    return (
        "Ky email ka tashmë llogari në ANALYTE",
        "Përshëndetje,\n\n"
        "Dikush u përpoq të krijojë një llogari në ANALYTE me këtë email, por ai ka tashmë llogari.\n\n"
        f"Nëse ishit ju, hyni këtu: {login_link}\n\n"
        "Nëse nuk ishit ju, nuk nevojitet asnjë veprim; llogaria juaj nuk ka ndryshuar.\n",
    )
