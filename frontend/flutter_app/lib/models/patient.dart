/// Patient read model, including the backend's intake-to-detail field aliases.
class Patient {
  final String id, code, name;
  final Map<String, dynamic> details;
  const Patient({
    required this.id,
    required this.code,
    required this.name,
    this.details = const {},
  });
  factory Patient.fromJson(Map<String, dynamic> j) => Patient(
    id: j['id'],
    code: j['patient_code'] ?? j['mrn'],
    name: j['full_name'],
    details: j,
  );
}

/// One page of clinic-scoped patients.
class PatientPage {
  final int total, page, limit;
  final List<Patient> patients;
  PatientPage.fromJson(Map<String, dynamic> j)
    : total = j['total'],
      page = j['page'],
      limit = j['limit'],
      patients = (j['patients'] as List)
          .map((p) => Patient.fromJson(p))
          .toList();
}
