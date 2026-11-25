import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';
import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:image_picker_platform_interface/image_picker_platform_interface.dart';
import 'package:netrava/core/network/api_client.dart';
import 'package:netrava/providers/session.dart';

const screeningId = '00000000-0000-4000-8000-000000000001';
const imageId = '00000000-0000-4000-8000-000000000002';
const patientId = '00000000-0000-4000-8000-000000000003';
const predictionId = '00000000-0000-4000-8000-000000000004';
const timestamp = '2026-11-14T00:00:00Z';
final fixturePng = base64Decode(
  'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAIAAACQkWg2AAAAI0lEQVR4nGOUSwlgIAUwkaSaYVQDcYCJSHVwMKqBGEByKAEAtXgA8mbl/agAAAAASUVORK5CYII=',
);

/// Test-only image picker; production always uses the actual platform picker.
class FixturePicker extends ImagePickerPlatform {
  @override
  Future<XFile?> getImageFromSource({
    required ImageSource source,
    ImagePickerOptions options = const ImagePickerOptions(),
  }) async =>
      XFile.fromData(fixturePng, name: 'fixture.png', mimeType: 'image/png');
}

/// Deterministic HTTP fixture. It is never imported by the application.
class FixtureApi implements HttpClientAdapter {
  final String role;
  final requests = <RequestOptions>[];
  final bodies = <String, List<int>>{};
  Map<String, dynamic>? report;
  Future<void>? responseGate;
  int? failureStatus;
  Map<String, dynamic>? failureBody;
  FixtureApi({this.role = 'technician'});
  Map<String, dynamic> get user => {
    'id': 'staff-id',
    'email': 'staff@example.com',
    'full_name': 'Demo Clinician',
    'role': role,
    'clinic_name': 'Test Clinic',
    'created_at': null,
  };
  Map<String, dynamic> get patient => {
    'id': patientId,
    'patient_code': 'TEST-001',
    'full_name': 'Synthetic Patient',
    'date_of_birth': '1975-06-15',
    'sex': 'female',
    'clinic_id': 'clinic-id',
    'diabetes_type': 'type_2',
    'is_insulin_dependent': false,
  };
  Map<String, dynamic> get prediction => {
    'prediction_id': predictionId,
    'retinal_image_id': imageId,
    'predicted_grade': 2,
    'severity_label': 'Moderate',
    'confidence_score': 0.8,
    'is_referral_recommended': true,
    'probabilities': [
      for (var i = 0; i < 5; i++)
        {
          'grade': i,
          'class_name': [
            'No DR',
            'Mild',
            'Moderate',
            'Severe',
            'Proliferative DR',
          ][i],
          'probability': i == 2 ? 0.8 : 0.05,
        },
    ],
    'explanation': {
      'target_layer': 'conv_head',
      'heatmap_signed_url': null,
      'heatmap_base64': base64Encode(fixturePng),
    },
    'inference_time_ms': 125.0,
    'persistence_status': 'persisted',
  };
  Session session() {
    FlutterSecureStorage.setMockInitialValues({});
    final dio = Dio(BaseOptions(baseUrl: 'https://fixture.invalid/api/v1'));
    dio.httpClientAdapter = this;
    return Session(
      client: ApiClient(transport: dio),
      clearFiles: () async {},
    );
  }

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    requests.add(options);
    if (responseGate != null) await responseGate;
    if (requestStream != null) {
      bodies[options.path] = await requestStream
          .expand((chunk) => chunk)
          .toList();
    }
    if (failureStatus != null) {
      return _json(
        failureBody ??
            {
              'detail': {
                'error': 'INVALID_TOKEN',
                'message': 'Session expired.',
              },
            },
        failureStatus!,
      );
    }
    switch (options.path) {
      case '/auth/forgot-password':
        return _json({'message': 'If an account exists for this email, you will receive a password reset link.'});
      case '/health':
        return _json({
          'status': 'healthy',
          'model_loaded': true,
          'database_connected': true,
        });
      case '/auth/login':
        return _json({
          'access_token': 'fixture-token',
          'token_type': 'bearer',
          'expires_in': 3600,
          'user': user,
        });
      case '/auth/me':
        return _json(user);
      case '/patients':
        if (options.method == 'POST') {
          return _json({
            ...patient,
            'mrn': 'TEST-001',
            'registered_by': 'staff-id',
            'created_at': timestamp,
          }, 201);
        }
        return _json({
          'total': 1,
          'page': 1,
          'limit': 20,
          'patients': [patient],
        });
      case '/patients/$patientId':
        return _json(patient);
      case '/screenings':
        return _json({
          'screening_id': screeningId,
          'retinal_image_id': imageId,
          'eye': 'OD',
          'qc_assessment': {
            'is_gradable': true,
            'blur_score': 150.0,
            'illumination': 'optimal',
            'confidence': 0.875,
          },
          'fundus_image_signed_url': 'https://fixture.invalid/image',
          'created_at': timestamp,
        }, 201);
      case '/predict':
        return _json(prediction);
      case '/screenings/$screeningId/report':
        if (options.method == 'POST') {
          final data = Map<String, dynamic>.from(options.data);
          report = {
            ...data,
            'id': 'report-id',
            'screening_id': screeningId,
            'prediction_id': predictionId,
            'signed_off_at': data['is_signed_off'] == true ? timestamp : null,
            'created_at': timestamp,
            'updated_at': timestamp,
          };
        }
        return report == null
            ? _json({
                'detail': {
                  'error': 'REPORT_NOT_FOUND',
                  'message': 'Clinical report was not found.',
                },
              }, 404)
            : _json(report!);
      case '/screenings/$screeningId/ai-report/pdf':
      case '/screenings/$screeningId/report/pdf':
        return ResponseBody.fromBytes(
          utf8.encode('%PDF-1.4\nfixture'),
          200,
          headers: {
            Headers.contentTypeHeader: ['application/pdf'],
          },
        );
      default:
        return _json({'detail': 'Not Found'}, 404);
    }
  }

  ResponseBody _json(Map<String, dynamic> data, [int status = 200]) =>
      ResponseBody.fromString(
        jsonEncode(data),
        status,
        headers: {
          Headers.contentTypeHeader: ['application/json'],
        },
      );
  @override
  void close({bool force = false}) {}
}
