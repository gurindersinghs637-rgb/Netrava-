# NETRAVA signup password and recovery flow

## Audit
Signup already validated matching passwords and sent only password (never confirm_password) to Supabase Auth. Existing accounts retained their original passwords. The earlier generic rejection text obscured this distinction. Recovery was absent. Passwords are not stored in user_profiles, clinics, or application files.

## Behavior
New email: submit name/email/phone/chosen password/confirmation. Backend validates, checks Auth account existence with backend-only paginated admin reads, then sends only the chosen password and name/phone metadata to GoTrue. The deployed active-signup trigger must create the active technician profile and private workspace. Provider email confirmation remains respected.
Existing email (confirmed or unconfirmed): HTTP 409 EMAIL_EXISTS, with ?This email is already registered. Please log in with your existing password or use Forgot Password to reset it.? Signup never updates that existing password. Concurrent duplicate creation is also handled from GoTrue errors/obfuscated identities. The admin lookup suits this small project; replace the linear lookup with a reviewed indexed identity lookup before large-scale deployment.
Forgot Password: login link opens a validated email form. POST /api/v1/auth/forgot-password asks Supabase /recover to send an email and returns an account-existence-neutral acknowledgement. Sending does not reset a password. The email opens a browser page; the user chooses matching new passwords. POST /api/v1/auth/reset-password exchanges token_hash with type=recovery and updates the password through Supabase /user. No service-role password reset, plaintext persistence or clinical-role bypass occurs. Return to the app and log in with the new password.

The one-time token is carried in the URL fragment, removed immediately by the reset script and kept only in memory; no token query string is needed. Reset responses use no-store and no-referrer; CSP disallows third-party content and framing. Reset forms never return tokens. A rejected password can consume the recovery token; the error tells the user to request a new link.

## Files changed / added
- backend/app/core/config.py: PASSWORD_RESET_REDIRECT_URL.
- backend/app/schemas/auth.py: strict forgot/reset schemas, matching-password validation and message response.
- backend/app/services/auth_service.py: existing-email detection and clear error text.
- backend/app/services/password_recovery.py: recover, verify recovery proof, update Supabase password.
- backend/app/api/v1/auth.py: POST forgot-password, POST reset-password, GET reset page and reset script.
- backend/app/templates/reset_password.html and reset_password.js: browser reset form.
- frontend/flutter_app/lib/services/auth_service.dart: recovery email API.
- frontend/flutter_app/lib/screens/auth/sign_in_screen.dart: Forgot Password navigation.
- frontend/flutter_app/lib/screens/auth/forgot_password_screen.dart: validated recovery request UI.
- backend/tests/test_signup.py and test_password_recovery.py: chosen-password, duplicates, reset security, one-time use, login tests.
- frontend/flutter_app/test/forgot_password_test.dart and test/support/fixture_api.dart: recovery UI test fixture.
- supabase/templates/recovery.html: reviewed email template to deploy manually.
- .env.example and local untracked .env: configurable reset URL (no secret values documented).
- shared/api_contracts/openapi_contract.json: regenerated contract.
- docs/API_DOCUMENTATION.md, docs/architecture/backend_architecture.md, docs/agents/WORK_LOG.md, IMPLEMENTATION_PLAN.md: contract and handover.

## Local configuration (no public HTTPS URL required yet)
PASSWORD_RESET_REDIRECT_URL=http://127.0.0.1:8000/api/v1/auth/reset-password
The local .env has been set to this value. The backend must be running and the email link must be opened in a browser ON THIS PC. On a physical phone, localhost means the phone and will not reach the PC. The Android app can request the email through its existing 10.0.2.2 API URL; open that email on the PC for this setup.

## Required Supabase configuration ? not changed automatically
1. Review/apply the existing 202611140002_active_signup.sql if the active workspace trigger is not deployed. Recovery itself needs no additional SQL migration.
2. In Auth URL Configuration, allow the exact reset URL above for development. Later set PASSWORD_RESET_REDIRECT_URL to the public HTTPS backend reset page, allow that URL in Supabase, and restart the backend. Production/staging recovery rejects HTTP.
3. In Auth Email Templates > Reset Password, use supabase/templates/recovery.html. Its link must be:
   <a href="{{ .RedirectTo }}#token_hash={{ .TokenHash }}">Reset password</a>
   The default ConfirmationURL template is incompatible with this recovery-only token-hash page. Configure both the URL and template together.
4. Configure email delivery/SMTP for the test recipient; provider quotas and recipient restrictions still apply. Do not claim that the acknowledgement proves inbox delivery.
5. For new-user login without a confirmation link, configure Confirm email appropriately in the development project. Otherwise confirm the signup email before login. This is separate from password recovery.
6. Restart the API and install the rebuilt app to see Forgot Password.

## Test email required
Provide a working new email address whose inbox you control, never registered in this Supabase project (an ordinary Gmail/Outlook inbox is suitable). No mailbox password is needed or wanted. The owner opens signup/reset emails. Use a new NETRAVA app password, not the mailbox password; choose and enter it privately in the app. This also verifies a genuinely new Auth user rather than reusing the repaired old account.

## Verification
136 backend tests passed, including new-password signup-to-login tests and controlled recovery-email/one-time-token/password-update/old-password-rejection/new-password-login/me tests. 11 Flutter tests passed, including recovery validation and public-transport payload. Dart analysis passed with no issues. Reset JavaScript syntax check passed. Running backend health, reset page and script returned 200; page no-store verified. These recovery provider calls use controlled transports: real inbox delivery, real recovery consumption and a new hosted user's chosen-password login have NOT been claimed as verified.

## Verdict
NOT READY for live acceptance. Local code and controlled flows pass. Remaining gates: owner supplies the fresh email, reviews/deploys active-signup trigger as needed, allows the reset URL and configures the recovery template/email delivery; then complete real signup -> confirmation if enabled -> login -> Forgot Password email -> new password -> login. Existing user profile repair did not authorize unrelated hosted auth setting changes. No recovery email was sent, no existing password changed, and no new hosted account created in this implementation turn.

## Official reference
https://supabase.com/docs/guides/auth/passwords
https://supabase.com/docs/guides/auth/auth-email-templates


Password policy correction: actual hosted signup returned HTTP 422 with numeric code=422, error_code=weak_password and minimum 12 characters. Fixed error_code precedence over numeric code; signup/reset confirmation schemas and Flutter/browser reset validation now require 12 characters. Existing login still allows historical passwords. Diagnostic signup was rejected; no account created or password changed. 57 authentication/signup/recovery tests passed.
