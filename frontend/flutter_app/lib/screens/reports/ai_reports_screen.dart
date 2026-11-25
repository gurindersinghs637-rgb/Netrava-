import 'package:flutter/material.dart';
import '../../providers/session.dart';
import '../../widgets/clinical_widgets.dart';
import 'ai_report_screen.dart';

/// Technician entry point; never reads or creates clinician reviews.
class AiReportsScreen extends StatefulWidget {
  final Session session;
  const AiReportsScreen({super.key, required this.session});

  @override
  State<AiReportsScreen> createState() => _AiReportsScreenState();
}

class _AiReportsScreenState extends State<AiReportsScreen> {
  final _id = TextEditingController();
  String? _error;

  @override
  void dispose() {
    _id.dispose();
    super.dispose();
  }

  void _open(String id, {String? predictionId}) {
    if (id.trim().isEmpty) {
      setState(() => _error = 'Enter a screening ID.');
      return;
    }
    setState(() => _error = null);
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => AiReportScreen(
          session: widget.session,
          screeningId: id.trim(),
          predictionId: predictionId,
          generateOnOpen: true,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) => PageBody(
    children: [
      const SectionHeading(
        'AI screening reports',
        subtitle:
            'Saved results from this signed-in session. Clinician review is not required.',
      ),
      if (widget.session.recentAiReports.isEmpty)
        const ClinicalCard(
          child: Text('Complete an AI screening to see its report here.'),
        ),
      for (final entry in widget.session.recentAiReports)
        ClinicalCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                entry.patientName,
                style: Theme.of(context).textTheme.titleMedium,
              ),
              Text('Patient reference: ${entry.patientCode}'),
              if (entry.screeningDate != null)
                Text(
                  'Screening: ${entry.screeningDate!.toLocal().toString().split('.').first}',
                ),
              Text('Grade ${entry.grade} · ${entry.gradeName}'),
              Text(
                'Confidence ${(entry.confidence * 100).toStringAsFixed(1)}%',
              ),
              TextButton.icon(
                onPressed: () =>
                    _open(entry.screeningId, predictionId: entry.predictionId),
                icon: const Icon(Icons.visibility),
                label: const Text('View Report'),
              ),
            ],
          ),
        ),
      const SectionHeading(
        'Find another screening',
        subtitle:
            'Use a screening reference shared by your clinic. This opens its latest saved prediction.',
      ),
      TextField(
        controller: _id,
        decoration: const InputDecoration(labelText: 'Screening ID'),
      ),
      PrimaryAction(
        'Generate AI Screening Report',
        onPressed: () => _open(_id.text),
        icon: Icons.picture_as_pdf_outlined,
      ),
      ErrorNotice(_error),
    ],
  );
}
