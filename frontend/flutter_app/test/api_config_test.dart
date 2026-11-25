import 'package:flutter/foundation.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:netrava/core/config/api_config.dart';

void main() {
  test('Android development uses the assigned HTTPS endpoint by default', () {
    debugDefaultTargetPlatformOverride = TargetPlatform.android;
    addTearDown(() => debugDefaultTargetPlatformOverride = null);

    const override = String.fromEnvironment('API_BASE_URL');
    expect(
      ApiConfig.validatedBaseUrl,
      override.isEmpty
          ? 'https://bouncing-unquote-lavender.ngrok-free.dev/api/v1'
          : override.replaceFirst(RegExp(r'/+$'), ''),
    );
  });
}
