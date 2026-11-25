import 'package:flutter/material.dart';
import '../../models/patient.dart';
import '../../providers/session.dart';
import '../../widgets/clinical_widgets.dart';
import '../screening/screening_screen.dart';

/// Read-only details fetched from the clinic-scoped patient endpoint.
class PatientDetailScreen extends StatefulWidget {
  final Session session;
  final String patientId;
  const PatientDetailScreen({
    super.key,
    required this.session,
    required this.patientId,
  });
  @override
  State<PatientDetailScreen> createState() => _PatientDetailScreenState();
}

class _PatientDetailScreenState extends State<PatientDetailScreen> {
  Patient? _patient;
  String? _error;
  bool _busy = true;
  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final p = await widget.session.patients.get(widget.patientId);
      if (mounted) setState(() => _patient = p);
    } catch (e) {
      if (mounted) setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Patient details')),
    body: SafeArea(
      child: PageBody(
        children: [
          ErrorNotice(_error),
          if (_error != null) PrimaryAction('Retry', onPressed: _load),
          if (_busy) const Center(child: CircularProgressIndicator()),
          if (!_busy && _patient != null) ...[
            SectionHeading(_patient!.name, subtitle: _patient!.code),
            ClinicalCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  for (final field in const {
                    'date_of_birth': 'Date of birth',
                    'sex': 'Gender',
                    'phone': 'Phone',
                    'email': 'Email',
                    'diabetes_type': 'Diabetes type',
                    'diabetes_duration_years': 'Years since diagnosis',
                    'latest_hba1c': 'Latest HbA1c (%)',
                    'is_insulin_dependent': 'Insulin dependent',
                    'medical_notes': 'Clinical notes',
                  }.entries)
                    ClinicalDataRow(field.value, _patient!.details[field.key]),
                  ClinicalDataRow('Patient ID', _patient!.id),
                ],
              ),
            ),
            PrimaryAction(
              'Start screening',
              icon: Icons.add_a_photo_outlined,
              onPressed: () => Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => ScreeningScreen(
                    session: widget.session,
                    patient: _patient!,
                  ),
                ),
              ),
            ),
          ],
        ],
      ),
    ),
  );
}
