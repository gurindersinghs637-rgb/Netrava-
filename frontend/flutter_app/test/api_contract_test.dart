import 'dart:convert';
import 'dart:typed_data';
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:netrava/core/network/api_client.dart';
import 'package:netrava/models/screening.dart';
import 'support/fixture_api.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  test(
    'login securely persists token; restore verifies profile; logout clears state',
    () async {
      final fixture = FixtureApi();
      final session = fixture.session();
      await session.login('staff@example.com', 'password123');
      expect(session.api.token, 'fixture-token');
      await session.restore();
      expect(session.user!.role, 'technician');
      expect(
        fixture.requests.last.headers['Authorization'],
        'Bearer fixture-token',
      );
      session.remember(screeningId);
      await session.logout();
      expect(session.api.token, isNull);
      expect(session.user, isNull);
      expect(session.recentScreenings, isEmpty);
      await session.restore();
      expect(session.user, isNull);
    },
  );
  test(
    'upload and predict use exact original bytes and correct multipart/query IDs',
    () async {
      final fixture = FixtureApi();
      final session = fixture.session();
      session.api.token = 'test';
      final upload = RetinalUpload(bytes: fixturePng, filename: 'fixture.png');
      final screening = await session.screenings.create(
        patientId,
        'OD',
        upload,
      );
      final result = await session.predictions.predict(
        screening.imageId,
        upload,
      );
      expect(result.grade, 2);
      expect(result.referral, isTrue);
      final create = fixture.requests.first;
      expect(
        Map.fromEntries((create.data as FormData).fields)['patient_id'],
        patientId,
      );
      expect(fixture.requests.last.queryParameters, {
        'retinal_image_id': imageId,
      });
      expect((fixture.requests.last.data as FormData).fields, isEmpty);
      for (final body in fixture.bodies.values) {
        expect(_containsBytes(body, fixturePng), isTrue);
      }
    },
  );
  test('normalizes nested, top-level and binary PDF errors', () async {
    final fixture = FixtureApi();
    final session = fixture.session();
    fixture.failureStatus = 422;
    fixture.failureBody = {
      'error': 'VALIDATION_ERROR',
      'message': 'Invalid field.',
      'details': [
        {
          'loc': ['body', 'mrn'],
          'msg': 'Required',
        },
      ],
    };
    await expectLater(
      session.patients.list(),
      throwsA(
        isA<ApiFailure>().having((e) => e.message, 'field', contains('mrn')),
      ),
    );
    fixture.failureStatus = 409;
    fixture.failureBody = {
      'detail': {
        'error': 'INVALID_STATE',
        'message': 'Signed report is immutable.',
      },
    };
    await expectLater(
      session.reports.pdf(screeningId),
      throwsA(isA<ApiFailure>().having((e) => e.code, 'code', 'INVALID_STATE')),
    );
  });
  test(
    '401 clears session; public invalid-credential errors do not recurse',
    () async {
      final fixture = FixtureApi();
      final session = fixture.session();
      await session.login('staff@example.com', 'password123');
      fixture.failureStatus = 401;
      await expectLater(session.auth.me(), throwsA(isA<ApiFailure>()));
      expect(session.user, isNull);
      expect(session.api.token, isNull);
      await expectLater(
        session.login('staff@example.com', 'password123'),
        throwsA(isA<ApiFailure>()),
      );
    },
  );
  test(
    'patient aliases and review fields roundtrip; PDF remains binary',
    () async {
      final fixture = FixtureApi(role: 'ophthalmologist');
      final session = fixture.session();
      final patient = await session.patients.create({'mrn': 'TEST-001'});
      expect(patient.code, 'TEST-001');
      final report = await session.reports.save(screeningId, {
        'overall_grade': 2,
        'grade_override': 3,
        'ophthalmologist_notes': 'Synthetic review',
        'is_urgent_referral': true,
        'is_signed_off': false,
      });
      expect(report.override, 3);
      expect(
        (await session.reports.get(screeningId)).notes,
        'Synthetic review',
      );
      expect(
        utf8.decode(await session.reports.pdf(screeningId)),
        startsWith('%PDF-'),
      );
    },
  );
  test('rejects unsupported and oversized images before upload', () {
    expect(
      RetinalUpload(
        bytes: Uint8List.fromList([1, 2, 3]),
        filename: 'x.jpg',
      ).validate(),
      isNotNull,
    );
    expect(
      RetinalUpload(
        bytes: Uint8List(15 * 1024 * 1024 + 1),
        filename: 'x.png',
      ).validate(),
      contains('15 MiB'),
    );
    expect(
      RetinalUpload(bytes: fixturePng, filename: 'x.png').validate(),
      isNull,
    );
  });
}

bool _containsBytes(List<int> data, List<int> match) {
  for (var i = 0; i <= data.length - match.length; i++) {
    var same = true;
    for (var j = 0; j < match.length; j++) {
      if (data[i + j] != match[j]) {
        same = false;
        break;
      }
    }
    if (same) return true;
  }
  return false;
}
