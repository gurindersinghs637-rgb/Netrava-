import 'package:flutter/material.dart';
import '../../core/network/api_client.dart';
import '../../models/patient.dart';
import '../../models/prediction.dart';
import '../../models/report.dart';
import '../../providers/session.dart';
import '../../services/pdf_files.dart';
import '../../widgets/clinical_widgets.dart';

/// Screening-ID lookup, persisted clinical review, immutable sign-off and PDF.
class ReportScreen extends StatefulWidget {
  final Session session;
  final String? screeningId;
  final Prediction? prediction;
  final Patient? patient;
  const ReportScreen({
    super.key,
    required this.session,
    this.screeningId,
    this.prediction,
    this.patient,
  });
  @override
  State<ReportScreen> createState() => _ReportScreenState();
}

class _ReportScreenState extends State<ReportScreen> {
  final _id = TextEditingController(), _notes = TextEditingController();
  ClinicalReport? _report;
  String? _loadedId, _error, _message;
  bool _busy = false,
      _missing = false,
      _urgent = false,
      _overrideEnabled = false;
  int? _grade;
  int _override = 0;
  bool get _canReview => widget.session.user?.canReview == true;
  bool get _editable =>
      _canReview && (_report != null || _missing) && _report?.signed != true;
  @override
  void initState() {
    super.initState();
    _id.text = widget.screeningId ?? '';
    _grade = widget.prediction?.grade;
    if (_id.text.isNotEmpty) _load();
  }

  @override
  void dispose() {
    _id.dispose();
    _notes.dispose();
    super.dispose();
  }

  bool _validId() => RegExp(
    r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$',
  ).hasMatch(_id.text.trim());
  void _apply(ClinicalReport report) {
    _report = report;
    _missing = false;
    _grade = report.grade;
    _overrideEnabled = report.override != null;
    _override = report.override ?? report.grade;
    _urgent = report.urgent;
    _notes.text = report.notes ?? '';
  }

  Future<void> _load() async {
    if (_busy) return;
    if (!_validId()) {
      setState(() => _error = 'Enter a valid screening UUID.');
      return;
    }
    final id = _id.text.trim();
    setState(() {
      _busy = true;
      _error = null;
      _message = null;
      _report = null;
      _missing = false;
      _loadedId = null;
      _notes.clear();
      _urgent = false;
      _overrideEnabled = false;
      _grade = widget.prediction?.grade;
    });
    try {
      final report = await widget.session.reports.get(id);
      if (mounted) {
        setState(() {
          _loadedId = id;
          _apply(report);
        });
      }
    } on ApiFailure catch (e) {
      if (mounted) {
        setState(() {
          if (e.status == 404 && e.code == 'REPORT_NOT_FOUND') {
            _missing = true;
            _loadedId = id;
            _message = _canReview
                ? 'No report was found. If this is a screening in your clinic with a saved prediction, you can create its clinical review below.'
                : 'No report was found for this ID. Ask your clinician to review the screening or check the screening ID.';
          } else {
            _error = e.message;
          }
        });
      }
    } catch (_) {
      if (mounted) setState(() => _error = 'Unable to read this report.');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _save(bool sign) async {
    if (_grade == null) {
      setState(() => _error = 'Select a confirmed DR grade before saving.');
      return;
    }
    if (_busy || !_editable || _loadedId == null) return;
    if (_notes.text.length > 5000) {
      setState(
        () => _error = 'Clinical notes must be at most 5,000 characters.',
      );
      return;
    }
    if (sign) {
      final confirmed = await showDialog<bool>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('Sign off this report?'),
          content: const Text(
            'A signed report cannot be edited. Confirm that you have reviewed the retinal images and the latest saved AI prediction for this screening.',
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('Keep draft'),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(context, true),
              child: const Text('Sign off'),
            ),
          ],
        ),
      );
      if (confirmed != true || !mounted || widget.session.user == null) return;
    }
    setState(() {
      _busy = true;
      _error = null;
      _message = null;
    });
    try {
      final report = await widget.session.reports.save(_loadedId!, {
        'overall_grade': _grade,
        'grade_override': _overrideEnabled ? _override : null,
        'ophthalmologist_notes': _notes.text.isEmpty ? null : _notes.text,
        'is_urgent_referral': _urgent,
        'is_signed_off': sign,
      });
      if (mounted) {
        setState(() {
          _apply(report);
          _message = sign ? 'Report signed off.' : 'Review draft saved.';
        });
      }
    } catch (e) {
      if (mounted) setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _pdf() async {
    if (_busy || _loadedId == null || _report == null) return;
    final owner = widget.session.user?.id;
    setState(() {
      _busy = true;
      _error = null;
      _message = null;
    });
    try {
      final bytes = await widget.session.reports.pdf(_loadedId!);
      if (!mounted || owner == null || widget.session.user?.id != owner) return;
      final message = await PdfFiles.instance.saveAndOpen(_loadedId!, bytes);
      if (mounted) setState(() => _message = message);
    } catch (e) {
      if (mounted) {
        setState(
          () => _error = e is ApiFailure
              ? e.message
              : 'Unable to download or open the PDF. Please retry.',
        );
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => PopScope(
    canPop: !_busy,
    child: PageBody(
      children: [
        const SectionHeading(
          'Clinical reports',
          subtitle:
              'Open a screening by its ID to read a report or submit a clinical review.',
        ),
        if (widget.patient != null)
          ClinicalDataRow(
            'Patient',
            '${widget.patient!.name} · ${widget.patient!.code}',
          ),
        TextField(
          controller: _id,
          readOnly: widget.screeningId != null,
          enabled: !_busy,
          decoration: const InputDecoration(
            labelText: 'Screening ID',
            hintText: 'Paste screening UUID',
            prefixIcon: Icon(Icons.qr_code_2),
          ),
          onChanged: (_) => setState(() {
            _loadedId = null;
            _report = null;
            _missing = false;
            _error = null;
            _message = null;
          }),
        ),
        const SizedBox(height: 16),
        PrimaryAction(
          'Open screening report',
          busy: _busy,
          onPressed: _load,
          icon: Icons.search,
        ),
        const SizedBox(height: 20),
        ErrorNotice(_error),
        if (_message != null) ClinicalCard(child: Text(_message!)),
        if (_report != null) _details(),
        if (_editable) _editor(),
        if (_report != null) ...[
          PrimaryAction(
            'Download & open PDF',
            busy: _busy,
            onPressed: _pdf,
            icon: Icons.download_outlined,
          ),
          const SizedBox(height: 16),
          const Text(
            'PDFs are saved in private app storage and cleared on logout. The current report PDF contains clinical data and probabilities; the Grad-CAM image is available on the AI result screen.',
          ),
        ],
        const SizedBox(height: 24),
        const Text(clinicalDisclaimer),
      ],
    ),
  );
  Widget _details() => ClinicalCard(
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SectionHeading(_report!.signed ? 'Signed report' : 'Review draft'),
        ClinicalDataRow('Report ID', _report!.id),
        ClinicalDataRow('Linked prediction ID', _report!.json['prediction_id']),
        ClinicalDataRow('Confirmed grade', _report!.grade),
        ClinicalDataRow('Grade override', _report!.override),
        ClinicalDataRow('Final grade', _report!.override ?? _report!.grade),
        ClinicalDataRow('Urgent referral', _report!.urgent ? 'Yes' : 'No'),
        ClinicalDataRow('Clinical notes', _report!.notes),
        if (_report!.signed)
          ClinicalDataRow('Signed off at', _report!.json['signed_off_at']),
        ClinicalDataRow('Last updated', _report!.json['updated_at']),
      ],
    ),
  );
  Widget _editor() => ClinicalCard(
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SectionHeading(
          'Clinician review',
          subtitle:
              'Saving links the report to the latest persisted prediction for this screening.',
        ),
        DropdownButtonFormField<int>(
          isExpanded: true,
          key: ValueKey('grade-$_loadedId-$_grade'),
          initialValue: _grade,
          decoration: const InputDecoration(labelText: 'Confirmed DR grade'),
          items: _grades(),
          onChanged: _busy ? null : (v) => setState(() => _grade = v!),
        ),
        SwitchListTile(
          contentPadding: EdgeInsets.zero,
          title: const Text('Set grade override'),
          value: _overrideEnabled,
          onChanged: _busy ? null : (v) => setState(() => _overrideEnabled = v),
        ),
        if (_overrideEnabled)
          DropdownButtonFormField<int>(
            isExpanded: true,
            initialValue: _override,
            decoration: const InputDecoration(labelText: 'Override grade'),
            items: _grades(),
            onChanged: _busy ? null : (v) => setState(() => _override = v!),
          ),
        const SizedBox(height: 20),
        TextField(
          controller: _notes,
          enabled: !_busy,
          maxLines: 5,
          maxLength: 5000,
          decoration: const InputDecoration(labelText: 'Clinical notes'),
        ),
        SwitchListTile(
          contentPadding: EdgeInsets.zero,
          title: const Text('Urgent referral'),
          value: _urgent,
          onChanged: _busy ? null : (v) => setState(() => _urgent = v),
        ),
        PrimaryAction(
          'Save review draft',
          busy: _busy,
          onPressed: () => _save(false),
          icon: Icons.save_outlined,
        ),
        const SizedBox(height: 12),
        OutlinedButton.icon(
          onPressed: _busy ? null : () => _save(true),
          icon: const Icon(Icons.verified_outlined),
          label: const Text('Sign off report'),
        ),
      ],
    ),
  );
  List<DropdownMenuItem<int>> _grades() => [
    for (final e in const {
      0: 'No DR',
      1: 'Mild',
      2: 'Moderate',
      3: 'Severe',
      4: 'Proliferative DR',
    }.entries)
      DropdownMenuItem(value: e.key, child: Text('${e.key} · ${e.value}')),
  ];
}
