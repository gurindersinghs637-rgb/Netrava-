import 'package:flutter_test/flutter_test.dart';
import 'package:netrava/app/app.dart';
import 'support/fixture_api.dart';

void main() {
  testWidgets('NetravaApp smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(NetravaApp(session: FixtureApi().session()));
    await tester.pumpAndSettle();
    expect(find.text('NETRAVA'), findsWidgets);
  });
}
