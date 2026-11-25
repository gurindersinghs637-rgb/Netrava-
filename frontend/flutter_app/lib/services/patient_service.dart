import '../core/network/api_client.dart';
import '../models/patient.dart';

/// Clinic-scoped patient API; input field names follow the backend schema.
class PatientService {
  final ApiClient api;
  PatientService(this.api);
  Future<PatientPage> list({String search = '', int page = 1}) => api.execute(
    () async => PatientPage.fromJson(
      (await api.dio.get(
        '/patients',
        queryParameters: {'search': search, 'page': page, 'limit': 20},
      )).data,
    ),
  );
  Future<Patient> get(String id) => api.execute(
    () async => Patient.fromJson(
      (await api.dio.get('/patients/${Uri.encodeComponent(id)}')).data,
    ),
  );
  Future<Patient> create(Map<String, dynamic> fields) => api.execute(
    () async =>
        Patient.fromJson((await api.dio.post('/patients', data: fields)).data),
  );
}
