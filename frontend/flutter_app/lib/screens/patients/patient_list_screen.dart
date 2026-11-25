import 'dart:async';
import 'package:flutter/material.dart';
import '../../models/patient.dart';
import '../../providers/session.dart';
import '../../widgets/clinical_widgets.dart';
import '../screening/screening_screen.dart';
import 'patient_form_screen.dart';
import 'patient_detail_screen.dart';

/// Searchable, paginated clinic patient registry and screening patient selector.
class PatientListScreen extends StatefulWidget {
  final Session session;
  final bool selecting;
  const PatientListScreen({
    super.key,
    required this.session,
    this.selecting = false,
  });
  @override
  State<PatientListScreen> createState() => _PatientListScreenState();
}

class _PatientListScreenState extends State<PatientListScreen> {
  final _search = TextEditingController();
  Timer? _debounce;
  PatientPage? _data;
  bool _loading = true;
  String? _error;
  int _page = 1, _request = 0;
  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _debounce?.cancel();
    _search.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    final request = ++_request;
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final page = await widget.session.patients.list(
        search: _search.text,
        page: _page,
      );
      if (mounted && request == _request) setState(() => _data = page);
    } catch (e) {
      if (mounted && request == _request) setState(() => _error = e.toString());
    } finally {
      if (mounted && request == _request) setState(() => _loading = false);
    }
  }

  Future<void> _add() async {
    final patient = await Navigator.of(context).push<Patient>(
      MaterialPageRoute(
        builder: (_) => PatientFormScreen(session: widget.session),
      ),
    );
    if (!mounted || patient == null) return;
    _page = 1;
    _search.clear();
    _load();
    _open(patient);
  }

  void _open(Patient patient) => Navigator.of(context).push(
    MaterialPageRoute(
      builder: (_) => widget.selecting
          ? ScreeningScreen(session: widget.session, patient: patient)
          : PatientDetailScreen(session: widget.session, patientId: patient.id),
    ),
  );
  @override
  Widget build(BuildContext context) => RefreshIndicator(
    onRefresh: _load,
    child: PageBody(
      children: [
        SectionHeading(
          widget.selecting ? 'Who are we screening?' : 'Your patients',
          subtitle: 'Search your clinic registry or register a new patient.',
        ),
        PrimaryAction(
          'Register patient',
          icon: Icons.person_add_alt_1,
          onPressed: _add,
        ),
        const SizedBox(height: 20),
        TextField(
          controller: _search,
          decoration: const InputDecoration(
            hintText: 'Search name or patient code',
            prefixIcon: Icon(Icons.search),
          ),
          onChanged: (_) {
            _debounce?.cancel();
            ++_request;
            _debounce = Timer(const Duration(milliseconds: 350), () {
              _page = 1;
              _load();
            });
          },
        ),
        const SizedBox(height: 20),
        ErrorNotice(_error),
        if (_error != null)
          TextButton(onPressed: _load, child: const Text('Retry')),
        if (_loading) const Center(child: CircularProgressIndicator()),
        if (!_loading && _error == null && _data != null) ...[
          Text('${_data!.total} patients'),
          const SizedBox(height: 12),
          if (_data!.patients.isEmpty)
            const ClinicalCard(
              child: Text(
                'No patients found. Try another search or register a patient.',
              ),
            ),
          for (final p in _data!.patients)
            ClinicalCard(
              child: ListTile(
                contentPadding: EdgeInsets.zero,
                leading: const CircleAvatar(child: Icon(Icons.person_outline)),
                title: Text(p.name),
                subtitle: Text(p.code),
                trailing: const Icon(Icons.chevron_right),
                onTap: () => _open(p),
              ),
            ),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              IconButton(
                tooltip: 'Previous page',
                onPressed: _page > 1
                    ? () {
                        _page--;
                        _load();
                      }
                    : null,
                icon: const Icon(Icons.chevron_left),
              ),
              Text('Page $_page'),
              IconButton(
                tooltip: 'Next page',
                onPressed: _page * _data!.limit < _data!.total
                    ? () {
                        _page++;
                        _load();
                      }
                    : null,
                icon: const Icon(Icons.chevron_right),
              ),
            ],
          ),
        ],
      ],
    ),
  );
}
