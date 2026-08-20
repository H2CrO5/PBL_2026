# Shared Student–Teacher Integration

## Implemented flow

```text
Teacher material -> authenticated sync -> course-scoped RAG chunks
Course RAG -> Teacher grounded generation / optional teaching-plan prose
Teacher question seed -> publish -> enrolled Student assignment
Student answers -> batch or single submission -> Bedrock grading -> latest-attempt progress
Real grading evidence -> Teacher analytics and individual insight
Teacher correction -> Student record -> immediate analytics recalculation
```

The applications still own separate SQLite files for local development. They do
not open each other's files. All cross-application reads and writes use the
Student integration API and `X-Integration-Token`.

## Shared identifiers

- `external_course_id`: stable Teacher `Course.external_key`, copied to Student.
- `external_assignment_id`: stable publication key; Student adds the student code
  when creating one personalized assignment row.
- `external_material_id`: stable material key used for idempotent re-ingestion.
- Student identity currently uses the stable `student_code` across both apps.

Teacher routes verify course ownership. Student routes verify enrollment.
Integration writes are idempotent and both sides store audit logs.

## Metric definitions

- A completed assignment is a unique assignment with a graded, real submission.
- When retries are allowed, only the latest graded attempt contributes to score,
  completion, topic mastery, and Teacher analytics.
- Student average is the mean of those latest attempts.
- Class average includes only students with at least one real graded submission.
- Class completion includes all actively enrolled students.
- Initial seed answers are included with `source="seed"` so the three demo
  accounts are visible before new activity; synthetic eval rows are excluded.
  Teacher submission rows expose their source so seed evidence is distinguishable.
- A teacher correction preserves the original automatic score and feedback.

## RAG behavior

Teacher material is chunked automatically. With
`AWS_BEARER_TOKEN_BEDROCK`, Amazon Titan embeddings are stored for semantic
retrieval. Without credentials, local development uses lexical retrieval and
returns `lexical-fallback` as the retrieval mode. The UI and API expose the
ingestion/retrieval mode rather than silently representing fallback as Bedrock.
Teacher uploads accept PDF, PPTX, Markdown, and text up to the configured size;
page and slide markers are preserved in extracted text before chunking.

TA Bot prompts require source labels for material-backed claims. When no course
material supports a response, the bot must say that the course material could
not verify it and label any general knowledge separately.
TA conversations are stored and retrieved by enrolled course. Assignment chat
also stores the owned assignment ID, preventing cross-course context mixing.

## Safety and operations

- Bedrock and service credentials live only in `.env`.
- CORS defaults to local Student and Teacher Streamlit origins.
- Integration failure returns an explicit 503; Teacher never silently replaces
  configured live data with demo analytics.
- Correct answers are not included in the Teacher analytics feed.
- Password hashes and login sessions never cross the service boundary.
- Grade corrections are course-scoped and audited.

## Production migration

The code supports local SQLite and optional `STUDENT_DATABASE_URL` /
`TEACHER_DATABASE_URL` PostgreSQL connections. Before a real university
deployment, migrate existing records to managed PostgreSQL, local material content
with S3 object storage, and local sessions with a university identity provider
or Amazon Cognito. Configure separate development/staging/production AWS
accounts, KMS encryption, CloudWatch alarms, backups, retention rules, and
least-privilege IAM. Those operations require the university's AWS account,
domains, identity-provider settings, and data-retention approval; no repository
code should guess them.
