import json
import os
from pathlib import Path


def get_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_users(path):
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}

    users = payload.get("users", {})
    if not isinstance(users, dict):
        return {}

    return {
        str(user): str(secret)
        for user, secret in users.items()
        if isinstance(secret, str) and secret
    }


PROXY_MODE = os.getenv("PROXY_MODE", "tls").strip().lower() or "tls"
TLS_DOMAIN = os.getenv("PROXY_TLS_DOMAIN", "www.google.com")
MASK_HOST = os.getenv("PROXY_MASK_HOST", "").strip() or TLS_DOMAIN
ACTIVE_USERS_FILE = Path(os.getenv("PROXY_ACTIVE_USERS_FILE", "/runtime/active_users.json"))
LAST_SEEN_FILE = Path(os.getenv("PROXY_LAST_SEEN_FILE", "/runtime/last_seen.json"))
METRICS_PORT_RAW = os.getenv("PROXY_METRICS_PORT", "").strip()
METRICS_WHITELIST_RAW = os.getenv("PROXY_METRICS_WHITELIST", "127.0.0.1,::1")

PORT = int(os.getenv("PROXY_PORT", "443"))
USERS = load_users(ACTIVE_USERS_FILE)
MODES = {
    "classic": PROXY_MODE == "classic",
    "secure": PROXY_MODE == "secure",
    "tls": PROXY_MODE == "tls",
}
MASK = get_bool("PROXY_MASK", True)
MASK_PORT = int(os.getenv("PROXY_MASK_PORT", "443"))
MY_DOMAIN = os.getenv("PROXY_PUBLIC_HOST", "").strip() or False
AD_TAG = os.getenv("PROXY_AD_TAG", "").strip()
USE_MIDDLE_PROXY = get_bool("PROXY_USE_MIDDLE_PROXY", False)
FAST_MODE = get_bool("PROXY_FAST_MODE", True)
PREFER_IPV6 = get_bool("PROXY_PREFER_IPV6", False)
PROXY_PROTOCOL = get_bool("PROXY_PROTOCOL", False)
LISTEN_ADDR_IPV4 = os.getenv("PROXY_LISTEN_ADDR_IPV4", "0.0.0.0")
LISTEN_ADDR_IPV6 = os.getenv("PROXY_LISTEN_ADDR_IPV6", "::")
LISTEN_UNIX_SOCK = os.getenv("PROXY_LISTEN_UNIX_SOCK", "")
STATS_PRINT_PERIOD = int(os.getenv("PROXY_STATS_PRINT_PERIOD", "600"))
METRICS_PORT = int(METRICS_PORT_RAW) if METRICS_PORT_RAW else None
METRICS_WHITELIST = [value.strip() for value in METRICS_WHITELIST_RAW.split(",") if value.strip()]
