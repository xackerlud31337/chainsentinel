"""Unit tests for wei <-> ether conversion."""

from decimal import Decimal

import pytest

from app.services.blockchain.units import (
    ETHER_DECIMALS,
    MAX_UINT256,
    WEI_PER_ETHER,
    ether_to_wei,
    wei_to_ether,
)


def test_why_float_is_forbidden() -> None:
    """Documents the reason this module exists: float cannot represent wei."""
    assert float(10**18 + 1) == float(10**18)
    assert Decimal(10**18 + 1) != Decimal(10**18)
    assert 0.1 + 0.2 != 0.3
    assert Decimal("0.1") + Decimal("0.2") == Decimal("0.3")


def test_constants() -> None:
    assert WEI_PER_ETHER == 10**ETHER_DECIMALS
    assert MAX_UINT256 == 2**256 - 1
    assert len(str(MAX_UINT256)) == 78


# --- wei_to_ether -----------------------------------------------------------


@pytest.mark.parametrize(
    ("wei", "ether"),
    [
        (0, Decimal("0")),
        (1, Decimal("0.000000000000000001")),
        (10**18, Decimal("1")),
        (10**18 + 1, Decimal("1.000000000000000001")),
        (15 * 10**17, Decimal("1.5")),
    ],
)
def test_wei_to_ether_exact_values(wei: int, ether: Decimal) -> None:
    assert wei_to_ether(wei) == ether


def test_wei_to_ether_max_uint256_is_exact() -> None:
    """Default Decimal precision (28 digits) would round a 78-digit value."""
    result = wei_to_ether(MAX_UINT256)
    assert (
        str(result)
        == "115792089237316195423570985008687907853269984665640564039457.584007913129639935"
    )


@pytest.mark.parametrize(
    "value",
    [
        pytest.param(True, id="bool"),
        pytest.param(1.0, id="float"),
        pytest.param("1", id="str"),
        pytest.param(Decimal(1), id="decimal"),
        pytest.param(None, id="none"),
    ],
)
def test_wei_to_ether_rejects_non_int(value: object) -> None:
    with pytest.raises(TypeError):
        wei_to_ether(value)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "value",
    [
        pytest.param(-1, id="negative"),
        pytest.param(MAX_UINT256 + 1, id="above-uint256"),
    ],
)
def test_wei_to_ether_rejects_out_of_range(value: int) -> None:
    with pytest.raises(ValueError):
        wei_to_ether(value)


# --- ether_to_wei -----------------------------------------------------------


@pytest.mark.parametrize(
    ("ether", "wei"),
    [
        pytest.param("0", 0, id="zero-str"),
        pytest.param("1", 10**18, id="one-str"),
        pytest.param(1, 10**18, id="one-int"),
        pytest.param(2, 2 * 10**18, id="two-int"),
        pytest.param("0.5", 5 * 10**17, id="half"),
        pytest.param(Decimal("1.50"), 15 * 10**17, id="trailing-zero"),
        pytest.param("1.000000000000000000", 10**18, id="eighteen-trailing-zeros"),
        pytest.param("1.000000000000000001", 10**18 + 1, id="exactly-18-decimals"),
        pytest.param("0.000000000000000001", 1, id="one-wei"),
        pytest.param("1E+2", 100 * 10**18, id="scientific-notation"),
        pytest.param(Decimal("1e-18"), 1, id="scientific-negative-exponent"),
    ],
)
def test_ether_to_wei_exact_values(ether: Decimal | str | int, wei: int) -> None:
    assert ether_to_wei(ether) == wei


@pytest.mark.parametrize(
    "wei",
    [0, 1, 999, 10**18, 10**18 + 1, 123456789012345678901234567890, MAX_UINT256],
)
def test_round_trip(wei: int) -> None:
    assert ether_to_wei(wei_to_ether(wei)) == wei


def test_large_integer_part_with_18_decimals_is_exact() -> None:
    integer_part = "1" * 60
    assert ether_to_wei(integer_part + ".123456789012345678") == int(
        integer_part + "123456789012345678"
    )


def test_regression_normalize_rounding_does_not_hide_19th_decimal() -> None:
    """
    Regression: Decimal.normalize() rounds to the active context. Under the default
    28-digit precision this 29-significant-digit value was rounded to 18 decimals,
    passed the fractional-digit check, and lost its last digit silently. The check
    must run inside the high-precision context.
    """
    with pytest.raises(ValueError, match="fractional"):
        ether_to_wei("1234567890.1234567890123456789")
    with pytest.raises(ValueError, match="fractional"):
        ether_to_wei("1" * 60 + ".1234567890123456789")


@pytest.mark.parametrize(
    "value",
    [
        pytest.param(1.5, id="float"),
        pytest.param(0.0, id="float-zero"),
        pytest.param(True, id="bool"),
    ],
)
def test_ether_to_wei_rejects_float_and_bool(value: object) -> None:
    with pytest.raises(TypeError):
        ether_to_wei(value)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "value",
    [
        pytest.param("abc", id="not-a-number"),
        pytest.param("", id="empty"),
        pytest.param("NaN", id="nan"),
        pytest.param("Infinity", id="inf"),
        pytest.param("-Infinity", id="neg-inf"),
        pytest.param(Decimal("NaN"), id="decimal-nan"),
        pytest.param("-1", id="negative"),
        pytest.param("-0.000000000000000001", id="negative-one-wei"),
        pytest.param("1.0000000000000000001", id="19-decimals"),
        pytest.param(Decimal(MAX_UINT256), id="above-uint256"),
    ],
)
def test_ether_to_wei_rejects_invalid_values(value: Decimal | str) -> None:
    with pytest.raises(ValueError):
        ether_to_wei(value)


def test_error_messages_do_not_echo_input() -> None:
    hostile = "9" * 50 + ".1234567890123456789"
    with pytest.raises(ValueError) as exc_info:
        ether_to_wei(hostile)
    assert hostile not in str(exc_info.value)
