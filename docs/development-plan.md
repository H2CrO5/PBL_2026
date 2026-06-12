# Development Plan

## Strategy

The project has four developers, one AWS account, and two groups. Development should be organized around two product parts: Student Part and Teacher Part. The shared backend defines API contracts, data model, RAG pipeline, and LLM prompt contracts, but it should be treated as common infrastructure rather than a third team.

- Group 1, Student Part: two developers.
- Group 2, Teacher Part: two developers.
- Shared backend work is split by feature ownership and coordinated through API/schema documents.

Current development assumption:

- The two groups should first make their own modules runnable independently.
- Student Part and Teacher Part do not need to share one complete backend at the beginning.
- Each group may temporarily use local data, mock APIs, local databases, or sample files while developing its own module.
- After both parts are independently functional, the team will enter the integration phase and unify authentication, database schema, RAG, LLM calls, API contracts, and AWS resources.
- This means the current Student Part can be considered aligned with the plan if it runs independently and covers the student learning workflow.

## Phase 1: Requirement Definition and System Design

Objective: align all teams on system behavior and interfaces.

Shared tasks:

- Finalize system architecture.
- Define database schema.
- Define API contracts.
- Select LLM provider and model strategy.
- Design RAG ingestion and retrieval flow.
- Define data flow between student answers, analytics, and assignment generation.

Student Part tasks:

- Design dashboard, assignment workflow, answer submission, feedback, and learning history UX.
- Define student memory fields required by the backend.

Teacher Part tasks:

- Design teacher dashboard, analytics metrics, material management, and individual student analysis.
- Define teacher report structure.

Deliverables:

- Architecture diagram.
- API specification.
- Database schema.
- UI wireframes.

## Phase 2: Module Backend Foundation

Objective: build the minimum backend foundation needed for each module to run. At this stage, the backend can still be module-local or mock-based. The goal is to validate each workflow before full integration.

RAG tasks:

- Material upload pipeline.
- PDF/slide parsing.
- Chunking and metadata extraction.
- Embedding generation.
- Vector DB storage and retrieval.

LLM tasks:

- Prompt template management.
- Assignment generation.
- Auto-grading.
- Student feedback generation.
- Teacher analytics generation.

API tasks:

- Authentication API.
- Assignment API.
- Submission/grading API.
- Analytics API.
- Chat API.
- Material API.

Infrastructure tasks:

- Database setup.
- API Gateway or FastAPI service deployment.
- Monitoring and logging.
- Basic security controls.

Ownership:

- Student Part group owns student-facing APIs first: current assignment, answer submission, grading result, learning history, and TA Bot chat.
- Teacher Part group owns teacher-facing APIs first: material upload, teacher-authored base/required question seeds, generation context preview, class analytics, individual student analytics, and lecture recommendation.
- Both groups review shared schema changes before implementation.

Temporary independence rule:

- Student Part may use its own local database and local vector store during independent development.
- Teacher Part may use mock student data or sample material data before integration.
- Frontends should still be designed around API calls so that the final shared backend can replace local/mock services later.

Deliverables:

- Backend APIs.
- RAG pipeline.
- Vector database.
- Prompt contracts.

## Phase 3: Student Part Development

Objective: build the student learning experience.

Frontend tasks:

- Student dashboard.
- Assignment interface.
- Answer submission page.
- Feedback page.
- Learning history page.
- TA Bot UI.

Student AI tasks:

- Understanding estimation display.
- Adaptive assignment request flow.
- Follow-up question generation.
- TA Bot integration.

Student memory tasks:

- Answer history.
- Understanding history.
- Weak-topic tracking.
- Questions asked.

Deliverables:

- Student UI.
- Assignment workflow.
- Feedback workflow.
- TA Bot integration.

Current uploaded Student Part alignment:

- The uploaded `student/` module already matches the independent Student Part stage.
- It includes login, assignment display, answer submission, auto-grading, feedback, history, and TA Bot.
- It currently uses `FastAPI`, `Streamlit`, `SQLite`, `FAISS`, and `AWS Bedrock`.
- Using local `SQLite` and local `FAISS` is acceptable before the final integration phase.

Current Student Part APIs:

- `POST /auth/login`
- `GET /assignments/pending`
- `GET /assignments/pending/by-lecture`
- `POST /assignments/submit`
- `GET /assignments/history`
- `GET /assignments/history/by-lecture`
- `GET /dashboard/summary`
- `GET /dashboard/trends`
- `POST /chat/message`
- `GET /chat/history`

Future shared API mapping:

- `GET /assignments/pending` will map to `GET /students/{student_id}/assignments/current`.
- `POST /assignments/submit` can either stay as one submit-and-grade endpoint or be split into `POST /assignments/{assignment_id}/submissions` and `POST /submissions/{submission_id}/grade`.
- `GET /assignments/history` will map to `GET /students/{student_id}/history`.
- `POST /chat/message` will map to shared `POST /chat`.

## Phase 4: Teacher Part Development

Objective: build analytics and monitoring tools for faculty.

Frontend tasks:

- Teacher dashboard.
- Material management page.
- Class analytics page.
- Student analytics page.
- Report view/export.

Teacher AI tasks:

- Class understanding analysis.
- Incorrect-answer trend analysis.
- Lecture improvement suggestions.
- Next lecture focus recommendations.

Teacher memory tasks:

- Lecture history.
- Class trends.
- Material history.
- Analytics history.

Deliverables:

- Teacher UI.
- Analytics dashboard.
- Report generation system.

## Phase 5: System Integration

Objective: connect Student Part, Teacher Part, and shared backend.

Integration tasks:

- API integration.
- Database integration.
- LLM integration.
- Authentication integration.
- Role-based routing.

Data synchronization:

- Student answers update analytics.
- Analytics informs future adaptive assignment generation.
- Teacher materials update the RAG knowledge base.
- Teacher-authored base/required question seeds become constraints and anchors for generated assignments.
- TA Bot uses the same course materials and student context.

Integration unification:

- Authentication changes from student-only login to role-based login for student, teacher, and TA.
- Student Part assignment workflows and teacher-authored question seeds are mapped into one shared assignment-generation contract.
- Student submissions become the source data for teacher analytics.
- Student weak/strong topics evolve into shared concept-level student memory.
- Teacher material upload becomes the source of the shared RAG knowledge base.
- Local/mock databases are replaced by one shared database schema.
- Local/mock vector stores are replaced by one shared RAG/vector infrastructure.
- All LLM calls go through backend services, not directly from frontend code.

Deliverables:

- Integrated end-to-end workflow.
- Shared demo dataset.
- Working student and teacher login flows.

## Phase 6: Testing and Improvement

Testing tasks:

- Unit testing.
- API testing.
- UI testing.
- End-to-end testing.
- Security and permission testing.

LLM evaluation:

- Assignment quality.
- Grading quality.
- Analytics accuracy.
- Hallucination verification.
- Citation/source grounding.

User testing:

- Student testing.
- Teacher testing.
- Feedback collection.
- Iteration based on evaluator comments.

Deliverables:

- Test report.
- LLM evaluation report.
- Improved system version.

## Team Allocation

- Group 1, Student Part, 2 people: student frontend, assignment workflow, answer submission, feedback page, learning history, TA Bot UI, student memory integration.
- Group 2, Teacher Part, 2 people: teacher frontend, material upload, analytics dashboard, visualization, individual student analysis, report system, teacher memory integration.

Shared responsibilities:

- API contracts are reviewed by all four members.
- Database schema changes are proposed in `docs/data-model.md` before implementation.
- AWS resources are created with agreed names and tags.
- Integration and QA are done together near the end of each milestone, not only at the final phase.

## One AWS Account Rules

- Use one resource prefix, for example `teachadapt-dev-*`.
- Use tags on every resource: `Project=TeachAdapt`, `Part=student|teacher|shared`, `Owner=<name>`.
- Keep one shared database and one shared auth setup unless there is a strong reason to split.
- Keep Bedrock model access and vector store configuration shared.
- Avoid deploying duplicate API gateways, duplicate databases, or duplicate vector stores.
- Use separate local `.env` files, but never commit AWS keys or secrets.
- Put resource decisions in [One AWS Account Collaboration Plan](./aws-collaboration.md).

## Recommended MVP Cut

For a course project, keep the demo sharp:

- Teacher uploads or selects sample course materials.
- Backend creates a small RAG knowledge base.
- Teacher uploads or selects materials and authors base/required question seeds.
- Shared backend generates adaptive assignments from materials, teacher seeds, student mastery, and weak-concept analytics.
- Student submits answers and receives score, correct answer, and explanation.
- Teacher sees weak concepts, common error patterns, and next lecture recommendations.

Future extensions can add personalized learning paths, multimodal materials, voice Q&A, video analysis, cross-class comparison, and syllabus optimization.
