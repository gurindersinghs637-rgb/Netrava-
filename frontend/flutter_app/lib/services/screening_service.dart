import 'package:dio/dio.dart';
import '../core/network/api_client.dart';
import '../models/screening.dart';

/// Upload original image bytes and run server quality control.
class ScreeningService {
  final ApiClient api;
  ScreeningService(this.api);
  Future<Screening> create(
    String patientId,
    String eye,
    RetinalUpload image, {
    ProgressCallback? onSendProgress,
  }) => api.execute(
    () async => Screening.fromJson(
      (await api.dio.post(
        '/screenings',
        data: FormData.fromMap({
          'patient_id': patientId,
          'eye': eye,
          'image': image.toMultipart(),
        }),
        onSendProgress: onSendProgress,
      )).data,
    ),
  );
}
