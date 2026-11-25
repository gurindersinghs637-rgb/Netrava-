import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:netrava/app/app.dart';
import 'package:netrava/core/network/api_client.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();
  testWidgets(
    'Pixel emulator starts real app, validates login, reaches backend health',
    (tester) async {
      final api = ApiClient();
      final response = await api.execute(() => api.dio.get('/health'));
      expect(response.statusCode, 200);
      expect(response.data['model_loaded'], isA<bool>());
      await tester.pumpWidget(const NetravaApp());
      await tester.pumpAndSettle();
      expect(find.text('NETRAVA'), findsOneWidget);
      await tester.ensureVisible(find.text('Log in'));
      await tester.tap(find.text('Log in'));
      await tester.pumpAndSettle();
      expect(find.text('Enter a valid email address.'), findsOneWidget);
      expect(find.text('Use at least 8 characters.'), findsOneWidget);
      expect(tester.takeException(), isNull);
      api.dio.close();
    },
  );
}
