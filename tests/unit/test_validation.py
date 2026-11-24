"""Unit tests for address / tx-hash validation and EIP-55 normalisation."""

import pytest
from eth_utils.address import to_checksum_address

from app.services.blockchain.exceptions import InvalidAddressError, InvalidTxHashError
from app.services.blockchain.validation import (
    is_valid_address,
    is_valid_tx_hash,
    normalize_address,
    normalize_tx_hash,
)

# Test vectors from the EIP-55 specification, plus two well-known addresses.
EIP55_VECTORS = [
    "0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed",
    "0xfB6916095ca1df60bB79Ce92cE3Ea74c37c5d359",
    "0xdbF03B407c01E7cD3CBea99509d93f8DDDC8C6FB",
    "0xD1220A0cf47c7B9Be7A2E6BA89F429762e7b9aDb",
    "0x" + "0" * 40,  # zero address
    "0x" + "0" * 36 + "dEaD",  # burn address
]

INVALID_ADDRESSES = [
    pytest.param(None, id="none"),
    pytest.param(123, id="int"),
    pytest.param("", id="empty"),
    pytest.param("0x", id="prefix-only"),
    pytest.param("0X" + "a" * 40, id="uppercase-X-prefix"),
    pytest.param("0x" + "a" * 39, id="39-chars"),
    pytest.param("0x" + "a" * 41, id="41-chars"),
    pytest.param("a" * 40, id="missing-prefix"),
    pytest.param("0x" + "g" * 40, id="non-hex"),
    pytest.param("0x" + "а" * 40, id="cyrillic-a"),
    pytest.param(" 0x" + "a" * 40, id="leading-space"),
    pytest.param("0x" + "a" * 40 + "\n", id="trailing-newline"),
]


@pytest.mark.parametrize("address", EIP55_VECTORS)
def test_vectors_match_reference_implementation(address: str) -> None:
    assert len(address) == 42
    assert normalize_address(address) == to_checksum_address(address)


@pytest.mark.parametrize("address", EIP55_VECTORS)
def test_lowercase_and_uppercase_normalize_to_checksum(address: str) -> None:
    body = address[2:]
    expected = to_checksum_address(address)
    assert normalize_address("0x" + body.lower()) == expected
    assert normalize_address("0x" + body.upper()) == expected


@pytest.mark.parametrize("address", EIP55_VECTORS)
def test_correct_checksum_is_valid(address: str) -> None:
    assert is_valid_address(address)


def test_wrong_checksum_casing_is_rejected() -> None:
    address = EIP55_VECTORS[0]
    body = address[2:]
    # Flip the case of the first letter -> checksum no longer matches.
    first_letter = next(i for i, c in enumerate(body) if c.isalpha())
    flipped = body[:first_letter] + body[first_letter].swapcase() + body[first_letter + 1 :]
    assert not is_valid_address("0x" + flipped)
    with pytest.raises(InvalidAddressError):
        normalize_address("0x" + flipped)


@pytest.mark.parametrize("value", INVALID_ADDRESSES)
def test_invalid_addresses_are_rejected(value: object) -> None:
    assert not is_valid_address(value)
    with pytest.raises(InvalidAddressError):
        normalize_address(value)


def test_error_message_does_not_echo_input() -> None:
    hostile = "0x" + "g" * 40
    with pytest.raises(InvalidAddressError) as exc_info:
        normalize_address(hostile)
    assert hostile not in str(exc_info.value)


# --- transaction hashes ---------------------------------------------------

VALID_TX_HASH = "0x" + "ab" * 32


def test_valid_tx_hash() -> None:
    assert is_valid_tx_hash(VALID_TX_HASH)
    assert normalize_tx_hash(VALID_TX_HASH) == VALID_TX_HASH


def test_tx_hash_normalizes_to_lowercase() -> None:
    upper = "0x" + "AB" * 32
    assert is_valid_tx_hash(upper)
    assert normalize_tx_hash(upper) == VALID_TX_HASH


@pytest.mark.parametrize(
    "value",
    [
        pytest.param(None, id="none"),
        pytest.param("", id="empty"),
        pytest.param("0x" + "a" * 63, id="63-chars"),
        pytest.param("0x" + "a" * 65, id="65-chars"),
        pytest.param("ab" * 32, id="missing-prefix"),
        pytest.param("0X" + "a" * 64, id="uppercase-X-prefix"),
        pytest.param("0x" + "z" * 64, id="non-hex"),
        pytest.param(EIP55_VECTORS[0], id="address-length"),
    ],
)
def test_invalid_tx_hashes_are_rejected(value: object) -> None:
    assert not is_valid_tx_hash(value)
    with pytest.raises(InvalidTxHashError):
        normalize_tx_hash(value)
