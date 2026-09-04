"""Concurrent Teacher API and Bedrock draft-generation stress test."""

from __future__ import annotations

import argparse
import asyncio
from collections import Counter
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import statistics
import time

import httpx


DEMO_TEACHER = {"teacher_code": "t2024001", "password": "demo123"}


def _latencies(values: list[float]) -> dict:
    ordered = sorted(values)
    if not ordered:
        return {"mean": 0, "p50": 0, "p95": 0, "max": 0}
    p95_index = max(0, math.ceil(len(ordered) * 0.95) - 1)
    return {
        "mean": round(statistics.mean(ordered), 1),
        "p50": ordered[len(ordered) // 2],
        "p95": ordered[p95_index],
        "max": ordered[-1],
    }


async def _teacher_flow(
    client: httpx.AsyncClient,
    base_url: str,
    semaphore: asyncio.Semaphore,
) -> dict:
    started = time.perf_counter()
    statuses: list[int] = []
    error = None
    async with semaphore:
        try:
            login = await client.post(f"{base_url}/auth/login", json=DEMO_TEACHER)
            statuses.append(login.status_code)
            login.raise_for_status()
            headers = {"Authorization": f"Bearer {login.json()['token']}"}

            me = await client.get(f"{base_url}/auth/me", headers=headers)
            statuses.append(me.status_code)
            me.raise_for_status()
            dashboard = await client.get(
                f"{base_url}/analytics/dashboard", headers=headers
            )
            statuses.append(dashboard.status_code)
            dashboard.raise_for_status()
            lectures = await client.get(
                f"{base_url}/materials/lectures", headers=headers
            )
            statuses.append(lectures.status_code)
            lectures.raise_for_status()
            lecture_rows = lectures.json()
            if not lecture_rows:
                raise RuntimeError("No lecture is available for generation context")

            for path in (
                "/materials",
                "/questions",
                "/students/insights",
                "/assignments",
                f"/questions/generation-context/{lecture_rows[0]['id']}",
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
        "duration_ms": round((time.perf_counter() - started) * 1000, 1),
        "statuses": statuses,
        "error": error,
    }


async def _session_isolation(
    client: httpx.AsyncClient,
    base_url: str,
) -> dict:
    statuses: list[int] = []
    error = None
    passed = False
    try:
        first, second = await asyncio.gather(
            client.post(f"{base_url}/auth/login", json=DEMO_TEACHER),
            client.post(f"{base_url}/auth/login", json=DEMO_TEACHER),
        )
        statuses.extend([first.status_code, second.status_code])
        first.raise_for_status()
        second.raise_for_status()
        first_headers = {"Authorization": f"Bearer {first.json()['token']}"}
        second_headers = {"Authorization": f"Bearer {second.json()['token']}"}
        logout = await client.post(f"{base_url}/auth/logout", headers=first_headers)
        still_active = await client.get(f"{base_url}/auth/me", headers=second_headers)
        cleanup = await client.post(f"{base_url}/auth/logout", headers=second_headers)
        statuses.extend([
            logout.status_code,
            still_active.status_code,
            cleanup.status_code,
        ])
        passed = all(status == 200 for status in statuses)
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    return {"passed": passed, "statuses": statuses, "error": error}


async def _generation_request(
    client: httpx.AsyncClient,
    base_url: str,
    headers: dict[str, str],
    payload: dict,
    index: int,
    semaphore: asyncio.Semaphore,
) -> dict:
    started = time.perf_counter()
    status = None
    error = None
    title = None
    async with semaphore:
        try:
            request_payload = dict(payload)
            request_payload["assignment_goal"] = (
                "Teacher concurrency validation draft " + str(index + 1)
            )
            response = await client.post(
                f"{base_url}/assignments/generate-batch",
                headers=headers,
                json=request_payload,
            )
            status = response.status_code
            response.raise_for_status()
            questions = response.json().get("questions", [])
            if len(questions) != 1:
                raise RuntimeError("Generation did not return exactly one draft")
            title = questions[0].get("title")
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
    return {
        "duration_ms": round((time.perf_counter() - started) * 1000, 1),
        "status": status,
        "title": title,
        "error": error,
    }


async def _generation_load(
    client: httpx.AsyncClient,
    base_url: str,
    requests: int,
    concurrency: int,
) -> dict:
    setup_statuses: list[int] = []
    if requests == 0:
        return {
            "requests": 0,
            "concurrency": concurrency,
            "successful": 0,
            "failed": 0,
            "duration_seconds": 0,
            "requests_per_second": 0,
            "latency_ms": _latencies([]),
            "statuses": [],
            "setup_statuses": [],
            "errors": [],
        }

    try:
        login = await client.post(f"{base_url}/auth/login", json=DEMO_TEACHER)
        setup_statuses.append(login.status_code)
        login.raise_for_status()
        headers = {"Authorization": f"Bearer {login.json()['token']}"}
        dashboard = await client.get(f"{base_url}/analytics/dashboard", headers=headers)
        setup_statuses.append(dashboard.status_code)
        dashboard.raise_for_status()
        lectures = await client.get(f"{base_url}/materials/lectures", headers=headers)
        setup_statuses.append(lectures.status_code)
        lectures.raise_for_status()
        lecture_rows = lectures.json()
        if not lecture_rows:
            raise RuntimeError("No lecture is available for draft generation")
        payload = {
            "course_id": dashboard.json()["course_id"],
            "lecture_id": lecture_rows[0]["id"],
            "target_concept": "Edge-case handling",
            "target_student_codes": ["s2024001"],
            "difficulty": "easy",
            "number_questions": 1,
        }
        semaphore = asyncio.Semaphore(concurrency)
        started = time.perf_counter()
        results = await asyncio.gather(*[
            _generation_request(
                client, base_url, headers, payload, index, semaphore
            )
            for index in range(requests)
        ])
        duration = time.perf_counter() - started
        logout = await client.post(f"{base_url}/auth/logout", headers=headers)
        setup_statuses.append(logout.status_code)
    except Exception as exc:
        return {
            "requests": requests,
            "concurrency": concurrency,
            "successful": 0,
            "failed": requests,
            "duration_seconds": 0,
            "requests_per_second": 0,
            "latency_ms": _latencies([]),
            "statuses": [],
            "setup_statuses": setup_statuses,
            "errors": [f"Generation setup failed: {type(exc).__name__}: {exc}"],
        }

    errors = [item for item in results if item["error"]]
    return {
        "requests": requests,
        "concurrency": concurrency,
        "successful": requests - len(errors),
        "failed": len(errors),
        "duration_seconds": round(duration, 3),
        "requests_per_second": round(requests / duration, 2) if duration else 0,
        "latency_ms": _latencies([item["duration_ms"] for item in results]),
        "statuses": [item["status"] for item in results if item["status"]],
        "setup_statuses": setup_statuses,
        "titles": [item["title"] for item in results if item["title"]],
        "errors": errors[:10],
    }


async def run(
    base_url: str,
    flows: int,
    concurrency: int,
    generation_requests: int,
    generation_concurrency: int,
) -> dict:
    maximum_connections = max(concurrency, generation_concurrency, 10)
    limits = httpx.Limits(
        max_connections=maximum_connections,
        max_keepalive_connections=maximum_connections,
    )
    async with httpx.AsyncClient(timeout=240.0, limits=limits) as client:
        isolation = await _session_isolation(client, base_url)
        semaphore = asyncio.Semaphore(concurrency)
        read_started = time.perf_counter()
        flow_results = await asyncio.gather(*[
            _teacher_flow(client, base_url, semaphore)
            for _ in range(flows)
        ])
        read_duration = time.perf_counter() - read_started
        generation = await _generation_load(
            client,
            base_url,
            generation_requests,
            generation_concurrency,
        )

    flow_errors = [item for item in flow_results if item["error"]]
    all_statuses = [
        status for item in flow_results for status in item["statuses"]
    ]
    all_statuses.extend(isolation["statuses"])
    all_statuses.extend(generation["setup_statuses"])
    all_statuses.extend(generation["statuses"])
    status_counts = Counter(all_statuses)
    passed = (
        isolation["passed"]
        and not flow_errors
        and generation["failed"] == 0
    )
    return {
        "target": "teacher-concurrent-sessions-reads-and-generation",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "read_phase": {
            "flows": flows,
            "requests_per_flow": 10,
            "concurrency": concurrency,
            "successful_flows": flows - len(flow_errors),
            "failed_flows": len(flow_errors),
            "failure_rate": round(len(flow_errors) / flows, 4) if flows else 0,
            "duration_seconds": round(read_duration, 3),
            "flow_throughput_per_second": (
                round(flows / read_duration, 2) if read_duration else 0
            ),
            "latency_ms": _latencies([
                item["duration_ms"] for item in flow_results
            ]),
            "errors": flow_errors[:10],
        },
        "generation_phase": generation,
        "session_isolation": isolation,
        "total_http_requests": len(all_statuses),
        "status_counts": dict(sorted(status_counts.items())),
        "passed": passed,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--teacher-url", default="http://127.0.0.1:8100")
    parser.add_argument("--flows", type=int, default=60)
    parser.add_argument("--concurrency", type=int, default=15)
    parser.add_argument("--generation-requests", type=int, default=0)
    parser.add_argument("--generation-concurrency", type=int, default=1)
    parser.add_argument("--out", default="eval/reports")
    args = parser.parse_args(argv)
    report = asyncio.run(run(
        args.teacher_url.rstrip("/"),
        max(1, args.flows),
        max(1, args.concurrency),
        max(0, args.generation_requests),
        max(1, args.generation_concurrency),
    ))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = out_dir / f"stress_teacher_{stamp}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Report: {path}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
