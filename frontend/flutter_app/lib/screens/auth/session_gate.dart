import 'package:flutter/material.dart';
import '../../providers/session.dart';
import '../../widgets/clinical_widgets.dart';
import '../dashboard/dashboard_screen.dart';
import 'sign_in_screen.dart';

/// Startup authentication check with recoverable network/storage failure states.
class SessionGate extends StatelessWidget {
  final Session session;
  const SessionGate({super.key, required this.session});
  @override
  Widget build(BuildContext context) {
    if (session.initializing || session.startupError != null) {
      return Scaffold(
        body: SafeArea(
          child: PageBody(
            children: [
              const SizedBox(height: 100),
              const BrandMark(),
              const SizedBox(height: 48),
              if (session.initializing) ...[
                const Center(child: CircularProgressIndicator()),
                const SizedBox(height: 24),
                const Center(
                  child: Text('Preparing your screening workspace…'),
                ),
              ] else ...[
                ErrorNotice(session.startupError),
                PrimaryAction(
                  'Retry session check',
                  onPressed: session.restore,
                ),
                TextButton(
                  onPressed: session.logout,
                  child: const Text('Clear session and sign in'),
                ),
              ],
            ],
          ),
        ),
      );
    }
    return session.user == null
        ? SignInScreen(session: session)
        : DashboardScreen(session: session);
  }
}
