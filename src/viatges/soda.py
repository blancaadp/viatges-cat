"""Cliente mínimo para la API SODA de Socrata, con paginación y reintentos."""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx

log = logging.getLogger(__name__)

RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class SodaClient:
    def __init__(
        self,
        domain: str,
        app_token: str | None = None,
        app_secret: str | None = None,
        *,
        timeout: float = 30.0,
        max_retries: int = 4,
        backoff_base: float = 2.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        headers = {"Accept": "application/json"}
        auth: tuple[str, str] | None = None
        if app_token and app_secret:
            # Clau API nueva (ID + Secreto): requiere autenticación Basic.
            auth = (app_token, app_secret)
        elif app_token:
            # Token antiguo de un solo valor.
            headers["X-App-Token"] = app_token
        self._client = httpx.Client(
            base_url=f"https://{domain}",
            headers=headers,
            auth=auth,
            timeout=timeout,
            transport=transport,
        )
        self.max_retries = max_retries
        self.backoff_base = backoff_base

    def __enter__(self) -> SodaClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self._client.close()

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self._client.get(path, params=params)
                response.raise_for_status()
                return response.json()
            except (httpx.TransportError, httpx.HTTPStatusError) as exc:
                retryable = isinstance(exc, httpx.TransportError) or (
                    exc.response.status_code in RETRYABLE_STATUS
                )
                if not retryable or attempt == self.max_retries:
                    raise
                wait = self.backoff_base**attempt
                log.warning("Fallo en %s (%s). Reintento %d en %.0fs", path, exc, attempt, wait)
                time.sleep(wait)
        raise RuntimeError("inalcanzable")  # pragma: no cover

    def metadata(self, dataset_id: str) -> dict[str, Any]:
        """Metadatos del dataset: columnas, tipos, fecha de última actualización..."""
        return self._get(f"/api/views/{dataset_id}.json")

    def fetch_all(self, dataset_id: str, page_size: int = 1000) -> list[dict[str, Any]]:
        """Descarga todas las filas paginando. Ordena por :id para que la paginación sea estable."""
        rows: list[dict[str, Any]] = []
        offset = 0
        while True:
            page = self._get(
                f"/resource/{dataset_id}.json",
                params={"$limit": page_size, "$offset": offset, "$order": ":id"},
            )
            rows.extend(page)
            log.info("Página con offset %d: %d filas (total %d)", offset, len(page), len(rows))
            if len(page) < page_size:
                return rows
            offset += page_size
