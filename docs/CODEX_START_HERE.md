# Codex Start Here

For every continuation session:

1. Read the root `AGENT.md` and `docs/PROJECT_HANDOFF.md`.
2. Read `docs/PROJECT_AUDIT.md`, then the architecture and API docs relevant to the task.
3. Inspect the current implementation and current filesystem state. Historical work logs and reports are not proof that code works.
4. Preserve existing Flutter work and `ai_model/checkpoint/best_efficientnet_b3_staged.pth`. Never alter trained weights without explicit owner approval.
5. The project is not currently a Git repository. Do not assume a branch, commit, or clean status exists; preserve work and report this limitation.
6. Use the repository root as working directory. Backend imports use `backend.app...`; the Windows startup command is in `docs/PROJECT_HANDOFF.md`.
7. Treat Supabase schema/RLS/storage integration as unverified: migration/seed/test directories are empty. Do not connect to production or apply database changes without explicit owner approval.
8. Before handling patient data, resolve trusted Supabase token verification, trusted role/clinic lookup, and server-side clinic isolation. Do not trust frontend-supplied role or clinic values.
9. Run only relevant tests in the available environment and record exact outcomes. Never claim clinical validation from software tests.
10. Update the audit and handoff whenever verified implementation status changes. Do not document intended behavior as implemented behavior.

Current high-priority gaps are listed in `docs/PROJECT_AUDIT.md` and `docs/PROJECT_HANDOFF.md`.
