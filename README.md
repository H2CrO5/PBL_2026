# ClassPilot

ClassPilot connects the Student and Teacher applications so a student submission
is graded, stored, reflected in teacher analytics, and available for correction.
Teacher materials can be indexed for course-scoped, citation-aware RAG through
Amazon Bedrock.

## First-time setup

```bash
git switch codex/shared-course-assignment-rag
./setup_classpilot.sh
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Open `.env` in a text editor and set:

```dotenv
AWS_BEARER_TOKEN_BEDROCK=your-key-kept-only-on-this-computer
TEACHER_INTEGRATION_TOKEN=the-random-value-from-the-command
TEACHER_USE_LLM=1
```

Never paste a real AWS key into source code, a commit, an issue, or a Pull
Request. `.env` is ignored by Git.

## Start everything

```bash
./run_classpilot.sh
```

- Student: <http://localhost:8501>
- Teacher: <http://localhost:8601>
- Student demo login: `s2024001 / demo123`
- Teacher demo login: `t2024001 / demo123`

## Teacher workflow

1. Open **Materials**, upload PDF/PPTX/MD/TXT or select **Sync all materials to Student RAG**.
2. Open **Question Bank** and generate a grounded Bedrock draft, or add a seed.
3. Review the question and select **Publish to Student app**.
4. The student answers it in the Student application.
5. Open **Students** to see the real answer, feedback, error pattern, and score.
6. If needed, save a grade correction; analytics are recalculated immediately.

See [docs/shared-integration.md](docs/shared-integration.md) for contracts,
metric definitions, security boundaries, and production migration notes.
