# ClassPilot

ClassPilot connects the Student and Teacher applications so a student submission
is graded, stored, reflected in teacher analytics, and available for correction.
Teacher materials can be indexed for course-scoped, citation-aware RAG through
Amazon Bedrock.

The local MVP keeps Student and Teacher as separate services and databases. An
authenticated API bridge with stable course, assignment, student and submission
IDs connects them; RAG supplies grounded course context but is not used as a
transport for submission records.

## First-time setup

Python 3.10 or newer is required. The setup script uses `python3` by default;
set `PYTHON_BIN` when your system default is older.

```bash
./setup_classpilot.sh
# Example when python3 is older than 3.10:
PYTHON_BIN=python3.12 ./setup_classpilot.sh
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

1. Open **Assignment Builder** and select an existing lecture, or use **Add Lecture** to create one.
2. Open **Materials**, upload a PDF/PPTX/MD/TXT file of up to 20 MB, or select **Sync all materials to Student RAG**.
3. Return to **Assignment Builder** and generate a grounded Bedrock draft, or add a seed.
4. Review the question and select **Publish to Student app**.
5. The student answers it in the Student application.
   Multiple questions in the same lecture can be submitted together.
6. Open **Students** to see the real answer, feedback, error pattern, and score.
7. If needed, save a grade correction; analytics are recalculated immediately.

The Student **Dashboard** shows live score trends, accuracy, weak/strong topics
and concept mastery evidence. Teacher **Analytics** includes class trends and
assignment-level completion, missing concepts and grading error patterns.
The TA Bot requires an enrolled course selection and keeps history isolated by
course; assignment questions are additionally tied to an owned assignment.

## Container integration environment

With Docker installed, the same four processes can be started with:

```bash
docker compose up --build
```

Fresh container volumes receive the demo users automatically. PostgreSQL can be
selected with `STUDENT_DATABASE_URL` and `TEACHER_DATABASE_URL`; see
[docs/aws-collaboration.md](docs/aws-collaboration.md) before deployment.

See [docs/shared-integration.md](docs/shared-integration.md) for contracts,
metric definitions, security boundaries, and production migration notes.
