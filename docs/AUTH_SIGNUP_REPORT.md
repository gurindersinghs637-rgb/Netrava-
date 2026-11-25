# Simplified signup and login ? 2026-11-14

This report supersedes the earlier pending-approval signup report.

## Audit and decision
The previous Auth insert trigger created inactive technicians with NULL clinic_id. fetch_active_profile rejected inactive profiles and missing/inactive clinics. Clinical APIs, PostgreSQL write functions, Storage paths and RLS depend on trusted clinic IDs. Removing only the login clinic check would leave clinical operations broken. A shared demo clinic would expose unrelated users' data to each other.

The minimal secure solution provisions a separate active clinic/workspace for each new signup, together with an active technician profile. Existing clinic checks, RLS and clinical write functions stay intact. Users cannot choose roles, activation state or clinic membership. Existing users and disabled accounts are untouched. Technicians retain existing privileges: intake, screening, predictions, viewing reports/PDF; clinical review and sign-off still require an ophthalmologist. A public signup does not gain clinical sign-off rights.

## Changed files
- backend/app/schemas/auth.py: required phone, normalized 7?15 digit validation, active/email_confirmation_required response.
- backend/app/services/auth_service.py: passes name/phone to GoTrue; verifies persisted active technician, clinic, phone/email; reports email confirmation separately.
- backend/app/api/v1/auth.py: updated signup documentation.
- supabase/migrations/202611140002_active_signup.sql: adds email if missing, reuses phone, replaces Auth trigger with atomic private workspace + active profile provisioning.
- frontend/flutter_app/lib/services/auth_service.dart: sends phone.
- frontend/flutter_app/lib/screens/auth/sign_up_screen.dart: phone input/validation, no approval messaging, returns success to login.
- frontend/flutter_app/lib/screens/auth/sign_in_screen.dart: displays signup success message, private workspace copy.
- backend/tests/test_signup.py: phone validation and signup/login/me tests.
- frontend/flutter_app/test/signup_test.dart: updated five-field validation test.
- scripts/database_test/verify_active_signup.mjs: real local PostgreSQL/RLS checks.
- shared/api_contracts/openapi_contract.json: updated generated contract.
- docs/API_DOCUMENTATION.md, docs/architecture/backend_architecture.md, docs/agents/WORK_LOG.md, IMPLEMENTATION_PLAN.md: updated handover/contract/status.

## API and data flow
POST /api/v1/auth/signup accepts full_name, email, phone, password, confirm_password. Supabase Auth creates UUID/email/password identity; an Auth insert trigger atomically creates a private workspace and user_profiles row. If profile creation fails, Auth and workspace insertions roll back. No passwords go into profile tables. Profiles store UUID, name, email, phone, technician role, active status, clinic ID and created_at. Email/password authentication remains owned by Auth; profile email is the signup snapshot.

Registration returns 201 and status active when the provider allows login, or email_confirmation_required when Supabase still requires email verification. No administrator approval is required in either case. Flutter returns to login and displays the appropriate message. Existing POST /api/v1/auth/login, GET /api/v1/auth/me, secure token storage, local logout and restoration remain in place. JWT expiry still requires login again; refresh-token rotation is outside this change.

## Manual deployment ? no hosted changes performed
1. Review existing auth.users insert triggers/provisioning scripts for conflicts in the selected development Supabase project.
2. Ensure the reviewed normalized schema migration 202611130001_normalized_backend.sql is deployed. Never use the legacy migration. Apply 202611140001_public_signup.sql if it is not already recorded, then apply the new 202611140002_active_signup.sql LAST. Use the Supabase SQL Editor to execute each complete file. The new migration is transactional and repeatable, creates no duplicate user tables, and changes no existing profiles.
3. Supabase email/password signup must be enabled. To meet the requested immediate login flow without email verification, disable Confirm email in the development project's email provider configuration. This is a hosted setting change requiring owner approval. The application does not silently bypass provider verification. If confirmation stays enabled, follow the emailed link before login.
4. Restart the backend after deployment, rebuild/reload the Flutter application for the phone field, and register a completely new email. Existing pending profiles are intentionally not automatically activated; they require a reviewed individual update or a fresh signup email.
5. Verify the Auth identity and matching active technician profile, private clinic, email/phone/name/timestamp. Login, inspect /auth/me, create a patient, upload a real retinal image, check QC, prediction/probabilities/Grad-CAM, saved results, report and PDF. Verify duplicate email, wrong password, session and logout. Use an authorized ophthalmologist for clinical sign-off.

## Validation
117 backend tests passed in the broad run; two additional signup/login/me tests passed afterward (20 signup cases total). Ten Flutter tests passed and Dart analysis found no issues. Real local PostgreSQL checks passed for active profile/email/phone persistence, independent clinic IDs, self-profile/clinic RLS, denied direct role changes, new-user patient creation, cross-clinic denial, repeated migration execution and atomic rollback of profile/Auth/workspace writes. Controlled provider tests cover duplicate email, rate limits, outages, unsafe profiles, invalid input and email-confirmation messaging. These controlled identities are not proof of hosted GoTrue persistence.

## Verdict
NOT READY for live acceptance: the new migration and provider setting must be reviewed/deployed, then an actual new-email signup and full live Auth/Storage/database/clinical workflow must be verified. Local implementation is ready for testing. No hosted data or settings were changed. No AI weights or inference behavior were changed.

Additional workflow verification passed: 16 API checks and 50 PostgreSQL checks with actual EfficientNet-B3 inference and actual SQL. GoTrue and Storage used controlled adapters; live_auth=false and live_storage=false.

## 2026-11-15 - Duplicate clinic-name correction (supersedes constant workspace name)
Hosted clinics enforces unique clinic names. The former active-signup trigger used the same Personal screening workspace name for every account, so the second signup failed inside GoTrue with SQLSTATE23505 (followed by transaction-aborted 25P02). Apply forward migration 202611150001_unique_signup_workspace.sql after 202611140002_active_signup.sql. It names the private workspace Personal screening workspace - <full Auth user UUID>; do not reapply the older active-signup migration afterward. No RLS, existing records, clinic-name constraints or user roles are changed. The hosted function correction was applied via SQL Editor and unique_workspace_fix_installed returned true. Actual-SQL regression reproduces the former failure, validates repeat execution, same-prefix UUID uniqueness, unchanged existing records, isolation and atomic rollback. New-user phone signup/login acceptance remains pending the owner's retry. Email confirmation remains enabled and must be completed before login.

## 2026-11-15 - Immediate-login policy now enabled
Owner approved disabling hosted email confirmation. Confirm email is now OFF in the hosted Sign In / Providers page and saving succeeded; public Auth settings was independently read and returned external.email=true, mailer_autoconfirm=true. Local auth.email config matches: enable_signup=true, enable_confirmations=false. New users are provisioned directly as active technicians in unique private workspaces without email confirmation or administrator approval. Existing identities created while confirmation was enabled remain individually pending until confirmed; do not silently bulk-confirm old users. An attempted combined live confirmation/synthetic-QA creation was rejected by automatic approval review before execution, and no workaround was attempted. Existing account info is saved; its one-time confirmation and fresh post-change login acceptance remain pending explicit authorization/user action. No new APK or backend restart needed for this hosted setting.
