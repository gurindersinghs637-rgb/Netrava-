import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:netrava/screens/auth/sign_up_screen.dart';
import 'support/fixture_api.dart';

void main() {
  testWidgets(
    'signup blocks invalid email and mismatched passwords before API',
    (tester) async {
      tester.view.physicalSize = const Size(800, 1200);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      final api = FixtureApi();
      final session = api.session();
      await tester.pumpWidget(
        MaterialApp(home: SignUpScreen(session: session)),
      );
      final fields = find.byType(TextFormField);
      await tester.enterText(fields.at(0), 'New Person');
      await tester.enterText(fields.at(1), 'invalid');
      await tester.enterText(fields.at(2), '+919876543210');
      await tester.enterText(fields.at(3), 'strong-password');
      await tester.enterText(fields.at(4), 'different-password');
      await tester.ensureVisible(find.text('Create account'));
      await tester.tap(find.text('Create account'));
      await tester.pumpAndSettle();
      expect(find.text('Enter a valid email address.'), findsOneWidget);
      expect(find.text('Passwords must match.'), findsOneWidget);
      expect(api.requests.where((r) => r.path == '/auth/signup'), isEmpty);
    },
  );
}
