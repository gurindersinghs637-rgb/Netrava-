import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:netrava/screens/auth/forgot_password_screen.dart';
import 'support/fixture_api.dart';

void main() {
  testWidgets('recovery validates email and sends only email with public transport', (tester) async {
    final fixture = FixtureApi();
    final session = fixture.session();
    await tester.pumpWidget(MaterialApp(home: ForgotPasswordScreen(session: session)));
    await tester.enterText(find.byType(TextFormField), 'invalid');
    await tester.tap(find.text('Send reset email'));
    await tester.pumpAndSettle();
    expect(find.text('Enter a valid email address.'), findsOneWidget);
    expect(fixture.requests, isEmpty);
    await tester.enterText(find.byType(TextFormField), 'person@example.com');
    await tester.tap(find.text('Send reset email'));
    await tester.pumpAndSettle();
    expect(fixture.requests.single.path, '/auth/forgot-password');
    expect(fixture.requests.single.data, {'email': 'person@example.com'});
    expect(fixture.requests.single.extra['public'], true);
    expect(find.textContaining('If an account exists'), findsOneWidget);
    expect(session.user, isNull);
  });
}
