"""Runtime adapters translate external agent traces into Citta events."""

from .generic import GenericJsonlAdapter

__all__ = ["GenericJsonlAdapter"]
