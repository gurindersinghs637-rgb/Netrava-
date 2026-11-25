import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../providers/session.dart';
import '../../widgets/clinical_widgets.dart';
import '../patients/patient_list_screen.dart';
import '../reports/report_screen.dart';
import '../reports/ai_report_screen.dart';
import '../reports/ai_reports_screen.dart';
import '../profile/profile_screen.dart';

/// Role-aware workspace with API-backed actions and session-only activity.
class DashboardScreen extends StatefulWidget {
  final Session session;
  const DashboardScreen({super.key, required this.session});
  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  int _tab = 0;
  Map<String, dynamic>? _health;
  String? _healthError;
  @override
  void initState() {
    super.initState();
    _checkHealth();
  }

  Future<void> _checkHealth() async {
    try {
      final response = await widget.session.api.execute(
        () => widget.session.api.dio.get('/health'),
      );
      if (mounted) {
        setState(() {
          _health = Map<String, dynamic>.from(response.data);
          _healthError = null;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(
          () => _healthError =
              'Backend status is unavailable. Check your connection.',
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(
      title: const Text('NETRAVA'),
      actions: [
        IconButton(
          tooltip: 'Profile',
          onPressed: () => setState(() => _tab = 3),
          icon: const Icon(Icons.account_circle_outlined),
        ),
      ],
    ),
    body: SafeArea(
      child: switch (_tab) {
        1 => PatientListScreen(session: widget.session),
        2 =>
          widget.session.user!.canReview
              ? ReportScreen(session: widget.session)
              : AiReportsScreen(session: widget.session),
        3 => ProfileScreen(session: widget.session),
        _ => _home(),
      },
    ),
    bottomNavigationBar: NavigationBar(
      selectedIndex: _tab,
      onDestinationSelected: (i) => setState(() => _tab = i),
      destinations: const [
        NavigationDestination(
          icon: Icon(Icons.home_outlined),
          selectedIcon: Icon(Icons.home),
          label: 'Home',
        ),
        NavigationDestination(
          icon: Icon(Icons.people_outline),
          selectedIcon: Icon(Icons.people),
          label: 'Patients',
        ),
        NavigationDestination(
          icon: Icon(Icons.description_outlined),
          selectedIcon: Icon(Icons.description),
          label: 'Reports',
        ),
        NavigationDestination(
          icon: Icon(Icons.person_outline),
          selectedIcon: Icon(Icons.person),
          label: 'Profile',
        ),
      ],
    ),
  );
  Widget _home() {
    final user = widget.session.user!;
    return PageBody(
      children: [
        if (_healthError != null) ErrorNotice(_healthError),
        if (_health?['status'] == 'degraded')
          ClinicalCard(
            child: Column(
              children: [
                const Text(
                  'Some screening services are unavailable. Your clinic may need to check backend connectivity.',
                ),
                TextButton(
                  onPressed: _checkHealth,
                  child: const Text('Check again'),
                ),
              ],
            ),
          ),
        SectionHeading(
          'Hello, ${user.fullName.isEmpty ? 'care team' : user.fullName.split(' ').first}.',
          subtitle:
              '${user.roleLabel} • ${user.clinicName ?? 'Clinic workspace'}',
        ),
        ClinicalCard(
          color: AppColors.featureIconBg,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Icon(
                Icons.visibility_outlined,
                size: 38,
                color: AppColors.primaryGreen,
              ),
              const SizedBox(height: 16),
              const SectionHeading(
                'Small steps. Clearer futures.',
                subtitle:
                    'Bring retinal screening closer to the people who need it.',
              ),
              PrimaryAction(
                'Start a new screening',
                icon: Icons.add_a_photo_outlined,
                onPressed: () => Navigator.of(context).push(
                  MaterialPageRoute(
                    builder: (_) => Scaffold(
                      appBar: AppBar(title: const Text('Select a patient')),
                      body: PatientListScreen(
                        session: widget.session,
                        selecting: true,
                      ),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
        Row(
          children: [
            Expanded(
              child: _action(
                'Patients',
                'Clinic registry',
                Icons.people_outline,
                () => setState(() => _tab = 1),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _action(
                user.canReview ? 'Clinical review' : 'Reports',
                user.canReview ? 'Review & sign off' : 'View & download',
                Icons.description_outlined,
                () => setState(() => _tab = 2),
              ),
            ),
          ],
        ),
        const SectionHeading(
          'This session',
          subtitle:
              'Screening IDs created while you are signed in. Copy an ID to share with a clinician.',
        ),
        if (widget.session.recentScreenings.isEmpty)
          const ClinicalCard(
            child: Text('Your new screenings will appear here.'),
          ),
        for (final id in widget.session.recentScreenings)
          ClinicalCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                ClinicalDataRow('Screening ID', id),
                TextButton.icon(
                  onPressed: () => Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (_) => widget.session.user!.canReview
                          ? Scaffold(
                              appBar: AppBar(
                                title: const Text('Screening report'),
                              ),
                              body: ReportScreen(
                                session: widget.session,
                                screeningId: id,
                              ),
                            )
                          : AiReportScreen(
                              session: widget.session,
                              screeningId: id,
                              generateOnOpen: true,
                            ),
                    ),
                  ),
                  icon: const Icon(Icons.open_in_new),
                  label: const Text('Open report'),
                ),
              ],
            ),
          ),
        const Text(clinicalDisclaimer),
      ],
    );
  }

  Widget _action(
    String title,
    String subtitle,
    IconData icon,
    VoidCallback action,
  ) => ClinicalCard(
    child: InkWell(
      onTap: action,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 32, color: AppColors.primaryGreen),
          const SizedBox(height: 12),
          Text(title, style: Theme.of(context).textTheme.titleMedium),
          Text(subtitle),
        ],
      ),
    ),
  );
}
