"""LLM-backed narration for teacher analytics.

The numeric facts (wrong_rate, affected counts, seed titles, priorities) are
computed deterministically by the router and passed in here. This module only
turns those facts into explanatory prose via Bedrock, and validates the shape
of what the model returns. Any failure raises, so the router can fall back to
the deterministic rule-based narration.

Enabled only when config.USE_LLM is true (env var TEACHER_USE_LLM).
"""

import json
from threading import Lock
import time

from llm import bedrock_client, prompts


TEACHER_ACTION_CACHE_SECONDS = 300
TEACHER_ACTION_CACHE_MAX_ENTRIES = 128
_teacher_action_cache: dict[str, tuple[float, list[dict]]] = {}
_teacher_action_cache_lock = Lock()


def _as_str(value) -> str:
    return value.strip() if isinstance(value, str) else ""


def _as_str_list(value) -> list[str]:
    if not isinstance(value, list):
        return []
    return [v.strip() for v in value if isinstance(v, str) and v.strip()]


def narrate_evidence(concept_facts: list[dict], course_context: str = "") -> dict[str, dict]:
    """Return {concept -> {"typical_errors": [...], "recommended_action": str}}.

    `concept_facts` items: {concept, wrong_rate, misconception, affected_count}.
    Raises on an unusable response so the caller can fall back.
    """
    if not concept_facts:
        return {}

    prompt = prompts.EVIDENCE_PROMPT.format(
        concept_facts=json.dumps(concept_facts, ensure_ascii=False, indent=2),
        course_context=course_context or "（利用可能な教材文脈なし）",
    )
    result = bedrock_client.invoke_json(prompt, system=prompts.EVIDENCE_SYSTEM)

    items = result.get("items") if isinstance(result, dict) else None
    if not isinstance(items, list) or not items:
        raise ValueError("evidence narration missing 'items'")

    out: dict[str, dict] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        concept = _as_str(item.get("concept"))
        errors = _as_str_list(item.get("typical_errors"))
        action = _as_str(item.get("recommended_action"))
        if concept and errors and action:
            out[concept] = {"typical_errors": errors, "recommended_action": action}

    if not out:
        raise ValueError("evidence narration produced no usable items")
    return out


def narrate_lecture_plan(
    concept_facts: list[dict], seed_titles: list[str], course_context: str = ""
) -> dict:
    """Return the prose fields of a lecture plan.

    Keys: suggested_activity, opening_activity, review_sequence,
    in_class_check, follow_up_actions. Raises on an unusable response.
    """
    prompt = prompts.LECTURE_PLAN_PROMPT.format(
        concept_facts=json.dumps(concept_facts, ensure_ascii=False, indent=2),
        seed_titles=json.dumps(seed_titles, ensure_ascii=False),
        course_context=course_context or "（利用可能な教材文脈なし）",
    )
    result = bedrock_client.invoke_json(prompt, system=prompts.LECTURE_PLAN_SYSTEM)
    if not isinstance(result, dict):
        raise ValueError("lecture plan narration is not an object")

    plan = {
        "suggested_activity": _as_str(result.get("suggested_activity")),
        "opening_activity": _as_str(result.get("opening_activity")),
        "review_sequence": _as_str_list(result.get("review_sequence")),
        "in_class_check": _as_str(result.get("in_class_check")),
        "follow_up_actions": _as_str_list(result.get("follow_up_actions")),
    }
    # Require the free-text fields; lists may legitimately be short but not empty.
    if not plan["suggested_activity"] or not plan["opening_activity"]:
        raise ValueError("lecture plan narration missing required prose")
    if not plan["review_sequence"] or not plan["follow_up_actions"]:
        raise ValueError("lecture plan narration missing required lists")
    if not plan["in_class_check"]:
        raise ValueError("lecture plan narration missing in_class_check")
    return plan


def narrate_teacher_actions(action_facts: list[dict]) -> list[dict]:
    """Return teacher-action dicts with LLM-written reason/next_step.

    `action_facts` items carry a fixed {priority, title} plus context; the model
    fills reason/next_step. Order and count are preserved. Raises on mismatch.
    """
    if not action_facts:
        return []

    # Dashboard refreshes are frequent and the facts are deterministic. Use a
    # small single-flight cache so concurrent viewers do not make identical,
    # paid Bedrock calls. A changed score/completion fact produces a new key.
    cache_key = json.dumps(action_facts, ensure_ascii=False, sort_keys=True)
    with _teacher_action_cache_lock:
        now = time.monotonic()
        for key, (expires_at, _) in list(_teacher_action_cache.items()):
            if expires_at <= now:
                _teacher_action_cache.pop(key, None)

        cached = _teacher_action_cache.get(cache_key)
        if cached and cached[0] > now:
            return [dict(item) for item in cached[1]]

        prompt = prompts.TEACHER_ACTIONS_PROMPT.format(
            action_facts=json.dumps(action_facts, ensure_ascii=False, indent=2)
        )
        result = bedrock_client.invoke_json(prompt, system=prompts.TEACHER_ACTIONS_SYSTEM)

        items = result.get("items") if isinstance(result, dict) else None
        if not isinstance(items, list) or len(items) != len(action_facts):
            raise ValueError("teacher actions narration count mismatch")

        out: list[dict] = []
        for fact, item in zip(action_facts, items):
            if not isinstance(item, dict):
                raise ValueError("teacher action item is not an object")
            reason = _as_str(item.get("reason"))
            next_step = _as_str(item.get("next_step"))
            if not reason or not next_step:
                raise ValueError("teacher action item missing reason/next_step")
            # Keep priority/title authoritative from the deterministic facts.
            out.append(
                {
                    "priority": fact["priority"],
                    "title": fact["title"],
                    "reason": reason,
                    "next_step": next_step,
                }
            )
        if len(_teacher_action_cache) >= TEACHER_ACTION_CACHE_MAX_ENTRIES:
            oldest_key = min(
                _teacher_action_cache,
                key=lambda key: _teacher_action_cache[key][0],
            )
            _teacher_action_cache.pop(oldest_key, None)
        _teacher_action_cache[cache_key] = (
            now + TEACHER_ACTION_CACHE_SECONDS,
            [dict(item) for item in out],
        )
        return out
