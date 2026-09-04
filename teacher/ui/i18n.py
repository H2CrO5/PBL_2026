"""English/Japanese translations for the teacher Streamlit UI."""

import re

import streamlit as st


TRANSLATIONS = {
    "role_label": {"en": "Teacher", "ja": "Teacher"},
    "navigation": {"en": "Navigation", "ja": "ナビゲーション"},
    "dashboard": {"en": "Dashboard", "ja": "ダッシュボード"},
    "materials": {"en": "Materials", "ja": "教材"},
    "question_bank": {"en": "Assignment Builder", "ja": "課題作成"},
    "analytics": {"en": "Analytics", "ja": "学習分析"},
    "students": {"en": "Students", "ja": "学生別分析"},
    "logout": {"en": "Logout", "ja": "ログアウト"},
    "session_expired": {"en": "Session expired. Please log in again.", "ja": "セッションの有効期限が切れました。再度ログインしてください。"},
    "api_error": {"en": "API error: {status}", "ja": "APIエラー: {status}"},
    "connection_error": {"en": "Cannot connect to teacher API server.", "ja": "教員用APIサーバーに接続できません。"},
    "timeout": {"en": "Request timed out.", "ja": "リクエストがタイムアウトしました。"},
    "material_timeout": {"en": "Material processing timed out.", "ja": "教材の処理がタイムアウトしました。"},
    "teacher_login": {"en": "Teacher Login", "ja": "Teacher Login"},
    "teacher_id": {"en": "Teacher ID", "ja": "教員ID"},
    "password": {"en": "Password", "ja": "パスワード"},
    "login": {"en": "Login", "ja": "ログイン"},
    "login_failed": {"en": "Login failed", "ja": "ログインに失敗しました"},
    "demo_accounts": {"en": "Demo Accounts", "ja": "デモアカウント"},
    "data_source": {"en": "Data source: {source}", "ja": "集計データ: {source}"},
    "live_submissions": {"en": "Live Student submissions", "ja": "学生が実際に提出した回答"},
    "submissions_with_seed": {"en": "Student submissions (including labeled sample answers)", "ja": "学生の回答（初期サンプルを含む）"},
    "sample_answer": {"en": "Initial sample answer · read only", "ja": "初期サンプル（閲覧のみ）"},
    "demo_data": {"en": "Demo analytics data", "ja": "デモ分析データ"},
    "demo_data_unconfigured": {"en": "Demo analytics data (Student integration is not configured)", "ja": "デモ分析データ（Student連携は未設定です）"},
    "average_score": {"en": "Average Score", "ja": "平均点"},
    "completion": {"en": "Submission Rate", "ja": "提出率"},
    "completion_rate": {"en": "Submission Rate", "ja": "提出率"},
    "weak_concepts": {"en": "Weak Areas", "ja": "理解が不十分な分野"},
    "class_dashboard": {"en": "Class Dashboard", "ja": "クラス概要"},
    "no_dashboard": {"en": "No dashboard data available.", "ja": "ダッシュボードデータがありません。"},
    "student_count": {"en": "Students", "ja": "学生数"},
    "question_seeds": {"en": "Question Library", "ja": "登録済み問題"},
    "seed_total": {"en": "{total} saved ({required} required)", "ja": "{total}件（必須{required}件）"},
    "question_seeds_help": {
        "en": "Reusable questions saved with expected answers and rubrics. Required questions are always included when Bedrock generates an assignment.",
        "ja": "模範解答と採点基準を付けて保存した問題です。「必須」の問題は、Bedrockで課題を生成する際に必ず使用されます。",
    },
    "action_list": {"en": "Recommended Actions", "ja": "対応が必要な項目"},
    "next_step": {"en": "Next step: {step}", "ja": "推奨する対応: {step}"},
    "wrong_rate": {"en": "Wrong Rate (%)", "ja": "誤答率（%）"},
    "concept": {"en": "Concept", "ja": "概念"},
    "lecture_focus": {"en": "Recommended Lecture Focus", "ja": "次回の授業で扱う内容"},
    "score_trend": {"en": "Class Score Trend", "ja": "クラス平均点の推移"},
    "date": {"en": "Date", "ja": "日付"},
    "submissions": {"en": "Submissions", "ja": "提出数"},
    "student_analysis": {"en": "Individual Student Analysis", "ja": "学生別の学習状況"},
    "no_student_insights": {"en": "No student insights available.", "ja": "学生分析データがありません。"},
    "student": {"en": "Student", "ja": "学生"},
    "weak_topics": {"en": "Weak Topics", "ja": "苦手分野"},
    "recommended_action": {"en": "Recommended Action", "ja": "推奨する対応"},
    "inspect_student": {"en": "Select student", "ja": "学生を選択"},
    "strong_topics": {"en": "Strong topics", "ja": "得意分野"},
    "recent_submissions": {"en": "Recent Submissions", "ja": "最近の提出"},
    "no_submissions": {"en": "No real submissions yet.", "ja": "実際の提出はまだありません。"},
    "recent_questions": {"en": "Recent TA Bot Questions", "ja": "最近のTA Bot質問"},
    "no_questions": {"en": "No TA Bot questions yet.", "ja": "TA Botへの質問はまだありません。"},
    "question": {"en": "Question", "ja": "問題"},
    "student_answer": {"en": "Student answer", "ja": "学生の回答"},
    "feedback": {"en": "Feedback", "ja": "フィードバック"},
    "missing_concepts": {"en": "Missing concepts", "ja": "不足している概念"},
    "error_pattern": {"en": "Error pattern", "ja": "誤答傾向"},
    "attempt_grading": {"en": "Attempt {attempt} | Grading: {source}", "ja": "解答回数: {attempt}回 | 採点方法: {source}"},
    "submitted": {"en": "Submitted: {date}", "ja": "提出日時: {date}"},
    "corrected_score": {"en": "Corrected score", "ja": "修正後のスコア"},
    "corrected_feedback": {"en": "Corrected feedback", "ja": "修正後のフィードバック"},
    "save_correction": {"en": "Save grade correction", "ja": "採点修正を保存"},
    "correction_saved": {"en": "Grade correction saved and analytics recalculated.", "ja": "採点修正を保存し、分析を再計算しました。"},
    "material_management": {"en": "Material Management", "ja": "教材管理"},
    "material_intro": {"en": "Review existing materials or add a new course material.", "ja": "登録済みの教材を確認したり、新しい教材を追加したりできます。"},
    "add_material": {"en": "Add Material", "ja": "教材を追加"},
    "no_lectures": {"en": "No lectures available.", "ja": "利用できる講義がありません。"},
    "lecture": {"en": "Lecture", "ja": "講義"},
    "add_lecture": {"en": "Add Lecture", "ja": "講義を追加"},
    "lecture_number": {"en": "Lecture number", "ja": "講義回"},
    "lecture_title": {"en": "Lecture title", "ja": "講義タイトル"},
    "learning_objectives": {"en": "Learning objectives", "ja": "学習目標"},
    "learning_objectives_help": {"en": "Enter one objective per line.", "ja": "1行につき1つの学習目標を入力してください。"},
    "save_lecture": {"en": "Save lecture", "ja": "講義を保存"},
    "lecture_required_fields": {"en": "Lecture title and at least one learning objective are required.", "ja": "講義タイトルと1つ以上の学習目標を入力してください。"},
    "lecture_saved": {"en": "Lecture saved and selected for assignment creation.", "ja": "講義を保存しました。課題作成で選択できます。"},
    "create_first_lecture": {"en": "Create a lecture before adding materials or assignments.", "ja": "教材や課題を追加する前に、講義を作成してください。"},
    "title": {"en": "Title", "ja": "タイトル"},
    "type": {"en": "Type", "ja": "種類"},
    "content": {"en": "Content", "ja": "内容"},
    "student_visible": {"en": "Visible to students", "ja": "Studentに公開する"},
    "student_visible_help": {"en": "Turn this off for teacher notes. Teacher-only content is removed from the Student screen and Student RAG.", "ja": "教員メモの場合はオフにします。教員専用の内容はStudent画面とStudent RAGの両方から除外されます。"},
    "course_unknown": {"en": "Cannot identify the current course.", "ja": "現在のコースを特定できません。"},
    "material_added": {"en": "Material added and marked ready.", "ja": "教材を追加し、利用可能にしました。"},
    "upload_course_file": {"en": "Upload a course file", "ja": "教材ファイルをアップロード"},
    "file_types": {"en": "PDF, PowerPoint, Markdown, or text", "ja": "PDF、PowerPoint、Markdown、テキスト"},
    "upload_instructions": {"en": "Step 1: Choose a file (maximum {size} MB). Step 2: select Upload and index.", "ja": "ステップ1：ファイルを選択（最大{size} MB）。ステップ2：「アップロードしてRAGに登録」を押します。"},
    "upload_title": {"en": "Uploaded material title (optional)", "ja": "アップロード教材のタイトル（任意）"},
    "upload_index": {"en": "Upload and index", "ja": "アップロードしてRAGに登録"},
    "uploaded": {"en": "Uploaded: {status}", "ja": "アップロード完了: {status}"},
    "current_materials": {"en": "Current Materials", "ja": "現在の教材"},
    "no_materials": {"en": "No materials found.", "ja": "教材が見つかりません。"},
    "sync_all_rag": {"en": "Apply visibility and sync public materials", "ja": "公開設定を反映して公開教材を同期"},
    "sync_result": {"en": "Synced {synced} material(s), {chunks} chunks; failed: {failed}.", "ja": "{synced}件の教材（{chunks}チャンク）を同期しました。失敗: {failed}件。"},
    "sync_rag": {"en": "Sync to Student RAG", "ja": "Student RAGへ同期"},
    "apply_teacher_only": {"en": "Remove from Student", "ja": "Studentから削除"},
    "make_teacher_only": {"en": "Change to Teacher only", "ja": "教員のみに変更"},
    "make_student_visible": {"en": "Publish to Student", "ja": "Studentに公開"},
    "visibility_updated": {"en": "Visibility updated", "ja": "公開範囲を更新しました"},
    "indexed": {"en": "Indexed {chunks} chunk(s): {status}", "ja": "{chunks}チャンクを索引化しました: {status}"},
    "no_course_materials": {"en": "No course materials available.", "ja": "利用できるコース教材がありません。"},
    "materials_count": {"en": "Materials", "ja": "教材数"},
    "lecture_seeds": {"en": "Saved Questions", "ja": "登録済み問題数"},
    "generation_readiness": {"en": "Generation Readiness", "ja": "課題生成の準備状況"},
    "ready_handoff": {"en": "Ready to generate", "ja": "課題を生成できます"},
    "needs_review": {"en": "Needs review", "ja": "内容を確認してください"},
    "generate_bedrock": {"en": "Generate a grounded draft with Bedrock", "ja": "教材をもとにBedrockで課題案を作成"},
    "assignment_goal": {"en": "Assignment goal", "ja": "この課題で確認したいこと"},
    "number_questions": {"en": "Number of questions", "ja": "問題数"},
    "target_students": {"en": "Target students (blank means whole class)", "ja": "配布対象（未選択の場合は全員）"},
    "draft_saved": {"en": "Bedrock draft saved for review. It is not published yet.", "ja": "Bedrockの下書きを確認用に保存しました。まだ公開されていません。"},
    "add_seed": {"en": "Add Question", "ja": "問題を追加"},
    "target_concept": {"en": "Target concept", "ja": "確認する分野"},
    "seed_type": {"en": "Question type", "ja": "問題の扱い"},
    "difficulty": {"en": "Difficulty", "ja": "難易度"},
    "expected_answer": {"en": "Expected answer", "ja": "模範解答"},
    "answer_rubric": {"en": "Expected answer and rubric", "ja": "模範解答と採点基準"},
    "no_lecture": {"en": "No lecture", "ja": "講義を指定しない"},
    "notes": {"en": "Notes", "ja": "メモ"},
    "rubric": {"en": "Rubric", "ja": "採点基準"},
    "points": {"en": "Points", "ja": "配点"},
    "max_attempts": {"en": "Maximum attempts", "ja": "最大試行回数"},
    "assessment_scope": {"en": "Assessment scope", "ja": "利用目的"},
    "variation_policy": {"en": "Variation policy", "ja": "類題の生成"},
    "teacher_priority": {"en": "Teacher priority", "ja": "対応の優先度"},
    "internal_notes": {"en": "Teacher notes", "ja": "教員向けメモ"},
    "save_seed": {"en": "Save question", "ja": "問題を保存"},
    "required_fields": {"en": "Question, expected answer, and rubric are required.", "ja": "問題、模範解答、採点基準は必須です。"},
    "seed_saved": {"en": "Question saved.", "ja": "問題を保存しました。"},
    "generation_context": {"en": "Generation Context", "ja": "課題案の作成に使用する情報"},
    "current_weak": {"en": "Current weak areas", "ja": "現在の苦手分野"},
    "candidate_seeds": {"en": "Draft Candidates", "ja": "課題案"},
    "candidate_details": {"en": "Candidate answer, rubric, and rationale", "ja": "候補の解答・採点基準・根拠"},
    "rationale": {"en": "Rationale", "ja": "生成理由"},
    "save_candidate": {"en": "Save candidate", "ja": "候補を保存"},
    "candidate_saved": {"en": "Draft added to the question library.", "ja": "課題案を登録済み問題に追加しました。"},
    "no_seeds": {"en": "No saved questions for this lecture yet.", "ja": "この講義には登録済みの問題がまだありません。"},
    "publish_student": {"en": "Publish to Student", "ja": "Studentに公開"},
    "publish_selected": {"en": "Publish selected questions together", "ja": "選択した問題をまとめてStudentに公開"},
    "select_questions": {"en": "Questions to publish", "ja": "公開する問題"},
    "published": {"en": "Published for {created} student(s); already present for {existing}.", "ja": "{created}人の学生に公開しました。公開済み: {existing}人。"},
    "seed_summary": {"en": "Points: {points:.0f} | Maximum attempts: {attempts}", "ja": "配点: {points:.0f} | 最大試行回数: {attempts}"},
    "analytics_title": {"en": "Analytics and Lecture Improvement", "ja": "学習状況と授業改善"},
    "incorrect_trends": {"en": "Incorrect Answer Trends", "ja": "分野別の誤答傾向"},
    "assignment_analytics": {"en": "Assignment Analytics", "ja": "課題別の提出・成績状況"},
    "select_assignment": {"en": "Select assignment", "ja": "課題を選択"},
    "no_published_assignments": {"en": "No published assignments yet.", "ja": "公開済み課題はまだありません。"},
    "assigned": {"en": "Assigned", "ja": "配布人数"},
    "wrong_rate_metric": {"en": "Wrong Rate", "ja": "誤答率"},
    "error_patterns": {"en": "Error Patterns", "ja": "誤答傾向"},
    "wrong_rate_line": {"en": "wrong rate: **{rate:.0f}%**", "ja": "誤答率: **{rate:.0f}%**"},
    "misconception": {"en": "Misconception", "ja": "よくあるつまずき"},
    "teaching_focus": {"en": "Teaching focus", "ja": "指導の重点"},
    "evidence_view": {"en": "Evidence View", "ja": "分析根拠"},
    "no_evidence": {"en": "No evidence data available.", "ja": "根拠データがありません。"},
    "affected_students": {"en": "Affected students", "ja": "該当する学生"},
    "related_seeds": {"en": "Related saved questions", "ja": "関連する登録済み問題"},
    "no_related_seed": {"en": "No related saved question yet", "ja": "関連する登録済み問題はまだありません"},
    "typical_evidence": {"en": "Typical evidence", "ja": "主な誤答・つまずき"},
    "next_lecture": {"en": "Next Lecture Recommendation", "ja": "次回授業への提案"},
    "generate_plan": {"en": "Generate lecture plan", "ja": "次回授業の案を作成"},
    "report_history": {"en": "Saved lecture plans", "ja": "保存済みの授業改善案"},
    "no_report_history": {"en": "No lecture plan has been saved yet.", "ja": "保存済みの授業改善案はまだありません。"},
    "opening_activity": {"en": "Opening activity", "ja": "授業の導入"},
    "weakest_concepts": {"en": "Weakest concepts", "ja": "優先して復習する分野"},
    "common_misconceptions": {"en": "Common misconceptions", "ja": "よく見られる誤解"},
    "recommended_focus": {"en": "Recommended focus", "ja": "授業で重点的に扱う内容"},
    "review_sequence": {"en": "Review sequence", "ja": "復習の進め方"},
    "in_class_check": {"en": "In-class check", "ja": "授業内の理解確認"},
    "follow_up": {"en": "Follow-up actions", "ja": "授業後のフォロー"},
    "recommended_seeds": {"en": "Recommended questions", "ja": "使用を推奨する問題"},
    "lecture_label": {"en": "Lecture {number}: {title}", "ja": "第{number}回：{title}"},
    "checkpoint_title": {"en": "{lecture} checkpoint", "ja": "{lecture}の理解度確認"},
    "default_assignment_goal": {"en": "Check conceptual understanding using course evidence", "ja": "教材の内容を根拠に、重要な概念を理解できているか確認する"},
    "default_material_title": {"en": "Teacher note: Evidence checklist", "ja": "教員メモ：根拠確認チェックリスト"},
    "default_material_content": {"en": "Students should verify whether each claim is supported by a passage from the course materials.", "ja": "学生は、それぞれの主張が授業教材の記述によって裏付けられているか確認する。"},
    "default_rubric": {"en": "Correctly identifies inputs and outputs\nHandles the edge case\nExplains the reasoning clearly", "ja": "入力と出力を正しく特定している\n境界条件を適切に処理している\n考え方を明確に説明している"},
}


VALUE_TRANSLATIONS = {
    "base": {"en": "Base", "ja": "基本"},
    "required": {"en": "Required", "ja": "必須"},
    "rubric_seed": {"en": "Rubric", "ja": "採点基準"},
    "supportive": {"en": "Supportive", "ja": "やさしめ"},
    "balanced": {"en": "Balanced", "ja": "標準"},
    "challenging": {"en": "Challenging", "ja": "発展"},
    "easy": {"en": "Easy", "ja": "初級"},
    "hard": {"en": "Hard", "ja": "上級"},
    "practice_only": {"en": "Practice only", "ja": "練習用"},
    "formative_checkpoint": {"en": "Formative checkpoint", "ja": "理解度確認"},
    "exam_relevant": {"en": "Exam relevant", "ja": "試験範囲"},
    "allow_variants": {"en": "Allow variants", "ja": "類題生成を許可"},
    "teacher_review_required": {"en": "Teacher review required", "ja": "教員確認後に生成"},
    "do_not_generate_variants": {"en": "Do not generate variants", "ja": "類題を生成しない"},
    "normal": {"en": "Normal", "ja": "通常"},
    "medium": {"en": "Medium", "ja": "中"},
    "high": {"en": "High", "ja": "高"},
    "critical": {"en": "Critical", "ja": "最優先"},
    "ready": {"en": "Ready", "ja": "準備完了"},
    "warning": {"en": "Warning", "ja": "要確認"},
    "blocked": {"en": "Blocked", "ja": "未準備"},
    "auto": {"en": "Automatic", "ja": "自動採点"},
    "teacher_override": {"en": "Teacher corrected", "ja": "教員が修正"},
    "note": {"en": "Note", "ja": "ノート"},
    "slide": {"en": "Slide", "ja": "スライド"},
    "book": {"en": "Book", "ja": "参考書"},
    "ready_bedrock": {"en": "Ready (Bedrock)", "ja": "利用可能（Bedrock）"},
    "ready_lexical": {"en": "Ready (keyword fallback)", "ja": "利用可能（キーワード検索）"},
    "ready_lexical_fallback": {"en": "Ready (keyword fallback)", "ja": "利用可能（キーワード検索）"},
    "local_only": {"en": "Saved locally; RAG sync pending", "ja": "ローカル保存済み・RAG同期待ち"},
    "sync_failed": {"en": "RAG sync failed", "ja": "RAG同期に失敗"},
    "student": {"en": "Student visible", "ja": "Studentに公開"},
    "teacher": {"en": "Teacher only", "ja": "教員のみ"},
    "teacher_only": {"en": "Teacher only", "ja": "教員のみ"},
    "pending": {"en": "Pending", "ja": "処理待ち"},
    "failed": {"en": "Failed", "ja": "失敗"},
    "high confidence": {"en": "High confidence", "ja": "根拠が十分"},
    "medium confidence": {"en": "Medium confidence", "ja": "一定の根拠あり"},
    "needs more evidence": {"en": "Needs more evidence", "ja": "データ不足"},
    "persistent issue": {"en": "Persistent issue", "ja": "継続して見られる課題"},
    "monitor": {"en": "Monitor", "ja": "経過観察"},
}


def get_lang() -> str:
    return st.session_state.get("teacher_lang", "en")


def t(key: str, **kwargs) -> str:
    entry = TRANSLATIONS.get(key, {})
    text = entry.get(get_lang(), entry.get("en", key))
    return text.format(**kwargs) if kwargs else text


def tv(value: str) -> str:
    """Translate an API enum/status without changing its stored value."""
    entry = VALUE_TRANSLATIONS.get(str(value), {})
    fallback = str(value).replace("_", " ").title()
    return entry.get(get_lang(), entry.get("en", fallback))


def localize_text(value: str) -> str:
    """Localize deterministic API prose while preserving stored/API values."""
    if get_lang() != "ja" or not value:
        return value

    exact = {
        "On track; continue with the next assignment.": "順調です。次の課題へ進めます。",
        "On track; assign a challenge-level item next.": "順調です。次は発展レベルの課題に取り組ませましょう。",
        "No real submission yet; monitor assignment completion.": "実際の提出はまだありません。提出状況を確認してください。",
        "Check low-performing students": "成績が低い学生を確認する",
        "Add required question seeds": "必須の問題を追加する",
        "Monitor completion": "提出状況を確認する",
        "Open Individual Student Analysis and plan follow-up practice.": "学生別分析を開き、追加の練習課題を検討してください。",
        "Shared backend generation needs teacher constraints before assignment creation.": "課題を生成するには、教員が出題条件を設定する必要があります。",
        "Add at least one required seed for each active lecture.": "各講義に「必須」の問題を1件以上追加してください。",
        "Use completion data after integration to identify missing submissions.": "提出状況を確認し、未提出の学生を把握してください。",
        "Completed materials": "登録済みの教材",
        "Learning objectives": "学習目標",
        "Weak concept signal": "苦手分野の分析データ",
        "Required question seed": "必須の問題",
        "Rubric guidance": "採点基準",
        "No analytics signal yet; shared backend can only generate generic practice.": "学習分析データがまだないため、現時点では一般的な練習問題のみ生成できます。",
        "Add at least one required seed before backend assignment generation.": "課題を生成する前に、「必須」の問題を1件以上追加してください。",
        "No rubric seed yet; grading guidance may be weaker.": "採点基準のテンプレートがないため、採点精度が低くなる可能性があります。",
        "Generated as a local candidate from completed lecture materials and analytics.": "登録済みの講義教材と学習分析をもとに作成した候補です。",
        "Suggested to reduce teacher workload: this candidate is not sent to students until the teacher reviews and saves it.": "教員が確認して保存するまでStudentには公開されません。",
        "Explains reasoning instead of only giving a final answer": "最終的な答えだけでなく、考え方も説明している",
        "Addresses the likely misconception or edge case": "想定される誤解や境界条件に対応している",
        "Start the next lecture with a 10-minute misconception review, then ask students to grade two sample answers using the teacher-authored rubric seeds.": "次回の授業は10分間の誤解の振り返りから始め、その後、教員が作成した採点基準を使って2つの解答例を学生に評価させます。",
        "Ask low-confidence students to submit one corrected explanation.": "理解度が十分でない学生には、説明を修正して再提出させてください。",
        "Use the evidence view to select students for individual follow-up.": "分析の根拠を確認し、個別フォローが必要な学生を選んでください。",
        "Keep required seeds locked when shared backend generates assignment variants.": "共有バックエンドが類題を生成する際も、「必須」の問題は変更しないでください。",
        "Edge-case handling": "境界条件への対応",
        "Problem decomposition": "問題の分解",
        "Data-structure selection": "データ構造の選択",
        "Complexity intuition": "計算量の考え方",
        "Students solve the normal case but miss empty input and equality boundaries.": "通常のケースには対応できていますが、空の入力や境界値の扱いを見落としています。",
        "Students jump directly to code before defining inputs, outputs, and intermediate steps.": "入力・出力・途中の手順を整理する前に、すぐコードを書き始めています。",
        "Students overuse lists instead of choosing dictionaries, sets, stacks, or queues by operation.": "必要な操作に応じて辞書・集合・スタック・キューを選ばず、リストを多用しています。",
        "Students describe complexity from output size instead of how work grows with input.": "入力の増加に対する処理量ではなく、出力の大きさだけで計算量を判断しています。",
        "Use trace tables to compare normal cases and edge cases.": "トレース表を使い、通常のケースと境界条件を比較してください。",
        "Have students rewrite a raw problem into inputs, outputs, rules, and edge cases.": "問題文を入力・出力・規則・境界条件に分けて整理させてください。",
        "Run an operation-first activity: lookup, membership, undo, and arrival-order processing.": "検索・所属判定・取り消し・到着順処理の各操作から、適切なデータ構造を選ぶ演習を行ってください。",
        "Compare fixed decision, single traversal, and nested comparison examples.": "定数回の判定、1回の走査、入れ子の比較を例で比較してください。",
    }
    if value in exact:
        return exact[value]

    localized_lines = []
    for line in value.splitlines():
        if line in exact:
            localized_lines.append(exact[line])
            continue
        match = re.fullmatch(r"Assessment scope: (.+)", line)
        if match:
            localized_lines.append(f"利用目的: {tv(match.group(1))}")
            continue
        match = re.fullmatch(r"Variation policy: (.+)", line)
        if match:
            localized_lines.append(f"類題の扱い: {tv(match.group(1))}")
            continue
        match = re.fullmatch(r"Teacher priority: (.+)", line)
        if match:
            localized_lines.append(f"優先度: {tv(match.group(1))}")
            continue
        match = re.fullmatch(r"Review real student evidence for (.+)\.", line)
        if match:
            localized_lines.append(f"{localize_text(match.group(1))}に関する実際の回答を確認し、つまずきに合わせて復習してください。")
            continue
        match = re.fullmatch(r"Review (.+)", line)
        if match:
            localized_lines.append(f"{match.group(1)}を復習する")
            continue
        match = re.fullmatch(r"(\d+) of (\d+) real submissions were graded incorrect\.", line)
        if match:
            localized_lines.append(f"実際の回答{match.group(2)}件のうち{match.group(1)}件が不正解でした。")
            continue
        match = re.fullmatch(r"Observed in (\d+) student profile\(s\) in the local teacher demo data\.", line)
        if match:
            localized_lines.append(f"{match.group(1)}人の学生に同様の傾向が見られます。")
            continue
        match = re.fullmatch(r"([\d.]+)% wrong-rate signal in current analytics\.", line)
        if match:
            localized_lines.append(f"現在の集計では誤答率が{match.group(1)}%です。")
            continue
        match = re.fullmatch(r"Average completion is ([\d.]+)%\.", line)
        if match:
            localized_lines.append(f"現在の提出率は{match.group(1)}%です。")
            continue
        match = re.fullmatch(r"(\d+) student\(s\) are below 60 average score: (.+)\.", line)
        if match:
            localized_lines.append(f"平均点が60点未満の学生が{match.group(1)}人います: {match.group(2)}。")
            continue
        match = re.fullmatch(r"Focus follow-up practice on: (.+)\.", line)
        if match:
            localized_lines.append(f"{match.group(1)}を重点的に復習してください。")
            continue
        match = re.fullmatch(r"(\d+) ready material\(s\) are available for this lecture\.", line)
        if match:
            localized_lines.append(f"この講義で利用できる教材が{match.group(1)}件あります。")
            continue
        match = re.fullmatch(r"(\d+) objective\(s\) are attached to this lecture\.", line)
        if match:
            localized_lines.append(f"この講義には学習目標が{match.group(1)}件設定されています。")
            continue
        match = re.fullmatch(r"(\d+) concept signal\(s\) are available\.", line)
        if match:
            localized_lines.append(f"苦手分野の分析データが{match.group(1)}件あります。")
            continue
        match = re.fullmatch(r"(\d+) required seed\(s\) will constrain generation\.", line)
        if match:
            localized_lines.append(f"「必須」の問題{match.group(1)}件を生成条件として使用します。")
            continue
        match = re.fullmatch(r"(\d+) rubric seed\(s\) are available\.", line)
        if match:
            localized_lines.append(f"採点基準のテンプレートが{match.group(1)}件あります。")
            continue
        match = re.fullmatch(r"(.+) checkpoint", line)
        if match:
            localized_lines.append(f"{localize_text(match.group(1))}の理解度確認")
            continue
        match = re.fullmatch(
            r"For the lecture '(.+)', answer a short question that demonstrates understanding of (.+)\. Include one explanation of your reasoning\.",
            line,
        )
        if match:
            localized_lines.append(f"「{match.group(1)}」の講義内容を踏まえ、{localize_text(match.group(2))}の理解を示す短い問題に答え、考え方を説明してください。")
            continue
        match = re.fullmatch(
            r"A correct answer should explicitly use the lecture concept (.+), state the reasoning path, and handle the most likely misconception\.",
            line,
        )
        if match:
            localized_lines.append(f"{localize_text(match.group(1))}の概念を明確に用い、考え方の過程と、想定される誤解への対応を示している解答。")
            continue
        match = re.fullmatch(r"Uses (.+) accurately", line)
        if match:
            localized_lines.append(f"{localize_text(match.group(1))}を正確に使用している")
            continue
        match = re.fullmatch(r"Open with a 5-minute diagnostic question on (.+), then ask students to explain the boundary or operation they used\.", line)
        if match:
            localized_lines.append(f"{localize_text(match.group(1))}に関する5分間の確認問題から始め、判断に使った条件や操作を学生に説明させます。")
            continue
        match = re.fullmatch(r"Revisit misconception: (.+)", line)
        if match:
            localized_lines.append(f"次の誤答傾向を確認する: {localize_text(match.group(1))}")
            continue
        match = re.fullmatch(r"Use '(.+)' as a short in-class checkpoint before moving on\.", line)
        if match:
            localized_lines.append(f"次の内容へ進む前に、「{localize_text(match.group(1))}」を短い理解度確認として使用します。")
            continue
        localized_lines.append(line)
    return "\n".join(localized_lines)
