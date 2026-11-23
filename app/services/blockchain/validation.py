"""
Address and tx-hash validation + EIP-55 checksum normalisation. Pure functions. Phase 1, step 1
(first code you write).
"""

import re
from typing import cast

from eth_typing import ChecksumAddress
from eth_utils.crypto import keccak

from app.services.blockchain.exceptions import InvalidAddressError, InvalidTxHashError

_ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
_TX_HASH_RE = re.compile(r"^0x[0-9a-fA-F]{64}$")


def _to_checksum(hex_body: str) -> str:
    """
    EIP-55: encode a checksum in the letter casing of a 40-char hex string.

    The hash is taken over the ASCII bytes of the *lowercase hex text*, not over
    the 20 raw address bytes. Each letter is uppercased when the hex digit of
    the digest at the same index is >= 8. Digits are left alone.
    """
    lower = hex_body.lower()
    digest = keccak(text=lower).hex()
    return "".join(
        ch.upper() if ch.isalpha() and int(digest[i], 16) >= 8 else ch for i, ch in enumerate(lower)
    )


def is_valid_address(value: object) -> bool:
    """
    True if `value` is a 0x-prefixed 40-hex-char string whose casing is either
    checksum-neutral (all lower / all upper) or a correct EIP-55 checksum.
    """
    if not isinstance(value, str) or not _ADDRESS_RE.fullmatch(value):
        return False
    body = value[2:]
    if body == body.lower() or body == body.upper():
        return True  # no checksum information present; format is valid
    return body == _to_checksum(body)


def normalize_address(value: object) -> ChecksumAddress:
    """Validate and return the EIP-55 checksummed form, or raise InvalidAddressError."""
    if not is_valid_address(value):
        raise InvalidAddressError("Invalid Ethereum address")
    assert isinstance(value, str)  # narrowed by is_valid_address; satisfies mypy
    return cast(ChecksumAddress, "0x" + _to_checksum(value[2:]))


def is_valid_tx_hash(value: object) -> bool:
    """True if `value` is a 0x-prefixed 64-hex-char string. Hashes carry no checksum."""
    return isinstance(value, str) and _TX_HASH_RE.fullmatch(value) is not None


def normalize_tx_hash(value: object) -> str:
    """Validate and return the lowercase form, or raise InvalidTxHashError."""
    if not is_valid_tx_hash(value):
        raise InvalidTxHashError("Invalid transaction hash")
    assert isinstance(value, str)
    return value.lower()
