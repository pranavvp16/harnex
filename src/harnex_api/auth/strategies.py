from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from harnex_api.db.models import AuthFlow

ApiKeyLocation = Literal["header", "query"]


@dataclass(frozen=True)
class AuthCredentials:
    """Resolved secret material for one connection. Loaded from Infisical at execution time."""

    flow: AuthFlow
    values: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class AuthContext:
    """Everything an executor needs to inject auth into an outbound request."""

    flow: AuthFlow
    headers: dict[str, str] = field(default_factory=dict)
    query: dict[str, str] = field(default_factory=dict)
    basic_auth: tuple[str, str] | None = None


class AuthStrategy:
    """Build an AuthContext from a connection's auth_config + resolved credentials."""

    flow: AuthFlow

    def build(self, auth_config: dict[str, Any], creds: AuthCredentials) -> AuthContext:
        raise NotImplementedError


class NoAuthStrategy(AuthStrategy):
    flow = AuthFlow.none

    def build(self, auth_config: dict[str, Any], creds: AuthCredentials) -> AuthContext:
        return AuthContext(flow=self.flow)


class ApiKeyHeaderStrategy(AuthStrategy):
    flow = AuthFlow.api_key_header

    def build(self, auth_config: dict[str, Any], creds: AuthCredentials) -> AuthContext:
        header_name = auth_config.get("header_name") or "X-API-Key"
        prefix = auth_config.get("prefix") or ""
        token = creds.values.get("api_key", "")
        value = f"{prefix}{token}".strip() if prefix else token
        return AuthContext(flow=self.flow, headers={header_name: value})


class ApiKeyQueryStrategy(AuthStrategy):
    flow = AuthFlow.api_key_query

    def build(self, auth_config: dict[str, Any], creds: AuthCredentials) -> AuthContext:
        param_name = auth_config.get("query_name") or "api_key"
        token = creds.values.get("api_key", "")
        return AuthContext(flow=self.flow, query={param_name: token})


class BearerStrategy(AuthStrategy):
    flow = AuthFlow.bearer

    def build(self, auth_config: dict[str, Any], creds: AuthCredentials) -> AuthContext:
        token = creds.values.get("token", "")
        return AuthContext(flow=self.flow, headers={"Authorization": f"Bearer {token}"})


class BasicStrategy(AuthStrategy):
    flow = AuthFlow.basic

    def build(self, auth_config: dict[str, Any], creds: AuthCredentials) -> AuthContext:
        username = creds.values.get("username", "")
        password = creds.values.get("password", "")
        return AuthContext(flow=self.flow, basic_auth=(username, password))


class OAuthAuthCodeStrategy(AuthStrategy):
    flow = AuthFlow.oauth_authcode

    def build(self, auth_config: dict[str, Any], creds: AuthCredentials) -> AuthContext:
        access_token = creds.values.get("access_token", "")
        return AuthContext(flow=self.flow, headers={"Authorization": f"Bearer {access_token}"})


class OAuthClientCredStrategy(AuthStrategy):
    flow = AuthFlow.oauth_clientcred

    def build(self, auth_config: dict[str, Any], creds: AuthCredentials) -> AuthContext:
        access_token = creds.values.get("access_token", "")
        return AuthContext(flow=self.flow, headers={"Authorization": f"Bearer {access_token}"})


_STRATEGIES: dict[AuthFlow, AuthStrategy] = {
    AuthFlow.none: NoAuthStrategy(),
    AuthFlow.api_key_header: ApiKeyHeaderStrategy(),
    AuthFlow.api_key_query: ApiKeyQueryStrategy(),
    AuthFlow.bearer: BearerStrategy(),
    AuthFlow.basic: BasicStrategy(),
    AuthFlow.oauth_authcode: OAuthAuthCodeStrategy(),
    AuthFlow.oauth_clientcred: OAuthClientCredStrategy(),
}


def get_strategy(flow: AuthFlow) -> AuthStrategy:
    try:
        return _STRATEGIES[flow]
    except KeyError as exc:
        raise ValueError(f"unsupported auth flow: {flow}") from exc


__all__ = [
    "ApiKeyHeaderStrategy",
    "ApiKeyLocation",
    "ApiKeyQueryStrategy",
    "AuthContext",
    "AuthCredentials",
    "AuthStrategy",
    "BasicStrategy",
    "BearerStrategy",
    "NoAuthStrategy",
    "OAuthAuthCodeStrategy",
    "OAuthClientCredStrategy",
    "get_strategy",
]
