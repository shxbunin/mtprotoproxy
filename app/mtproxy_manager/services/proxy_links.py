from __future__ import annotations

from urllib.parse import urlencode

from mtproxy_manager.core.config import Settings


class ProxyLinkService:
    def __init__(self, settings: Settings):
        self._settings = settings

    def build_link(self, proxy_secret: str) -> str:
        secret = self._format_secret(proxy_secret)
        params = urlencode(
            {
                "server": self._settings.proxy_public_host,
                "port": self._settings.proxy_public_port,
                "secret": secret,
            },
            safe=":",
        )
        return f"tg://proxy?{params}"

    def _format_secret(self, proxy_secret: str) -> str:
        if self._settings.proxy_mode == "classic":
            return proxy_secret
        if self._settings.proxy_mode == "secure":
            return f"dd{proxy_secret}"
        return f"ee{proxy_secret}{self._settings.proxy_tls_domain.encode().hex()}"
