import 'package:flutter/material.dart';
import '../../providers/session.dart';
import '../../widgets/clinical_widgets.dart';

/// Trusted profile details and local logout.
class ProfileScreen extends StatefulWidget {
  final Session session;
  const ProfileScreen({super.key, required this.session});
  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  bool _busy = false;
  String? _error;
  Future<void> _refresh() async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await widget.session.refreshProfile();
    } catch (_) {
      if (mounted) {
        setState(
          () => _error = 'Unable to refresh your profile. Please retry.',
        );
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  void initState() {
    super.initState();
    _refresh();
  }

  @override
  Widget build(BuildContext context) {
    final user = widget.session.user;
    if (user == null) return const SizedBox.shrink();
    return PageBody(
      children: [
        const SectionHeading(
          'Your profile',
          subtitle: 'Your verified clinic identity.',
        ),
        ClinicalCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const CircleAvatar(
                radius: 32,
                child: Icon(Icons.person_outline, size: 36),
              ),
              const SizedBox(height: 16),
              ClinicalDataRow('Full name', user.fullName),
              ClinicalDataRow('Email', user.email),
              ClinicalDataRow('Role', user.roleLabel),
              ClinicalDataRow('Clinic', user.clinicName),
            ],
          ),
        ),
        ErrorNotice(_error),
        PrimaryAction(
          'Refresh profile',
          busy: _busy,
          onPressed: _refresh,
          icon: Icons.refresh,
        ),
        const SizedBox(height: 16),
        OutlinedButton.icon(
          onPressed: widget.session.logout,
          icon: const Icon(Icons.logout),
          label: const Text('Log out'),
        ),
        const SizedBox(height: 24),
        const Text('Your account is managed by your clinic administrator.'),
      ],
    );
  }
}
