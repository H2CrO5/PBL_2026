"""Internationalization: Japanese / English UI text."""

import streamlit as st

TRANSLATIONS = {
    # ── App / Sidebar ─────────────────────────────────────
    "role_label": {"ja": "Student", "en": "Student"},
    "navigation": {"ja": "ナビゲーション", "en": "Navigation"},
    "page_dashboard": {"ja": "ダッシュボード", "en": "Dashboard"},
    "page_assignments": {"ja": "課題", "en": "Assignments"},
    "page_materials": {"ja": "教材", "en": "Materials"},
    "page_ta_bot": {"ja": "TA Bot", "en": "TA Bot"},
    "logout": {"ja": "ログアウト", "en": "Logout"},
    "language": {"ja": "言語", "en": "Language"},

    # ── Login ─────────────────────────────────────────────
    "login_title": {"ja": "Student Login", "en": "Student Login"},
    "student_id": {"ja": "学生ID", "en": "Student ID"},
    "password": {"ja": "パスワード", "en": "Password"},
    "login_button": {"ja": "ログイン", "en": "Login"},
    "login_empty_error": {"ja": "学生IDとパスワードを入力してください。", "en": "Please enter your student ID and password."},
    "login_failed": {"ja": "ログインに失敗しました。", "en": "Login failed."},
    "login_connect_error": {"ja": "APIサーバーに接続できません。サーバーが起動しているか確認してください。", "en": "Cannot connect to the API server. Please check if the server is running."},
    "login_error": {"ja": "エラーが発生しました", "en": "An error occurred"},
    "demo_accounts": {"ja": "デモアカウント", "en": "Demo Accounts"},

    # ── Assignments ───────────────────────────────────────
    "assignments_title": {"ja": "課題", "en": "Assignments"},
    "tab_pending": {"ja": "未回答の課題", "en": "Pending"},
    "tab_history": {"ja": "解答履歴", "en": "History"},
    "no_pending": {"ja": "未回答の課題はありません。", "en": "No pending assignments."},
    "pending_count": {"ja": "{count}件 の未回答課題があります。", "en": "{count} pending assignment(s)."},
    "deadline": {"ja": "締切", "en": "Deadline"},
    "items_suffix": {"ja": "件", "en": " item(s)"},
    "answer_button": {"ja": "解答する", "en": "Answer"},
    "back_to_list": {"ja": "← 課題一覧に戻る", "en": "← Back to list"},
    "question_header": {"ja": "問題", "en": "Question"},
    "topic_label": {"ja": "トピック", "en": "Topic"},
    "difficulty_label": {"ja": "難易度", "en": "Difficulty"},
    "format_label": {"ja": "形式", "en": "Type"},
    "select_answer": {"ja": "回答を選択してください:", "en": "Select your answer:"},
    "enter_code": {"ja": "コードを入力してください:", "en": "Enter your code:"},
    "enter_answer": {"ja": "回答を入力してください:", "en": "Enter your answer:"},
    "submit_answer": {"ja": "回答を提出", "en": "Submit"},
    "answer_all": {"ja": "この回の問題にまとめて回答", "en": "Answer all questions in this lecture"},
    "submit_all": {"ja": "すべての回答を提出", "en": "Submit all answers"},
    "batch_result": {"ja": "{count}問を提出しました。合計 {score:.1f}/{max_score:.1f}", "en": "Submitted {count} questions. Total: {score:.1f}/{max_score:.1f}"},
    "answer_empty_warning": {"ja": "回答を入力してください。", "en": "Please enter your answer."},
    "grading_spinner": {"ja": "採点中...", "en": "Grading..."},
    "result_header": {"ja": "採点結果", "en": "Result"},
    "correct_msg": {"ja": "正解！ スコア: {score:.1f}/{max_score:.1f}", "en": "Correct! Score: {score:.1f}/{max_score:.1f}"},
    "incorrect_msg": {"ja": "不正解 スコア: {score:.1f}/{max_score:.1f}", "en": "Incorrect. Score: {score:.1f}/{max_score:.1f}"},
    "feedback_label": {"ja": "フィードバック:", "en": "Feedback:"},
    "missing_concepts_label": {"ja": "復習が必要な概念", "en": "Concepts to review"},
    "show_answer": {"ja": "正解と解説を見る", "en": "Show correct answer"},
    "correct_answer_label": {"ja": "正解:", "en": "Correct answer:"},
    "explanation_label": {"ja": "解説:", "en": "Explanation:"},
    "no_history": {"ja": "まだ解答履歴がありません。", "en": "No submission history yet."},
    "history_count": {"ja": "{count}件 の解答済み課題があります。", "en": "{count} completed assignment(s)."},
    "correct_suffix": {"ja": "正解", "en": "correct"},
    "ask_ta_bot": {"ja": "TA Botに質問", "en": "Ask TA Bot"},
    "show_details": {"ja": "詳細を見る", "en": "Details"},
    "your_answer": {"ja": "あなたの回答:", "en": "Your answer:"},
    "submitted_at": {"ja": "提出日時:", "en": "Submitted:"},
    "back_to_history": {"ja": "← 解答履歴に戻る", "en": "← Back to history"},
    "your_answer_feedback": {"ja": "あなたの回答とフィードバック", "en": "Your answer & feedback"},
    "ta_bot_assignment_header": {"ja": "TA Bot — この課題について質問", "en": "TA Bot — Ask about this assignment"},
    "ta_bot_assignment_placeholder": {"ja": "この課題について質問...", "en": "Ask about this assignment..."},
    "ta_bot_response_error": {"ja": "回答の生成に失敗しました。", "en": "Failed to generate a response."},

    # ── Difficulty / Question type labels ─────────────────
    "easy": {"ja": "初級", "en": "Easy"},
    "medium": {"ja": "中級", "en": "Medium"},
    "hard": {"ja": "上級", "en": "Hard"},
    "multiple_choice": {"ja": "選択", "en": "MC"},
    "short_answer": {"ja": "記述", "en": "Short"},
    "code": {"ja": "コード", "en": "Code"},

    # ── Lecture prefix ────────────────────────────────────
    "lecture_prefix": {"ja": "第{n}回", "en": "Lecture {n}"},

    # ── TA Bot page ───────────────────────────────────────
    "ta_bot_title": {"ja": "TA Bot", "en": "TA Bot"},
    "ta_bot_caption": {"ja": "教材に基づいた質問に回答します。プログラミングに関する質問をどうぞ。", "en": "Ask questions based on course materials."},
    "ta_bot_placeholder": {"ja": "質問を入力してください...", "en": "Type your question..."},
    "ta_bot_thinking": {"ja": "考え中...", "en": "Thinking..."},
    "ta_bot_ref": {"ja": "参照", "en": "Ref"},
    "course_label": {"ja": "コース", "en": "Course"},
    "no_active_courses": {"ja": "受講中のコースがありません。", "en": "No active courses are available."},
    "materials_title": {"ja": "教材", "en": "Course Materials"},
    "materials_caption": {"ja": "教員が公開した講義教材を確認できます。", "en": "Review lecture materials published by your teacher."},
    "no_published_materials": {"ja": "公開されている教材はまだありません。", "en": "No materials have been published for students yet."},
    "other_materials": {"ja": "その他の教材", "en": "Other Materials"},
    "slide": {"ja": "スライド", "en": "Slides"},
    "book": {"ja": "参考資料", "en": "Reference"},
    "note": {"ja": "ノート", "en": "Note"},

    # ── Common errors ─────────────────────────────────────
    "session_expired": {"ja": "セッションが切れました。再ログインしてください。", "en": "Session expired. Please log in again."},
    "api_connect_error": {"ja": "APIサーバーに接続できません。", "en": "Cannot connect to API server."},
    "timeout_error": {"ja": "タイムアウトしました。もう一度試してください。", "en": "Request timed out. Please try again."},
    "api_error": {"ja": "エラーが発生しました。", "en": "An error occurred."},
    "score_label": {"ja": "スコア", "en": "Score"},

    # ── Dashboard ────────────────────────────────────────
    "welcome_student": {"ja": "ようこそ、{name}さん", "en": "Welcome, {name}"},
    "dashboard_caption": {"ja": "現在の学習状況と最近の成績を確認できます。", "en": "Review your current progress and recent performance."},
    "overall_score": {"ja": "総合スコア", "en": "Overall Score"},
    "completion": {"ja": "完了した課題", "en": "Completed"},
    "completion_rate": {"ja": "課題完了率", "en": "Completion"},
    "pending": {"ja": "未完了", "en": "Pending"},
    "accuracy": {"ja": "正答率", "en": "Accuracy"},
    "answered": {"ja": "回答済み", "en": "Answered"},
    "today_progress": {"ja": "今日の進捗", "en": "Today's Progress"},
    "weak_topics_title": {"ja": "復習が必要なトピック", "en": "Topics to Review"},
    "strong_topics_title": {"ja": "得意なトピック", "en": "Strong Topics"},
    "no_weak_topics": {"ja": "現在、明確な苦手トピックはありません。", "en": "No clear weak topics yet."},
    "no_strong_topics": {"ja": "課題に回答すると得意トピックが表示されます。", "en": "Strong topics will appear after you complete assignments."},
    "score_trend": {"ja": "日別スコア推移", "en": "Daily Score Trend"},
    "topic_scores": {"ja": "トピック別スコア", "en": "Scores by Topic"},
    "no_trend_data": {"ja": "推移を表示する提出データがまだありません。", "en": "No submission data is available for trends yet."},
    "average_score": {"ja": "平均スコア", "en": "Average Score"},
    "responses": {"ja": "回答数", "en": "Responses"},
    "date": {"ja": "日付", "en": "Date"},
    "topic": {"ja": "トピック", "en": "Topic"},
    "concept_mastery": {"ja": "概念別習熟度", "en": "Concept Mastery"},
    "mastery_score": {"ja": "習熟スコア", "en": "Mastery Score"},
    "attempts": {"ja": "評価数", "en": "Evidence Count"},
    "progress_rules": {"ja": "進捗は各課題の最新の採点済み回答から計算します。課題を初めて完了すると完了数が増え、再回答では最新スコアに更新されます。", "en": "Progress uses the latest graded answer for each assignment. First completion increases the completed count; a retry replaces that assignment's current score."},
    "progress_over_time": {"ja": "課題完了による進捗の変化", "en": "Progress after each completed assignment"},
    "percent_or_score": {"ja": "割合・スコア", "en": "Percent / Score"},
    "assignment_score": {"ja": "今回のスコア", "en": "Assignment Score"},
    "progress_change": {"ja": "今回の回答による変化", "en": "What changed after this answer"},
    "progress_change_explanation": {"ja": "総合スコア、課題完了率、対象トピックの習熟度を再計算しました。", "en": "Overall score, assignment completion, and topic mastery were recalculated."},
    "first_evidence": {"ja": "最初の評価", "en": "First evidence"},
}


def get_lang() -> str:
    """Return current language code from session state."""
    return st.session_state.get("lang", "ja")


def t(key: str, **kwargs) -> str:
    """Translate a key to the current language, with optional format args."""
    lang = get_lang()
    entry = TRANSLATIONS.get(key, {})
    text = entry.get(lang, entry.get("ja", key))
    if kwargs:
        text = text.format(**kwargs)
    return text
