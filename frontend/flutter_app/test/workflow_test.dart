import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:image_picker_platform_interface/image_picker_platform_interface.dart';
import 'package:netrava/app/app.dart';
import 'package:netrava/core/theme/app_theme.dart';
import 'package:netrava/models/prediction.dart';
import 'package:netrava/screens/reports/report_screen.dart';
import 'support/fixture_api.dart';

void main() {
  testWidgets(
    'technician: login → patient → upload/QC → prediction → report → logout',
    (tester) async {
      tester.view.physicalSize = const Size(440, 1200);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      final originalPicker = ImagePickerPlatform.instance;
      ImagePickerPlatform.instance = FixturePicker();
      addTearDown(() => ImagePickerPlatform.instance = originalPicker);
      final fixture = FixtureApi();
      final session = fixture.session();
      await tester.pumpWidget(NetravaApp(session: session));
      await tester.pumpAndSettle();
      await tester.enterText(
        find.byType(TextFormField).at(0),
        'staff@example.com',
      );
      await tester.enterText(find.byType(TextFormField).at(1), 'password123');
      await tester.tap(find.text('Log in'));
      await tester.pumpAndSettle();
      expect(find.text('Hello, Demo.'), findsOneWidget);
      await tester.tap(find.byIcon(Icons.description_outlined).last);
      await tester.pumpAndSettle();
      expect(find.text('AI screening reports'), findsOneWidget);
      expect(find.text('Clinical reports'), findsNothing);
      await tester.tap(find.byIcon(Icons.home_outlined));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Start a new screening'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Synthetic Patient'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Import from gallery'));
      await tester.pumpAndSettle();
      await tester.ensureVisible(find.text('Upload & check quality'));
      await tester.tap(find.text('Upload & check quality'));
      await tester.pumpAndSettle();
      expect(find.text('Image quality passed'), findsOneWidget);
      await tester.ensureVisible(find.text('Continue to AI analysis'));
      await tester.tap(find.text('Continue to AI analysis'));
      await tester.pumpAndSettle();
      expect(find.text('Grade 2 · Moderate'), findsOneWidget);
      await tester.scrollUntilVisible(
        find.text('Generate AI Screening Report'),
        300,
        scrollable: find.byType(Scrollable).first,
      );
      await tester.ensureVisible(find.text('Generate AI Screening Report'));
      await tester.tap(find.text('Generate AI Screening Report'));
      await tester.pumpAndSettle();

      expect(find.text('View Report'), findsOneWidget);
      expect(find.text('Download/Open Report'), findsOneWidget);
      expect(find.text('Save review draft'), findsNothing);
      expect(find.text('Review & create report'), findsNothing);
      expect(find.text('View clinical report'), findsNothing);
      final pdfRequest = fixture.requests.last;
      expect(pdfRequest.path, '/screenings/$screeningId/ai-report/pdf');
      expect(pdfRequest.queryParameters['prediction_id'], predictionId);
      expect(fixture.requests.any((r) => r.path.endsWith('/report')), isFalse);
      expect(fixture.requests.where((r) => r.path == '/predict').length, 1);
      expect(session.recentAiReports.single.patientName, 'Synthetic Patient');
      expect(session.recentAiReports.single.predictionId, predictionId);
      await session.logout();
      await tester.pumpAndSettle();
      expect(find.text('Log in'), findsOneWidget);
      expect(session.recentScreenings, isEmpty);
      expect(session.recentAiReports, isEmpty);
      expect(tester.takeException(), isNull);
    },
  );
  testWidgets(
    'clinician: draft roundtrip, sign-off confirmation and locked editor',
    (tester) async {
      tester.view.physicalSize = const Size(440, 1800);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      final fixture = FixtureApi(role: 'ophthalmologist');
      final session = fixture.session();
      await tester.runAsync(
        () => session.login('staff@example.com', 'password123'),
      );
      await tester.pumpWidget(
        MaterialApp(
          theme: AppTheme.lightTheme,
          home: Scaffold(
            body: ReportScreen(
              session: session,
              screeningId: screeningId,
              prediction: Prediction.fromJson(fixture.prediction),
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();
      await tester.enterText(
        find.byType(TextField).last,
        'Synthetic clinician review',
      );
      await tester.ensureVisible(find.text('Save review draft'));
      await tester.tap(find.text('Save review draft'));
      await tester.pumpAndSettle();
      expect(
        fixture.report!['ophthalmologist_notes'],
        'Synthetic clinician review',
      );
      expect(fixture.report!['is_signed_off'], false);
      await tester.ensureVisible(find.text('Sign off report'));
      await tester.tap(find.text('Sign off report'));
      await tester.pumpAndSettle();
      expect(find.text('Sign off this report?'), findsOneWidget);
      await tester.tap(find.text('Sign off'));
      await tester.pumpAndSettle();
      expect(fixture.report!['is_signed_off'], true);
      expect(find.text('Save review draft'), findsNothing);
      await tester.ensureVisible(find.text('Download & open PDF'));
      expect(find.text('Download & open PDF'), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );
}
