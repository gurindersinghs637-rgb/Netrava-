import 'package:flutter/material.dart';
import '../../providers/session.dart';
import '../../widgets/clinical_widgets.dart';

/// Validated intake form using every supported backend patient creation field.
class PatientFormScreen extends StatefulWidget {
  final Session session;
  const PatientFormScreen({super.key, required this.session});
  @override
  State<PatientFormScreen> createState() => _PatientFormScreenState();
}

class _PatientFormScreenState extends State<PatientFormScreen> {
  final _form = GlobalKey<FormState>();
  final _controllers = {
    for (final key in [
      'mrn',
      'full_name',
      'phone_number',
      'diabetes_duration_years',
      'latest_hba1c',
      'notes',
      'date_of_birth',
    ])
      key: TextEditingController(),
  };
  String _gender = 'female', _diabetes = 'type_2';
  bool _insulin = false, _busy = false;
  String? _error;
  @override
  void dispose() {
    for (final c in _controllers.values) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _birthDate() async {
    final date = await showDatePicker(
      context: context,
      initialDate: DateTime(1975),
      firstDate: DateTime(1850),
      lastDate: DateTime.now(),
    );
    if (date != null) {
      _controllers['date_of_birth']!.text = date.toIso8601String().substring(
        0,
        10,
      );
    }
  }

  Future<void> _submit() async {
    if (_busy || !_form.currentState!.validate()) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    final fields = <String, dynamic>{
      for (final e in _controllers.entries)
        e.key: e.value.text.trim().isEmpty ? null : e.value.text.trim(),
    };
    fields.addAll({
      'gender': _gender,
      'diabetes_type': _diabetes,
      'is_insulin_dependent': _insulin,
      'diabetes_duration_years': int.tryParse(
        _controllers['diabetes_duration_years']!.text,
      ),
      'latest_hba1c': double.tryParse(_controllers['latest_hba1c']!.text),
    });
    try {
      final patient = await widget.session.patients.create(fields);
      if (mounted) Navigator.of(context).pop(patient);
    } catch (e) {
      if (mounted) setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Widget _field(
    String key,
    String label, {
    int? maxLength,
    TextInputType? keyboard,
    String? Function(String?)? validate,
    bool readOnly = false,
    VoidCallback? onTap,
    int lines = 1,
  }) => Padding(
    padding: const EdgeInsets.only(bottom: 18),
    child: TextFormField(
      controller: _controllers[key],
      decoration: InputDecoration(labelText: label),
      maxLength: maxLength,
      keyboardType: keyboard,
      validator: validate,
      readOnly: readOnly,
      onTap: onTap,
      maxLines: lines,
    ),
  );
  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Register patient')),
    body: SafeArea(
      child: PageBody(
        children: [
          const SectionHeading(
            'Care starts here.',
            subtitle:
                'Enter the patient’s clinical details. Required fields are marked *.',
          ),
          Form(
            key: _form,
            child: Column(
              children: [
                _field(
                  'mrn',
                  'Medical record number *',
                  maxLength: 50,
                  validate: (v) =>
                      !RegExp(r'^[A-Za-z0-9_-]{3,50}$').hasMatch(v ?? '')
                      ? 'Use 3–50 letters, digits, hyphens or underscores.'
                      : null,
                ),
                _field(
                  'full_name',
                  'Full name *',
                  maxLength: 200,
                  validate: (v) => (v?.trim().length ?? 0) < 2
                      ? 'Enter at least two characters.'
                      : null,
                ),
                _field(
                  'date_of_birth',
                  'Date of birth *',
                  readOnly: true,
                  onTap: _birthDate,
                  validate: (v) =>
                      (v?.isEmpty ?? true) ? 'Choose date of birth.' : null,
                ),
                DropdownButtonFormField<String>(
                  initialValue: _gender,
                  decoration: const InputDecoration(labelText: 'Gender *'),
                  items: ['female', 'male', 'other']
                      .map((g) => DropdownMenuItem(value: g, child: Text(g)))
                      .toList(),
                  onChanged: (v) => setState(() => _gender = v!),
                ),
                const SizedBox(height: 18),
                _field(
                  'phone_number',
                  'Phone number',
                  maxLength: 20,
                  keyboard: TextInputType.phone,
                ),
                DropdownButtonFormField<String>(
                  initialValue: _diabetes,
                  decoration: const InputDecoration(
                    labelText: 'Diabetes type *',
                  ),
                  items: ['type_1', 'type_2', 'gestational', 'other']
                      .map(
                        (g) => DropdownMenuItem(
                          value: g,
                          child: Text(g.replaceAll('_', ' ')),
                        ),
                      )
                      .toList(),
                  onChanged: (v) => setState(() => _diabetes = v!),
                ),
                const SizedBox(height: 18),
                _field(
                  'diabetes_duration_years',
                  'Years since diagnosis',
                  keyboard: TextInputType.number,
                  validate: (v) => v == null || v.isEmpty
                      ? null
                      : int.tryParse(v) == null ||
                            int.parse(v) < 0 ||
                            int.parse(v) > 100
                      ? 'Enter a whole number from 0 to 100.'
                      : null,
                ),
                _field(
                  'latest_hba1c',
                  'Latest HbA1c (%)',
                  keyboard: const TextInputType.numberWithOptions(
                    decimal: true,
                  ),
                  validate: (v) {
                    if (v == null || v.isEmpty) return null;
                    final n = double.tryParse(v);
                    return n == null || !n.isFinite || n < 3 || n > 20
                        ? 'Enter a value from 3 to 20.'
                        : null;
                  },
                ),
                SwitchListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Insulin dependent'),
                  value: _insulin,
                  onChanged: (v) => setState(() => _insulin = v),
                ),
                _field('notes', 'Clinical notes', maxLength: 2000, lines: 4),
                ErrorNotice(_error),
                PrimaryAction(
                  'Register patient',
                  busy: _busy,
                  onPressed: _submit,
                ),
              ],
            ),
          ),
        ],
      ),
    ),
  );
}
