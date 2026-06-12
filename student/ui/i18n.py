"""Internationalization: Japanese / English UI text."""

import streamlit as st

TRANSLATIONS = {
    # ── App / Sidebar ─────────────────────────────────────
    "app_title": {"ja": "学習支援システム", "en": "Learning Support System"},
    "page_label": {"ja": "ページ", "en": "Page"},
    "page_assignments": {"ja": "課題", "en": "Assignments"},
    "page_ta_bot": {"ja": "TA Bot", "en": "TA Bot"},
    "logout": {"ja": "ログアウト", "en": "Logout"},
    "language": {"ja": "言語", "en": "Language"},

    # ── Login ─────────────────────────────────────────────
    "login_title": {"ja": "ログイン", "en": "Login"},
    "login_instruction": {"ja": "学生IDとパスワードを入力してください。", "en": "Enter your student ID and password."},
    "student_id": {"ja": "学生ID", "en": "Student ID"},
    "password": {"ja": "パスワード", "en": "Password"},
    "login_button": {"ja": "ログイン", "en": "Login"},
    "login_empty_error": {"ja": "学生IDとパスワードを入力してください。", "en": "Please enter your student ID and password."},
    "login_failed": {"ja": "ログインに失敗しました。", "en": "Login failed."},
    "login_connect_error": {"ja": "APIサーバーに接続できません。サーバーが起動しているか確認してください。", "en": "Cannot connect to the API server. Please check if the server is running."},
    "login_error": {"ja": "エラーが発生しました", "en": "An error occurred"},
    "demo_account": {"ja": "デモアカウント: s2024001 / demo123", "en": "Demo account: s2024001 / demo123"},

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
    "answer_empty_warning": {"ja": "回答を入力してください。", "en": "Please enter your answer."},
    "grading_spinner": {"ja": "採点中...", "en": "Grading..."},
    "result_header": {"ja": "採点結果", "en": "Result"},
    "correct_msg": {"ja": "正解！ スコア: {score:.1f}/100", "en": "Correct! Score: {score:.1f}/100"},
    "incorrect_msg": {"ja": "不正解 スコア: {score:.1f}/100", "en": "Incorrect. Score: {score:.1f}/100"},
    "feedback_label": {"ja": "フィードバック:", "en": "Feedback:"},
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

    # ── Common errors ─────────────────────────────────────
    "session_expired": {"ja": "セッションが切れました。再ログインしてください。", "en": "Session expired. Please log in again."},
    "api_connect_error": {"ja": "APIサーバーに接続できません。", "en": "Cannot connect to API server."},
    "timeout_error": {"ja": "タイムアウトしました。もう一度試してください。", "en": "Request timed out. Please try again."},
    "api_error": {"ja": "エラーが発生しました。", "en": "An error occurred."},
    "score_label": {"ja": "スコア", "en": "Score"},
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
