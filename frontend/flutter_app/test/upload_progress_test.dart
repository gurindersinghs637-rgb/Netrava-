import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:image_picker_platform_interface/image_picker_platform_interface.dart';
import 'package:netrava/core/theme/app_theme.dart';
import 'package:netrava/models/patient.dart';
import 'package:netrava/screens/screening/screening_screen.dart';
import 'support/fixture_api.dart';

void main() {
  testWidgets(
    'slow upload shows progress, blocks repeats and clears on failure',
    (tester) async {
      tester.view.physicalSize = const Size(440, 1400);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      final originalPicker = ImagePickerPlatform.instance;
      ImagePickerPlatform.instance = FixturePicker();
      addTearDown(() => ImagePickerPlatform.instance = originalPicker);
      final fixture = FixtureApi();
      final gate = Completer<void>();
      fixture.responseGate = gate.future;
      fixture.failureStatus = 503;
      fixture.failureBody = {
        'detail': {
          'error': 'STORAGE_ERROR',
          'message': 'Could not upload retinal image.',
        },
      };
      await tester.pumpWidget(
        MaterialApp(
          theme: AppTheme.lightTheme,
          home: ScreeningScreen(
            session: fixture.session(),
            patient: Patient.fromJson(fixture.patient),
          ),
        ),
      );
      await tester.tap(find.text('Import from gallery'));
      await tester.pumpAndSettle();
      await tester.ensureVisible(find.text('Upload & check quality'));
      await tester.tap(find.text('Upload & check quality'));
      await tester.pump(const Duration(milliseconds: 100));
      expect(find.text('Uploading image: 0%'), findsOneWidget);
      final request = fixture.requests.single;
      request.onSendProgress!(50, 100);
      await tester.pump();
      expect(find.text('Uploading image: 50%'), findsOneWidget);
      request.onSendProgress!(100, 100);
      await tester.pump();
      expect(
        find.textContaining('Upload sent. Checking image quality'),
        findsOneWidget,
      );
      final uploadButton = tester.widget<FilledButton>(
        find.widgetWithText(FilledButton, 'Upload & check quality'),
      );
      expect(uploadButton.onPressed, isNull);
      expect(fixture.requests.length, 1);
      gate.complete();
      await tester.pumpAndSettle();
      expect(find.textContaining('Upload sent.'), findsNothing);
      expect(find.byType(LinearProgressIndicator), findsNothing);
      expect(find.text('Could not upload retinal image.'), findsOneWidget);
      expect(
        tester
            .widget<FilledButton>(
              find.widgetWithText(FilledButton, 'Upload & check quality'),
            )
            .onPressed,
        isNotNull,
      );
      expect(tester.takeException(), isNull);
    },
  );
}
