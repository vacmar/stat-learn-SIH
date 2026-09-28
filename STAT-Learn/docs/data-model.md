# Data model

The canonical schema and entity relationships are documented in **[backend/docs/data-model.md](../backend/docs/data-model.md)** and implemented in `backend/infra/exasol/schema.sql`.

## Summary

- **Catalog**: career roles, skills, courses, projects, prerequisite graph, course→skill weights.
- **Learner**: account, profile, self-reported proficiency, goals.
- **Runtime state**: path instances, path nodes (status), learning progress, conversations, evidence ledger, proficiency/confidence per skill.
- **Verification**: sessions storing fused assessment/practical/evidence/coursework signals.

Analytical SQL in `backend/infra/exasol/queries.sql` supports gap analysis and path ranking without LLM calls.
