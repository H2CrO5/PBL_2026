"""Concurrent local API smoke/load test for Student authentication and reads."""

from __future__ import annotations

import argparse
import asyncio
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import statistics
import time

import httpx


DEMO_STUDENTS = ("s2024001", "s2024002", "s2024003")
SESSION_ISOLATION_REQUESTS = 5


async def _one_user_flow(
    client: httpx.AsyncClient,
    base_url: str,
    student_code: str,
    semaphore: asyncio.Semaphore,
) -> dict:
    started = time.perf_counter()
    statuses = []
    error = None
    async with semaphore:
        try:
            login = await client.post(
                f"{base_url}/auth/login",
                json={"student_code": student_code, "password": "demo123"},
            )
            statuses.append(login.status_code)
            login.raise_for_status()
            headers = {"Authorization": f"Bearer {login.json()['token']}"}
            for path in (
                "/auth/me",
                "/dashboard/summary",
                "/dashboard/timeline?days=30",
                "/materials",
                "/assignments/pending",
            ):
                response = await client.get(f"{base_url}{path}", headers=headers)
                statuses.append(response.status_code)
                response.raise_for_status()
            logout = await client.post(f"{base_url}/auth/logout", headers=headers)
            statuses.append(logout.status_code)
            logout.raise_for_status()
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
    return {
        "student_code": student_code,
        "duration_ms": round((time.perf_counter() - started) * 1000, 1),
        "statuses": statuses,
        "error": error,
    }


async def _session_isolation(client: httpx.AsyncClient, base_url: str) -> bool:
    payload = {"student_code": DEMO_STUDENTS[0], "password": "demo123"}
    first, second = await asyncio.gather(
        client.post(f"{base_url}/auth/login", json=payload),
        client.post(f"{base_url}/auth/login", json=payload),
    )
    first.raise_for_status()
    second.raise_for_status()
    first_headers = {"Authorization": f"Bearer {first.json()['token']}"}
    second_headers = {"Authorization": f"Bearer {second.json()['token']}"}
    logout = await client.post(f"{base_url}/auth/logout", headers=first_headers)
    still_active = await client.get(f"{base_url}/auth/me", headers=second_headers)
    await client.post(f"{base_url}/auth/logout", headers=second_headers)
    return logout.status_code == 200 and still_active.status_code == 200


async def run(base_url: str, requests: int, concurrency: int) -> dict:
    limits = httpx.Limits(
        max_connections=max(concurrency, 10),
        max_keepalive_connections=max(concurrency, 10),
    )
    async with httpx.AsyncClient(timeout=60.0, limits=limits) as client:
        isolation_ok = await _session_isolation(client, base_url)
        semaphore = asyncio.Semaphore(concurrency)
        results = await asyncio.gather(*[
            _one_user_flow(
                client,
                base_url,
                DEMO_STUDENTS[index % len(DEMO_STUDENTS)],
                semaphore,
            )
            for index in range(requests)
        ])

    durations = sorted(item["duration_ms"] for item in results)
    errors = [item for item in results if item["error"]]
    statuses = Counter(
        status for item in results for status in item["statuses"]
    )
    p95_index = min(len(durations) - 1, int(len(durations) * 0.95))
    return {
        "target": "student-concurrent-login-and-reads",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "flows": requests,
        "requests_per_flow": 7,
        "concurrency": concurrency,
        "session_isolation_http_requests": SESSION_ISOLATION_REQUESTS,
        "total_http_requests": (
            sum(len(item["statuses"]) for item in results)
            + SESSION_ISOLATION_REQUESTS
        ),
        "successful_flows": requests - len(errors),
        "failed_flows": len(errors),
        "failure_rate": round(len(errors) / requests, 4) if requests else 0,
        "session_isolation_passed": isolation_ok,
        "latency_ms": {
            "mean": round(statistics.mean(durations), 1) if durations else 0,
            "p50": durations[len(durations) // 2] if durations else 0,
            "p95": durations[p95_index] if durations else 0,
            "max": durations[-1] if durations else 0,
        },
        "status_counts": dict(sorted(statuses.items())),
        "errors": errors[:10],
        "passed": not errors and isolation_ok,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--student-url", default="http://127.0.0.1:8000")
    parser.add_argument("--requests", type=int, default=60)
    parser.add_argument("--concurrency", type=int, default=15)
    parser.add_argument("--out", default="eval/reports")
    args = parser.parse_args(argv)
    report = asyncio.run(run(
        args.student_url.rstrip("/"),
        max(1, args.requests),
        max(1, args.concurrency),
    ))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = out_dir / f"stress_{stamp}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Report: {path}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
