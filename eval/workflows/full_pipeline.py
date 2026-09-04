"""Black-box Teacher-to-Student workflow evaluation."""

from datetime import datetime, timezone
import os

import httpx


def _checked(response: httpx.Response, step: str) -> dict | list:
    if response.status_code != 200:
        try:
            detail = response.json().get("detail", response.text[:300])
        except ValueError:
            detail = response.text[:300]
        raise RuntimeError(f"{step} returned HTTP {response.status_code}: {detail}")
    return response.json()


def run_full_pipeline(
    teacher_url: str,
    student_url: str,
) -> tuple[dict, list[dict]]:
    """Exercise lecture, material, assignment, submission, and progress APIs."""
    checks: dict[str, bool | str | int | float] = {}
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    course_external_id = os.getenv(
        "DEFAULT_COURSE_EXTERNAL_KEY",
        "course-generative-ai-2026",
    )
    try:
        with httpx.Client(timeout=180.0) as client:
            teacher_login = _checked(client.post(
                f"{teacher_url.rstrip('/')}/auth/login",
                json={"teacher_code": "t2024001", "password": "demo123"},
            ), "teacher login")
            teacher_headers = {"Authorization": f"Bearer {teacher_login['token']}"}
            checks["teacher_login"] = True

            student_login = _checked(client.post(
                f"{student_url.rstrip('/')}/auth/login",
                json={"student_code": "s2024001", "password": "demo123"},
            ), "student login")
            student_headers = {"Authorization": f"Bearer {student_login['token']}"}
            checks["student_login"] = True

            dashboard_before = _checked(client.get(
                f"{student_url.rstrip('/')}/dashboard/summary",
                headers=student_headers,
            ), "dashboard before")
            teacher_dashboard = _checked(client.get(
                f"{teacher_url.rstrip('/')}/analytics/dashboard",
                headers=teacher_headers,
            ), "teacher dashboard")
            lectures = _checked(client.get(
                f"{teacher_url.rstrip('/')}/materials/lectures",
                headers=teacher_headers,
            ), "list lectures")
            lecture_number = max(
                (item["lecture_number"] for item in lectures),
                default=0,
            ) + 1
            lecture = _checked(client.post(
                f"{teacher_url.rstrip('/')}/materials/lectures",
                headers=teacher_headers,
                json={
                    "course_id": teacher_dashboard["course_id"],
                    "lecture_number": lecture_number,
                    "title": f"Workflow Evaluation {stamp}",
                    "learning_objectives": [
                        "Explain how evidence supports a claim",
                        "Complete a grounded assignment",
                    ],
                },
            ), "create lecture")
            checks["lecture_created"] = True

            material_title = f"Workflow Material {stamp}"
            material_content = (
                "# Evidence grounding\n\n"
                "Grounded answers connect each important claim to relevant "
                "course evidence and explain why that evidence supports the claim."
            )
            material = _checked(client.post(
                f"{teacher_url.rstrip('/')}/materials/upload",
                headers=teacher_headers,
                data={
                    "course_id": str(teacher_dashboard["course_id"]),
                    "lecture_id": str(lecture["id"]),
                    "title": material_title,
                    "student_visible": True,
                },
                files={
                    "file": (
                        f"workflow-{stamp}.md",
                        material_content.encode("utf-8"),
                        "text/markdown",
                    ),
                },
            ), "upload and synchronize material")
            checks["material_indexed"] = material["ingestion_status"] in {
                "ready_bedrock", "ready_lexical"
            }

            visible_materials = _checked(client.get(
                f"{student_url.rstrip('/')}/materials",
                headers=student_headers,
                params={"external_course_id": course_external_id},
            ), "student material list after publish")
            checks["material_visible_to_student"] = any(
                item["external_material_id"] == material["external_key"]
                and "Grounded answers" in item["content"]
                for item in visible_materials
            )

            _checked(client.patch(
                f"{teacher_url.rstrip('/')}/materials/{material['id']}/visibility",
                headers=teacher_headers,
                json={"student_visible": False},
            ), "hide material from students")
            hidden_materials = _checked(client.get(
                f"{student_url.rstrip('/')}/materials",
                headers=student_headers,
                params={"external_course_id": course_external_id},
            ), "student material list after hide")
            checks["material_hidden_from_student"] = all(
                item["external_material_id"] != material["external_key"]
                for item in hidden_materials
            )

            _checked(client.patch(
                f"{teacher_url.rstrip('/')}/materials/{material['id']}/visibility",
                headers=teacher_headers,
                json={"student_visible": True},
            ), "republish material to students")
            republished_materials = _checked(client.get(
                f"{student_url.rstrip('/')}/materials",
                headers=student_headers,
                params={"external_course_id": course_external_id},
            ), "student material list after republish")
            checks["material_republished_to_student"] = any(
                item["external_material_id"] == material["external_key"]
                for item in republished_materials
            )

            generated = _checked(client.post(
                f"{teacher_url.rstrip('/')}/assignments/generate-batch",
                headers=teacher_headers,
                json={
                    "course_id": teacher_dashboard["course_id"],
                    "lecture_id": lecture["id"],
                    "target_concept": "Evidence grounding",
                    "assignment_goal": (
                        "Generate one short question grounded in the uploaded material"
                    ),
                    "target_student_codes": ["s2024001"],
                    "difficulty": "easy",
                    "number_questions": 1,
                },
            ), "generate Bedrock assignment draft")
            generated_questions = generated.get("questions", [])
            checks["teacher_bedrock_draft_generated"] = (
                len(generated_questions) == 1
                and bool(generated_questions[0].get("question_text"))
                and bool(generated_questions[0].get("expected_answer"))
                and bool(generated_questions[0].get("rubric"))
            )

            seed = _checked(client.post(
                f"{teacher_url.rstrip('/')}/questions",
                headers=teacher_headers,
                json={
                    "course_id": teacher_dashboard["course_id"],
                    "lecture_id": lecture["id"],
                    "title": f"Workflow Assignment {stamp}",
                    "target_concept": "Evidence grounding",
                    "seed_type": "required",
                    "difficulty": "easy",
                    "question_text": "Why should an answer connect claims to course evidence?",
                    "expected_answer": (
                        "Evidence makes the reasoning verifiable and shows that each claim "
                        "is supported by the course material."
                    ),
                    "rubric": [
                        "Explains that evidence supports claims",
                        "Mentions verifiability",
                    ],
                    "points": 100,
                    "max_attempts": 1,
                },
            ), "create assignment seed")
            publication = _checked(client.post(
                f"{teacher_url.rstrip('/')}/questions/{seed['id']}/publish",
                headers=teacher_headers,
                json={"target_student_codes": ["s2024001"]},
            ), "publish assignment")
            checks["assignment_published"] = publication["created_for_students"] == 1

            pending = _checked(client.get(
                f"{student_url.rstrip('/')}/assignments/pending",
                headers=student_headers,
            ), "student pending assignments")
            assignment = next(
                item for item in pending
                if item.get("external_assignment_id", "").startswith(
                    publication["external_assignment_id"]
                )
            )
            checks["assignment_visible_to_student"] = True

            submission = _checked(client.post(
                f"{student_url.rstrip('/')}/assignments/submit",
                headers=student_headers,
                json={
                    "assignment_id": assignment["id"],
                    "answer_text": (
                        "Connecting claims to course evidence makes the answer verifiable "
                        "and demonstrates that the reasoning is supported."
                    ),
                },
            ), "student submission")
            checks["submission_graded"] = submission["score"] >= 0

            dashboard_after = _checked(client.get(
                f"{student_url.rstrip('/')}/dashboard/summary",
                headers=student_headers,
            ), "dashboard after")
            checks["progress_incremented"] = (
                dashboard_after["completed_assignments"]
                == dashboard_before["completed_assignments"] + 1
            )
            checks["progress_delta_returned"] = (
                submission.get("progress_change", {}).get("completed_after")
                == dashboard_after["completed_assignments"]
            )

            timeline = _checked(client.get(
                f"{student_url.rstrip('/')}/dashboard/timeline",
                headers=student_headers,
                params={"days": 365},
            ), "progress timeline")
            checks["timeline_updated"] = any(
                point["assignment_id"] == assignment["id"]
                for point in timeline["points"]
            )
            checks["completed_before"] = dashboard_before["completed_assignments"]
            checks["completed_after"] = dashboard_after["completed_assignments"]
            checks["submission_score"] = submission["score"]
    except Exception as exc:
        checks["error"] = str(exc)

    required = [
        "teacher_login",
        "student_login",
        "lecture_created",
        "material_indexed",
        "material_visible_to_student",
        "material_hidden_from_student",
        "material_republished_to_student",
        "teacher_bedrock_draft_generated",
        "assignment_published",
        "assignment_visible_to_student",
        "submission_graded",
        "progress_incremented",
        "progress_delta_returned",
        "timeline_updated",
    ]
    passed = all(checks.get(name) is True for name in required)
    metrics = {
        "workflow_success": 1.0 if passed else 0.0,
        "steps_passed": sum(checks.get(name) is True for name in required),
        "steps_total": len(required),
    }
    return metrics, [checks]
