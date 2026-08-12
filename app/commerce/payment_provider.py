"""Payment-provider boundary for the first sellable MVP."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.config import Settings


class PaymentProviderUnavailable(Exception):
    pass


@dataclass(frozen=True, slots=True)
class ManualPaymentInstructions:
    card_number: str
    account_number: str
    account_name: str
    bank_name: str
    instructions: str


class PaymentProvider(Protocol):
    code: str


class ManualCardTransferProvider:
    """Configuration-backed Iranian card-transfer provider.

    This boundary deliberately performs no bank API call. Human review remains
    the source of payment approval for MVP.
    """

    code = "manual_card_transfer"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def instructions(self) -> ManualPaymentInstructions:
        card_number = self.settings.card_transfer_card_number.get_secret_value().strip()
        account_number = self.settings.card_transfer_account_number.get_secret_value().strip()
        account_name = self.settings.card_transfer_account_name.strip()
        bank_name = self.settings.card_transfer_bank_name.strip()
        instructions = self.settings.card_transfer_instructions.strip()
        if not all((card_number, account_number, account_name, bank_name, instructions)):
            raise PaymentProviderUnavailable("Payment instructions are unavailable")
        return ManualPaymentInstructions(
            card_number=card_number,
            account_number=account_number,
            account_name=account_name,
            bank_name=bank_name,
            instructions=instructions,
        )
