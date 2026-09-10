# Working agreement

This is a take-home backend challenge being built incrementally for learning.

- Read `PROGRESS.md` before starting work. Inspect the relevant code and tests to
  verify the recorded state before resuming.
- Work on one agreed milestone at a time. Keep changes small and easy to review.
- Explain significant choices and unfamiliar concepts in plain language.
- Prefer straightforward code and minimal dependencies. Create files only when
  the current milestone needs them.
- Add meaningful tests alongside each feature. Run checks appropriate to the
  change and report their actual results.
- Do not add optional features or unrelated refactors.
- Flag conflicting requirements and unresolved decisions before implementing
  the affected behavior. Distinguish source requirements from proposed choices.
- At the end of each milestone, update `PROGRESS.md`, summarize changes,
  verification, and limitations, then stop for user review.
- Keep "implemented, awaiting review" separate from "accepted". Only record
  acceptance when the user provides it. Do not automatically start the next
  milestone.
- Do not commit or push unless the user explicitly requests it.

The intended stack is FastAPI, Pydantic, PostgreSQL, SQLAlchemy, Alembic, JWT
authentication, Docker Compose, and Nginx in front of Uvicorn. Introduce each
component only in its relevant milestone.
