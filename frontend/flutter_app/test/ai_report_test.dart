import 'dart:async';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:netrava/screens/reports/ai_report_screen.dart';
import 'package:netrava/services/pdf_files.dart';
import 'support/fixture_api.dart';

class RecordingPdfFiles extends PdfFiles {
  final opened = <Uint8List>[];
  @override
  Future<String> saveAndOpen(String id, Uint8List bytes) async {
    opened.add(bytes);
    return 'Report downloaded and opened.';
  }
}

void main() {
  testWidgets(
    'technician generates AI PDF and sees view and download actions',
    (tester) async {
      final fixture = FixtureApi();
      final session = fixture.session();
      final files = RecordingPdfFiles();
      await tester.runAsync(
        () => session.login('staff@example.com', 'password123'),
      );
      await tester.pumpWidget(
        MaterialApp(
          home: AiReportScreen(
            session: session,
            screeningId: screeningId,
            predictionId: predictionId,
            files: files,
          ),
        ),
      );
      expect(find.text('View Report'), findsNothing);
      await tester.runAsync(() async {
        await tester.tap(find.text('Generate Report'));
        await Future<void>.delayed(const Duration(milliseconds: 100));
      });
      await tester.pumpAndSettle();
      expect(find.text('AI Screening Report Ready'), findsOneWidget);
      expect(find.text('View Report'), findsOneWidget);
      expect(find.text('Download/Open Report'), findsOneWidget);
      final request = fixture.requests.last;
      expect(request.path, '/screenings/$screeningId/ai-report/pdf');
      expect(request.headers['Authorization'], 'Bearer fixture-token');
      expect(request.queryParameters['prediction_id'], predictionId);
      expect(fixture.report, isNull);
      final count = fixture.requests.length;
      for (final label in ['View Report', 'Download/Open Report']) {
        await tester.ensureVisible(find.text(label));
        await tester.runAsync(() async {
          await tester.tap(find.text(label));
          await Future<void>.delayed(const Duration(milliseconds: 100));
        });
        await tester.pumpAndSettle();
      }
      expect(files.opened.length, 2);
      expect(String.fromCharCodes(files.opened.first), startsWith('%PDF-'));
      expect(fixture.requests.length, count);
    },
  );

  testWidgets('PDF failure is shown with a retry action', (tester) async {
    final fixture = FixtureApi();
    final session = fixture.session();
    await tester.runAsync(
      () => session.login('staff@example.com', 'password123'),
    );
    fixture.failureStatus = 409;
    fixture.failureBody = {
      'detail': {
        'error': 'PREDICTION_REQUIRED',
        'message': 'A saved prediction is required.',
      },
    };
    await tester.pumpWidget(
      MaterialApp(
        home: AiReportScreen(
          session: session,
          screeningId: screeningId,
          predictionId: predictionId,
        ),
      ),
    );
    await tester.runAsync(() async {
      await tester.tap(find.text('Generate Report'));
      await Future<void>.delayed(const Duration(milliseconds: 100));
    });
    await tester.pumpAndSettle();
    expect(find.text('A saved prediction is required.'), findsOneWidget);
    expect(find.text('View Report'), findsNothing);
    expect(find.text('Generate Report'), findsOneWidget);
  });
  testWidgets('generation shows progress and disables repeated requests', (
    tester,
  ) async {
    final fixture = FixtureApi();
    final session = fixture.session();
    await tester.runAsync(
      () => session.login('staff@example.com', 'password123'),
    );
    final gate = Completer<void>();
    fixture.responseGate = gate.future;
    await tester.pumpWidget(
      MaterialApp(
        home: AiReportScreen(
          session: session,
          screeningId: screeningId,
          predictionId: predictionId,
        ),
      ),
    );
    await tester.tap(find.text('Generate Report'));
    await tester.pump();
    expect(find.byType(CircularProgressIndicator), findsOneWidget);
    expect(find.text('Generating your AI Screening Report...'), findsOneWidget);
    expect(
      tester.widget<FilledButton>(find.byType(FilledButton)).onPressed,
      isNull,
    );
    gate.complete();
    await tester.pumpAndSettle();
    expect(find.text('View Report'), findsOneWidget);
  });
}
