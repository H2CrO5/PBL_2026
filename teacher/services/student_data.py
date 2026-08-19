"""Read real Student analytics through the authenticated Student API boundary."""

from dataclasses import dataclass
from datetime import datetime
from urllib.parse import quote

import httpx

import config


class StudentDataUnavailable(RuntimeError):
    """Raised when live integration is enabled but cannot provide valid data."""


@dataclass
class LiveStudent:
    id: int
    student_code: str
    name: str
    average_score: float
    completion_rate: float
    total_submissions: int
    strong_topics: str
    weak_topics: str
    recommended_action: str
    recent_submissions: list[dict]
    chat_summary: list[str]


@dataclass
class LiveConcept:
    concept: str
    wrong_rate: float
    misconception: str
    recommended_focus: str


def integration_enabled() -> bool:
    return bool(config.STUDENT_INTEGRATION_TOKEN)


def _request(
    method: str,
    path: str,
    payload: dict | None = None,
    timeout: float | None = None,
) -> dict:
    try:
        response = httpx.request(
            method,
            f"{config.STUDENT_API_BASE_URL}{path}",
            headers={"X-Integration-Token": config.STUDENT_INTEGRATION_TOKEN},
            json=payload,
            timeout=timeout or config.STUDENT_API_TIMEOUT,
        )
        response.raise_for_status()
        result = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise StudentDataUnavailable(f"Student integration unavailable: {exc}") from exc
    if not isinstance(result, dict):
        raise StudentDataUnavailable("Student integration returned an invalid payload")
    return result


def fetch_feed(external_course_id: str | None = None) -> dict | None:
    """Return None only when integration is intentionally not configured."""
    if not integration_enabled():
        return None
    path = "/integrations/teacher/analytics"
    if external_course_id:
        path += f"?external_course_id={quote(external_course_id, safe='')}"
    feed = _request("GET", path)

    if not isinstance(feed, dict) or not isinstance(feed.get("students"), list):
        raise StudentDataUnavailable("Student analytics API returned an invalid payload")
    return feed


def sync_course(payload: dict) -> dict:
    return _request("POST", "/integrations/teacher/courses/sync", payload)


def publish_assignment(payload: dict) -> dict:
    return _request("POST", "/integrations/teacher/assignments/publish", payload)


def fetch_assignment_analytics(external_assignment_id: str) -> dict:
    return _request(
        "GET",
        f"/integrations/teacher/assignments/{quote(external_assignment_id, safe='')}/analytics",
    )


def sync_material(payload: dict) -> dict:
    return _request(
        "POST",
        "/integrations/teacher/materials/sync",
        payload,
        timeout=config.STUDENT_RAG_TIMEOUT,
    )


def override_grade(
    submission_id: int,
    external_course_id: str,
    score: float,
    feedback: str,
) -> dict:
    return _request(
        "POST",
        f"/integrations/teacher/submissions/{submission_id}/override",
        {
            "external_course_id": external_course_id,
            "score": score,
            "feedback": feedback,
        },
    )


def _recommended_action(weak_topics: list[str], submission_count: int) -> str:
    if submission_count == 0:
        return "No real submission yet; monitor assignment completion."
    if weak_topics:
        return "Focus follow-up practice on: " + ", ".join(weak_topics) + "."
    return "On track; continue with the next assignment."


def teacher_records(feed: dict) -> tuple[list[LiveStudent], list[LiveConcept], datetime | None]:
    import json

    students = []
    for item in feed.get("students", []):
        weak_topics = item.get("weak_topics", [])
        students.append(LiveStudent(
            id=int(item["student_id"]),
            student_code=str(item["student_code"]),
            name=str(item["name"]),
            average_score=float(item.get("average_score", 0)),
            completion_rate=float(item.get("completion_rate", 0)),
            total_submissions=int(item.get("total_submissions", 0)),
            strong_topics=json.dumps(item.get("strong_topics", []), ensure_ascii=False),
            weak_topics=json.dumps(weak_topics, ensure_ascii=False),
            recommended_action=_recommended_action(
                weak_topics, int(item.get("total_submissions", 0))
            ),
            recent_submissions=item.get("recent_submissions", []),
            chat_summary=item.get("chat_summary", []),
        ))

    concepts = [
        LiveConcept(
            concept=str(item["topic"]),
            wrong_rate=float(item.get("wrong_rate", 0)),
            misconception=(
                "; ".join(item.get("common_error_patterns", []))
                or (
                    f"{item.get('incorrect', 0)} of {item.get('attempts', 0)} real submissions "
                    "were graded incorrect."
                )
            ),
            recommended_focus=f"Review real student evidence for {item['topic']}.",
        )
        for item in feed.get("topic_metrics", [])
    ]

    generated_at = None
    raw_generated_at = feed.get("generated_at")
    if raw_generated_at:
        try:
            generated_at = datetime.fromisoformat(str(raw_generated_at).replace("Z", "+00:00"))
        except ValueError:
            generated_at = None
    return students, concepts, generated_at
