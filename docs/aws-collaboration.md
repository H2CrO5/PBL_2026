# AWS collaboration and production boundary

ClassPilot can run locally with SQLite and one Bedrock bearer token. Production
must use account-managed identities and secrets; no AWS secret belongs in Git.

## Recommended ownership

| Resource | Shared owner | Student use | Teacher use |
|---|---|---|---|
| Bedrock text model | AWS administrator | grading and TA answers | draft generation and analytics prose |
| Titan Embeddings | AWS administrator | course RAG ingestion/retrieval | through the authenticated Student RAG API |
| S3 course-material bucket | Teacher/backend | retrieved text only | upload original files |
| PostgreSQL/RDS | Backend maintainers | Student database | Teacher database during staged migration |
| Cognito or university IdP | University administrator | student role | teacher role |
| CloudWatch/KMS/Backup | AWS administrator | logs, encryption, recovery | logs, encryption, recovery |

## Secret handling

- Keep `AWS_BEARER_TOKEN_BEDROCK`, database URLs, and
  `TEACHER_INTEGRATION_TOKEN` in each developer's `.env` or a managed secret
  store. `.env` is ignored by Git.
- Use the same integration token in both services locally. In production,
  replace it with IAM-signed service calls or OAuth client credentials.
- Grant Bedrock model access and S3 access to backend workloads only. Browser
  and Streamlit code must never receive AWS credentials.

## Staged deployment

1. Run `docker compose up --build` for an integration environment.
2. Create PostgreSQL databases and set `STUDENT_DATABASE_URL` and
   `TEACHER_DATABASE_URL`. Fresh databases are created from SQLAlchemy metadata;
   migrate existing SQLite data separately and verify record counts.
3. Configure `MATERIALS_S3_BUCKET`, KMS encryption, lifecycle rules, backups,
   and CloudWatch alarms.
4. Configure Cognito/university SSO and replace local demo-session auth only
   after role mappings and test accounts are supplied.
5. Run the unit tests and `eval/` quality gates, then complete one end-to-end
   test: upload → RAG sync → generate/publish → submit/grade → analytics.

## Decisions that require the university

Retention periods, deletion requests, staff access rules, incident contacts,
IdP metadata, AWS account/region, approved Bedrock models, and budget alarms
cannot be safely selected in application code. Record these decisions before
handling real student data.
