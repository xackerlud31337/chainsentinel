"""
Conversions between wei (the integer base unit) and ether (human-readable).

Rules:
  - wei is always `int`. Balances go up to 2**256 - 1 (78 decimal digits).
  - ether is always `Decimal`. Never `float`: a float has ~16 significant
    digits and cannot even represent 10**18 + 1 wei exactly.
  - No silent rounding anywhere. If a value cannot be represented exactly,
    we raise.
"""

from decimal import Decimal, InvalidOperation, localcontext

WEI_PER_ETHER: int = 10**18
ETHER_DECIMALS: int = 18

# Largest value an EVM uint256 can hold. Anything above this did not come from a chain.
MAX_UINT256: int = 2**256 - 1

# Decimal's default context has 28 digits of precision. MAX_UINT256 has 78.
# Any arithmetic on wei-scale numbers must run with at least that much room.
_PRECISION: int = 100


def wei_to_ether(wei: int) -> Decimal:
    """
    Exact conversion from wei to ether.

    Raises TypeError for bool/float/str (bool is excluded explicitly because it
    subclasses int) and ValueError for negatives or values above uint256.
    """
    if isinstance(wei, bool) or not isinstance(wei, int):
        raise TypeError(f"wei must be int, got {type(wei).__name__}")
    if wei < 0:
        raise ValueError("wei cannot be negative")
    if wei > MAX_UINT256:
        raise ValueError("wei exceeds uint256")
    with localcontext() as ctx:
        ctx.prec = _PRECISION
        return Decimal(wei) / Decimal(WEI_PER_ETHER)


def ether_to_wei(ether: Decimal | str | int) -> int:
    """
    Exact conversion from ether to wei.

    Accepts Decimal, a decimal string ("0.5"), or int. Rejects float outright:
    by the time a float reaches us the precision is already gone, so converting
    it would only hide the caller's bug.

    Raises TypeError on float/bool, ValueError on NaN/Infinity, negatives,
    more than 18 fractional digits, or results above uint256.
    """
    if isinstance(ether, bool | float):
        raise TypeError(f"ether must be Decimal, str or int, got {type(ether).__name__}")

    # Everything below runs at high precision. normalize() and the multiplication
    # both round to the active context, and the default 28 digits is not enough
    # for a 60-digit integer part plus 18 fractional digits.
    with localcontext() as ctx:
        ctx.prec = _PRECISION
        try:
            value = Decimal(ether)
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise ValueError("ether is not a valid decimal number") from exc
        if not value.is_finite():
            raise ValueError("ether must be finite")
        if value < 0:
            raise ValueError("ether cannot be negative")

        # as_tuple().exponent is negative for fractional digits: Decimal("1.5") -> -1.
        # Trailing zeros also count ("1.50" -> -2), so normalize() strips them first.
        exponent = value.normalize().as_tuple().exponent
        if isinstance(exponent, int) and -exponent > ETHER_DECIMALS:
            raise ValueError(f"ether has more than {ETHER_DECIMALS} fractional digits")

        wei = int(value * WEI_PER_ETHER)

    if wei > MAX_UINT256:
        raise ValueError("wei exceeds uint256")
    return wei
