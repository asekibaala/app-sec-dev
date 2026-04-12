"""
settings.py — authentication and identity-provider configuration.

Local username/password auth is active today. The settings in this module create
an explicit seam for a future external identity provider such as Windows Active
Directory via OIDC federation.
"""

import os

from dotenv import load_dotenv

load_dotenv()

DEFAULT_AUTH_SECRET = "development-only-change-me-32-bytes-min"

# Current runtime mode.
# `local` uses FastAPI Users + PostgreSQL credentials.
# `external_oidc` is reserved for a future secure AD/Entra/ADFS integration.
AUTH_PROVIDER_MODE = os.getenv("AUTH_PROVIDER_MODE", "local")

# FastAPI Users JWT signing secret.
APP_AUTH_SECRET = os.getenv("APP_AUTH_SECRET", DEFAULT_AUTH_SECRET)

# Future-facing OIDC settings for enterprise identity providers.
# For Windows Active Directory, prefer federation through Entra ID / ADFS /
# OIDC rather than raw LDAP password binds. That keeps MFA, conditional access,
# and central account policy enforcement in the IdP.
OIDC_DISCOVERY_URL = os.getenv("OIDC_DISCOVERY_URL", "")
OIDC_CLIENT_ID = os.getenv("OIDC_CLIENT_ID", "")
OIDC_CLIENT_SECRET = os.getenv("OIDC_CLIENT_SECRET", "")
OIDC_SCOPES = os.getenv("OIDC_SCOPES", "openid profile email")
