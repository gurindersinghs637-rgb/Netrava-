import 'dart:typed_data';
import 'package:dio/dio.dart';
import '../core/network/api_client.dart';
import '../models/report.dart';

/// Clinical review and authenticated PDF download.
class ReportService {
  final ApiClient api;
  ReportService(this.api);
  String _path(String id) => '/screenings/${Uri.encodeComponent(id)}/report';
  Future<ClinicalReport> get(String id) => api.execute(
    () async => ClinicalReport.fromJson((await api.dio.get(_path(id))).data),
  );
  Future<ClinicalReport> save(String id, Map<String, dynamic> review) =>
      api.execute(
        () async => ClinicalReport.fromJson(
          (await api.dio.post(_path(id), data: review)).data,
        ),
      );
  Future<Uint8List> aiPdf(String id, {String? predictionId}) => api.execute(
    () async => Uint8List.fromList(
      (await api.dio.get<List<int>>(
        '/screenings/${Uri.encodeComponent(id)}/ai-report/pdf',
        queryParameters: {
          'prediction_id': ?predictionId,
        },
        options: Options(responseType: ResponseType.bytes),
      )).data!,
    ),
  );
  Future<Uint8List> pdf(String id) => api.execute(
    () async => Uint8List.fromList(
      (await api.dio.get<List<int>>(
        '${_path(id)}/pdf',
        options: Options(responseType: ResponseType.bytes),
      )).data!,
    ),
  );
}
