"""Domain exceptions for the blockchain layer. RPC-related ones join these in step 3."""


class InvalidAddressError(ValueError):
    """Raised when a value is not a well-formed Ethereum address."""


class InvalidTxHashError(ValueError):
    """Raised when a value is not a well-formed transaction hash."""
