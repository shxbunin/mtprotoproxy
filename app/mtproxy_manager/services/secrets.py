from __future__ import annotations

import secrets


def generate_proxy_secret() -> str:
    return secrets.token_hex(16)
