"""Shared pytest configuration for the test suite."""

from __future__ import annotations

import inspect
from types import SimpleNamespace
from typing import Any

import aiohttp

# aiohttp 3.14 added a required keyword-only ``stream_writer`` argument to
# ``ClientResponse.__init__``. aioresponses (<= 0.7.9) builds mocked responses
# without it, so every mocked request raises
# ``TypeError: ... missing 1 required keyword-only argument: 'stream_writer'``.
# ``ClientResponse`` only reads ``stream_writer.output_size``, so a tiny stub
# is enough. Tracked upstream in pnuckowski/aioresponses#289 (fix in #288).
#
# The signature guard makes this a no-op on aiohttp < 3.14 and once
# aioresponses supplies the argument itself. Remove the shim at that point.
_response_init = aiohttp.ClientResponse.__init__

if "stream_writer" in inspect.signature(_response_init).parameters:

    def _patched_response_init(
        self: aiohttp.ClientResponse, *args: Any, **kwargs: Any
    ) -> None:
        kwargs.setdefault("stream_writer", SimpleNamespace(output_size=0))
        _response_init(self, *args, **kwargs)

    aiohttp.ClientResponse.__init__ = _patched_response_init  # type: ignore[method-assign]
