#!/usr/bin/env python3
"""Run lifecycle checks against a live Home Assistant."""

import argparse
import json
import ssl
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


def _request(base_url, token, path, *, method="GET", data=None):
    request = Request(
        f"{base_url.rstrip('/')}{path}",
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        data=json.dumps(data or {}).encode() if method != "GET" else None,
    )
    parsed = urlparse(base_url)
    context = None
    if parsed.scheme == "https" and parsed.hostname in {"localhost", "127.0.0.1", "::1"}:
        context = ssl._create_unverified_context()  # noqa: S323

    try:
        with urlopen(request, timeout=15, context=context) as response:
            body = response.read()
            return response.status, json.loads(body) if body else None
    except HTTPError as err:
        raise RuntimeError(f"Home Assistant returned HTTP {err.code} for {path}") from err
    except URLError as err:
        raise RuntimeError(f"Home Assistant is unreachable for {path}: {err.reason}") from err


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ha-url", required=True)
    parser.add_argument("--token", required=True)
    parser.add_argument("--entity-id", required=True)
    parser.add_argument(
        "--exercise-actions",
        action="store_true",
        help="Call open, close, and stop. Use only with a safe test cover.",
    )
    args = parser.parse_args()

    status, api = _request(args.ha_url, args.token, "/api/")
    if status != 200 or not isinstance(api, dict):
        raise SystemExit("Authenticated Home Assistant API health check failed.")

    status, entity = _request(args.ha_url, args.token, f"/api/states/{args.entity_id}")
    if status != 200 or not isinstance(entity, dict):
        raise SystemExit(f"PCC entity is unavailable: {args.entity_id}")

    status, entries = _request(args.ha_url, args.token, "/api/config/config_entries/entry")
    if status != 200 or not isinstance(entries, list):
        raise SystemExit("Could not inspect Home Assistant config entries.")

    pcc_entries = [entry for entry in entries if entry.get("domain") == "pcc"]
    if not pcc_entries:
        raise SystemExit("No loaded PCC config entry was found.")

    for entry in pcc_entries:
        _request(
            args.ha_url,
            args.token,
            f"/api/config/config_entries/entry/{entry['entry_id']}/reload",
            method="POST",
        )

    status, entity = _request(args.ha_url, args.token, f"/api/states/{args.entity_id}")
    if status != 200 or not isinstance(entity, dict):
        raise SystemExit("PCC entity did not recover after config entry reload.")

    if args.exercise_actions:
        expected_states = {
            "open_cover": "opening",
            "close_cover": "closing",
            "stop_cover": "closed",
        }
        for service, expected_state in expected_states.items():
            _request(
                args.ha_url,
                args.token,
                f"/api/services/cover/{service}",
                method="POST",
                data={"entity_id": args.entity_id},
            )
            _, entity = _request(
                args.ha_url,
                args.token,
                f"/api/states/{args.entity_id}",
            )
            if entity.get("state") != expected_state:
                raise SystemExit(
                    f"Expected {expected_state} after {service}, got {entity.get('state')}"
                )

    print(
        "LIVE ACCEPTANCE PASS: "
        f"authenticated API, {len(pcc_entries)} PCC entry reload, entity available"
        + (", open/close/stop actions" if args.exercise_actions else "")
    )


if __name__ == "__main__":
    main()
