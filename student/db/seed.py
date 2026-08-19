"""Seed the database with sample students, assignments, submissions, and chat messages."""

import json
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

import bcrypt

# Allow running as `python -m db.seed` from student/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.database import SessionLocal, create_tables
from db.models import Assignment, ChatMessage, Lecture, Student, Submission


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


# ── Sample questions per topic ─────────────────────────────────────────
SAMPLE_QUESTIONS = {
    "Python基礎": [
        {
            "question_text": "Pythonで変数 x に整数 10 を代入する正しい構文はどれですか？",
            "choices": json.dumps(["x := 10", "int x = 10", "x = 10", "var x = 10"]),
            "correct_answer": "x = 10",
            "explanation": "Pythonでは型宣言不要で、= 演算子で代入します。",
            "question_type": "multiple_choice",
            "difficulty": "easy",
        },
        {
            "question_text": "リスト [1, 2, 3] の長さを取得する関数は何ですか？",
            "choices": json.dumps(["size([1,2,3])", "len([1,2,3])", "[1,2,3].length()", "count([1,2,3])"]),
            "correct_answer": "len([1,2,3])",
            "explanation": "Pythonの組み込み関数 len() でシーケンスの長さを取得できます。",
            "question_type": "multiple_choice",
            "difficulty": "easy",
        },
        {
            "question_text": "Pythonにおけるリスト内包表記を使って、1から10までの偶数のリストを作成するコードを書いてください。",
            "choices": None,
            "correct_answer": "[x for x in range(1, 11) if x % 2 == 0]",
            "explanation": "リスト内包表記は [式 for 変数 in イテラブル if 条件] の形式です。",
            "question_type": "code",
            "difficulty": "medium",
        },
        {
            "question_text": "Pythonのデコレータの役割を簡潔に説明してください。",
            "choices": None,
            "correct_answer": "関数やクラスの振る舞いを変更・拡張するための構文で、@記号を使って適用する。",
            "explanation": "デコレータは関数を引数に取り、新しい関数を返す高階関数です。ログ出力、認証チェック等に使われます。",
            "question_type": "short_answer",
            "difficulty": "hard",
        },
        {
            "question_text": "次のうち、Pythonのイミュータブル（変更不可）な型はどれですか？",
            "choices": json.dumps(["list", "dict", "tuple", "set"]),
            "correct_answer": "tuple",
            "explanation": "タプルは一度作成すると要素の変更ができないイミュータブルな型です。",
            "question_type": "multiple_choice",
            "difficulty": "easy",
        },
    ],
    "データ構造": [
        {
            "question_text": "スタック(Stack)のデータ操作方式は何ですか？",
            "choices": json.dumps(["FIFO", "LIFO", "FILO", "ランダム"]),
            "correct_answer": "LIFO",
            "explanation": "スタックはLIFO（Last In, First Out）方式で、最後に追加された要素が最初に取り出されます。",
            "question_type": "multiple_choice",
            "difficulty": "easy",
        },
        {
            "question_text": "ハッシュテーブルの平均的な検索時間計算量はどれですか？",
            "choices": json.dumps(["O(n)", "O(log n)", "O(1)", "O(n log n)"]),
            "correct_answer": "O(1)",
            "explanation": "ハッシュテーブルはハッシュ関数により直接アクセスするため、平均O(1)です。",
            "question_type": "multiple_choice",
            "difficulty": "medium",
        },
        {
            "question_text": "二分探索木(BST)において、左の子ノードと右の子ノードの値の関係を説明してください。",
            "choices": None,
            "correct_answer": "左の子ノードの値は親ノードより小さく、右の子ノードの値は親ノードより大きい。",
            "explanation": "BSTの基本性質により、効率的な検索・挿入・削除が可能になります。",
            "question_type": "short_answer",
            "difficulty": "medium",
        },
        {
            "question_text": "キュー(Queue)に要素を追加する操作を何と呼びますか？",
            "choices": json.dumps(["push", "enqueue", "insert", "append"]),
            "correct_answer": "enqueue",
            "explanation": "キューでは追加をenqueue、取り出しをdequeueと呼びます。",
            "question_type": "multiple_choice",
            "difficulty": "easy",
        },
        {
            "question_text": "連結リスト(Linked List)の先頭への挿入の時間計算量はどれですか？",
            "choices": json.dumps(["O(1)", "O(n)", "O(log n)", "O(n²)"]),
            "correct_answer": "O(1)",
            "explanation": "連結リストの先頭への挿入は、ポインタの付け替えのみで済むためO(1)です。",
            "question_type": "multiple_choice",
            "difficulty": "medium",
        },
    ],
    "アルゴリズム": [
        {
            "question_text": "バブルソートの最悪時間計算量はどれですか？",
            "choices": json.dumps(["O(n)", "O(n log n)", "O(n²)", "O(log n)"]),
            "correct_answer": "O(n²)",
            "explanation": "バブルソートは隣接要素を比較・交換するため、最悪の場合 O(n²) となります。",
            "question_type": "multiple_choice",
            "difficulty": "easy",
        },
        {
            "question_text": "二分探索を適用するための前提条件は何ですか？",
            "choices": None,
            "correct_answer": "データがソート済みであること。",
            "explanation": "二分探索は中央値との比較で探索範囲を半分にするため、ソート済みデータが必要です。",
            "question_type": "short_answer",
            "difficulty": "easy",
        },
        {
            "question_text": "再帰関数に必ず必要な要素は何ですか？",
            "choices": json.dumps(["ループ文", "ベースケース(基底条件)", "グローバル変数", "例外処理"]),
            "correct_answer": "ベースケース(基底条件)",
            "explanation": "ベースケースがないと無限再帰に陥りスタックオーバーフローが発生します。",
            "question_type": "multiple_choice",
            "difficulty": "medium",
        },
        {
            "question_text": "BFS（幅優先探索）で使用する主なデータ構造は何ですか？",
            "choices": json.dumps(["スタック", "キュー", "ヒープ", "ハッシュテーブル"]),
            "correct_answer": "キュー",
            "explanation": "BFSは近い頂点から順に探索するため、FIFO構造のキューを使います。",
            "question_type": "multiple_choice",
            "difficulty": "medium",
        },
        {
            "question_text": "動的計画法(DP)の基本的な考え方を説明してください。",
            "choices": None,
            "correct_answer": "問題を部分問題に分割し、各部分問題の解をメモ化して再利用することで計算量を削減する手法。",
            "explanation": "DPは重複する部分問題を持つ最適化問題に有効で、メモ化により指数的な計算を多項式時間に改善します。",
            "question_type": "short_answer",
            "difficulty": "hard",
        },
    ],
}

# ── Lecture definitions ────────────────────────────────────────────────
# Lecture 1 & 2 = past (all answered), Lecture 3 = current (pending)
LECTURES = [
    {
        "lecture_number": 1,
        "title": "Python基礎入門",
        "description": "変数、型、基本構文を学びます。",
        "topic": "Python基礎",
        "days_ago": 21,
        "answered": True,   # past lecture -> all answered
    },
    {
        "lecture_number": 2,
        "title": "データ構造の基礎",
        "description": "スタック、キュー、連結リスト、ハッシュテーブルを学びます。",
        "topic": "データ構造",
        "days_ago": 14,
        "answered": True,   # past lecture -> all answered
    },
    {
        "lecture_number": 3,
        "title": "アルゴリズム入門",
        "description": "ソート、探索、再帰、動的計画法を学びます。",
        "topic": "アルゴリズム",
        "days_ago": 7,
        "answered": False,  # current lecture -> pending
    },
]

# ── Student profiles ───────────────────────────────────────────────────
# correct_rate determines how often the student answers correctly
STUDENTS = [
    {
        "student_code": "s2024001",
        "name": "田中太郎",
        "password": "demo123",
        "correct_rate": 0.75,  # 75% of answers correct
    },
    {
        "student_code": "s2024002",
        "name": "鈴木花子",
        "password": "demo123",
        "correct_rate": 0.50,
    },
    {
        "student_code": "s2024003",
        "name": "佐藤健二",
        "password": "demo123",
        "correct_rate": 0.92,
    },
]

# ── Chat samples ───────────────────────────────────────────────────────
CHAT_SAMPLES = [
    ("user", "Pythonのリスト内包表記について教えてください。"),
    (
        "assistant",
        "リスト内包表記は、既存のリストやイテラブルから新しいリストを簡潔に作成するための構文です。\n\n"
        "基本形: `[式 for 変数 in イテラブル]`\n\n"
        "例: `squares = [x**2 for x in range(10)]`\n\n"
        "条件付き: `[x for x in range(20) if x % 2 == 0]`\n\n"
        "通常のfor文より短く書け、Pythonらしいコードになります。",
    ),
    ("user", "スタックとキューの違いは何ですか？"),
    (
        "assistant",
        "スタックとキューはどちらも線形データ構造ですが、要素の取り出し順が異なります。\n\n"
        "**スタック (Stack)**\n- LIFO (Last In, First Out)\n- 最後に追加した要素を最初に取り出す\n- 例: ブラウザの「戻る」ボタン\n\n"
        "**キュー (Queue)**\n- FIFO (First In, First Out)\n- 最初に追加した要素を最初に取り出す\n- 例: プリンターの印刷待ち行列",
    ),
]


def _make_submission(q: dict, is_correct: bool) -> tuple[str, float, str]:
    """Generate a realistic answer, score, and feedback for a submission.

    Scoring rules:
      - multiple_choice: correct=100, incorrect=0 (binary)
      - short_answer:    correct=100, partial=50, incorrect=20
      - code:            correct=100, partial=60, incorrect=10
    """
    qtype = q["question_type"]

    if is_correct:
        answer = q["correct_answer"]
        score = 100.0
        feedback = "正解です！よく理解しています。"
    else:
        if qtype == "multiple_choice":
            choices_list = json.loads(q["choices"])
            wrong = [c for c in choices_list if c != q["correct_answer"]]
            answer = random.choice(wrong) if wrong else q["correct_answer"]
            score = 0.0
            feedback = f"不正解です。正解は「{q['correct_answer']}」です。{q['explanation']}"
        elif qtype == "code":
            # Partial attempt
            if random.random() < 0.5:
                answer = "# 方針は合っていますが構文エラーがあります\nfor x in range(1, 11):\n    if x % 2 == 0 print(x)"
                score = 60.0
                feedback = "方向性は合っていますが、構文に誤りがあります。printの前にコロンが必要です。"
            else:
                answer = "わかりません"
                score = 10.0
                feedback = f"解答が不十分です。{q['explanation']}"
        else:  # short_answer
            if random.random() < 0.5:
                answer = "よくわかりませんが、何かのデータの管理方法だと思います。"
                score = 20.0
                feedback = f"要点が不足しています。{q['explanation']}"
            else:
                answer = q["correct_answer"][:len(q["correct_answer"]) // 2] + "..."
                score = 50.0
                feedback = "部分的に合っていますが、もう少し具体的に説明する必要があります。"

    return answer, score, feedback


def seed():
    """Populate the database with sample data."""
    create_tables()
    db = SessionLocal()

    try:
        # Check if already seeded
        if db.query(Student).count() > 0:
            print("Database already seeded. Skipping.")
            return

        random.seed(42)
        now = datetime.utcnow()

        # ── Create lectures ───────────────────────────────────────────
        lecture_objs = {}  # topic -> Lecture
        for lec in LECTURES:
            lecture_date = now - timedelta(days=lec["days_ago"])
            deadline = lecture_date + timedelta(days=7)

            lecture = Lecture(
                lecture_number=lec["lecture_number"],
                title=lec["title"],
                description=lec["description"],
                lecture_date=lecture_date,
                deadline=deadline,
            )
            db.add(lecture)
            db.flush()
            lecture_objs[lec["topic"]] = {"obj": lecture, "answered": lec["answered"]}

        # ── Create students ──────────────────────────────────────────
        student_objs = []
        for s in STUDENTS:
            student = Student(
                student_code=s["student_code"],
                name=s["name"],
                password_hash=_hash_password(s["password"]),
                overall_score=0.0,
                total_answered=0,
                total_correct=0,
                weak_topics="[]",
                strong_topics="[]",
            )
            db.add(student)
            student_objs.append((student, s))
        db.flush()

        # ── Create assignments per lecture ────────────────────────────
        for student, profile in student_objs:
            correct_rate = profile["correct_rate"]
            all_scores = []
            total_answered = 0
            total_correct = 0

            for topic, lec_info in lecture_objs.items():
                lecture = lec_info["obj"]
                is_answered_lecture = lec_info["answered"]
                questions = SAMPLE_QUESTIONS[topic]

                for i, q in enumerate(questions):
                    # Assignment created around lecture date
                    created = lecture.lecture_date + timedelta(hours=random.randint(1, 24))

                    assignment = Assignment(
                        student_id=student.id,
                        lecture_id=lecture.id,
                        topic=topic,
                        difficulty=q["difficulty"],
                        question_text=q["question_text"],
                        choices=q["choices"],
                        correct_answer=q["correct_answer"],
                        explanation=q["explanation"],
                        question_type=q["question_type"],
                        created_at=created,
                    )
                    db.add(assignment)
                    db.flush()

                    # Past lectures: create submissions. Current lecture: leave pending.
                    if is_answered_lecture:
                        is_correct = random.random() < correct_rate
                        answer, score, feedback = _make_submission(q, is_correct)

                        submission = Submission(
                            assignment_id=assignment.id,
                            student_id=student.id,
                            answer_text=answer,
                            is_correct=is_correct,
                            score=score,
                            feedback=feedback,
                            source="seed",
                            submitted_at=created + timedelta(
                                hours=random.randint(1, 48),
                                minutes=random.randint(0, 59),
                            ),
                        )
                        db.add(submission)

                        all_scores.append(score)
                        total_answered += 1
                        if is_correct:
                            total_correct += 1

            # ── Update student aggregate stats ───────────────────────
            student.total_answered = total_answered
            student.total_correct = total_correct
            if all_scores:
                student.overall_score = round(sum(all_scores) / len(all_scores), 1)

            # Compute weak/strong topics from actual scores
            topic_scores: dict[str, list[float]] = {}
            for sub in db.query(Submission).filter(Submission.student_id == student.id).all():
                t = sub.assignment.topic
                topic_scores.setdefault(t, []).append(sub.score)

            weak = []
            strong = []
            for t, scores in topic_scores.items():
                avg = sum(scores) / len(scores)
                if avg < 60:
                    weak.append(t)
                elif avg >= 80:
                    strong.append(t)

            student.weak_topics = json.dumps(weak, ensure_ascii=False)
            student.strong_topics = json.dumps(strong, ensure_ascii=False)

            # ── Chat messages ──────────────────────────────────────
            for role, content in CHAT_SAMPLES[:2]:
                msg = ChatMessage(
                    student_id=student.id,
                    role=role,
                    content=content,
                    sources=json.dumps(["python_basics.md"]) if role == "assistant" else None,
                    created_at=now - timedelta(days=random.randint(0, 5)),
                )
                db.add(msg)

        db.commit()
        print(f"Seeded {len(STUDENTS)} students with {len(LECTURES)} lectures.")
        print("  Past lectures (1, 2): all assignments answered")
        print("  Current lecture (3): all assignments pending")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
