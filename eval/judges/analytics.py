"""Analytics-faithfulness judge (step 4, decoupled from the teacher module).

This does NOT import the teacher's analytics code. It takes the numeric facts
(the same schema the teacher consumes: concept_metrics + students, i.e.
teacher_feed.json), independently generates an analytics narration from those
numbers, then judges whether the narration is faithful to them. This makes the
gate a check on "can faithful analytics be produced from these numbers, and does
the judge catch a narration that invents figures it shouldn't."

Metric:
  - analytics_faithfulness : 0..1, does every quantitative claim in the
    narration follow from the given numbers (no invented students/rates/concepts)
"""

from __future__ import annotations

import json

NARRATE_SYSTEM = (
    "あなたはプログラミング講義の学習分析アシスタントです。"
    "与えられた数値と事実だけに基づいて分析文を書きます。"
    "与えられていない生徒・数値・概念を創作してはいけません。"
    "出力は必ず指定されたJSON形式のみで返してください。"
)

NARRATE_PROMPT = """\
以下は、ある講義の集計結果です（数値は確定値です）。

## 概念ごとの誤答率（JSON）
{concept_metrics}

## 生徒プロファイル（JSON）
{students}

上の数値だけを根拠に、教師向けの短い分析を作成してください。

## 出力形式（JSON）
{{
  "summary": "クラス全体の理解状況を2文以内で",
  "weak_concepts": ["誤答率の高い順に概念名を列挙"],
  "recommended_focus": "次回授業で重点的に扱うべきことを1文で"
}}

注意:
- 入力に無い数値・生徒名・概念を出さないでください。
- weak_concepts は誤答率の高い順に並べてください。
- 過度に一般化しないでください。平均点にばらつきがある場合（高得点の生徒がいる等）、
  クラス全体が一律に低いと断定せず、事実に即した表現にしてください。"""

JUDGE_SYSTEM = (
    "You are a strict fact-checker. You verify whether an analytics narration is "
    "faithful to the numeric facts it was derived from. Return ONLY JSON."
)

JUDGE_PROMPT = """\
## Numeric facts (the only ground truth)
concept_metrics:
{concept_metrics}

students:
{students}

## Analytics narration to verify (JSON)
{narration}

Judge FAITHFULNESS, not completeness. Omitting facts is acceptable and must not
be penalized — the narration need not mention every student or number. Only the
claims it *does* make must be supported by the facts.

Penalize only:
- invented figures, students, or concepts not in the facts,
- wrong wrong-rate rankings,
- statements that contradict the numbers (e.g. calling the whole class uniformly
  weak when a student's average is clearly high).

Score proportionally on a 0.0-1.0 scale: 1.0 when every stated claim is
supported; deduct in proportion to how much of the content is unsupported or
contradictory. Reserve scores below 0.5 for narrations that invent figures or
badly misrepresent the data.

Return ONLY JSON:
{{"analytics_faithfulness": 0.0, "rationale": "..."}}
"""


def _facts_blocks(facts: dict) -> tuple[str, str]:
    concept_metrics = json.dumps(facts.get("concept_metrics", []), ensure_ascii=False, indent=2)
    students = json.dumps(facts.get("students", []), ensure_ascii=False, indent=2)
    return concept_metrics, students


def generate_narration(provider, facts: dict) -> dict:
    """Independently generate an analytics narration from the numbers."""
    concept_metrics, students = _facts_blocks(facts)
    prompt = NARRATE_PROMPT.format(concept_metrics=concept_metrics, students=students)
    # Temperature 0.0: keep the narration deterministic and conservative so the
    # faithfulness gate is stable run-to-run.
    return provider.complete_json(
        prompt, system=NARRATE_SYSTEM, temperature=0.0, kind="analytics_narrate", seed="analytics"
    )


def judge_narration(provider, facts: dict, narration: dict) -> dict:
    """Score how faithful the narration is to the numbers (low temperature)."""
    concept_metrics, students = _facts_blocks(facts)
    prompt = JUDGE_PROMPT.format(
        concept_metrics=concept_metrics,
        students=students,
        narration=json.dumps(narration, ensure_ascii=False, indent=2),
    )
    return provider.complete_json(
        prompt, system=JUDGE_SYSTEM, temperature=0.0, kind="analytics_judge", seed="analytics_judge"
    )
