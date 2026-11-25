import 'package:flutter/foundation.dart';

/// Central API configuration for local and tunneled development.
abstract final class ApiConfig {
  static const _configuredUrl = String.fromEnvironment('API_BASE_URL');

  static String get baseUrl {
    if (_configuredUrl.isNotEmpty) return _configuredUrl;
    if (kReleaseMode) return 'https://configure-backend.invalid/api/v1';
    if (!kIsWeb && defaultTargetPlatform == TargetPlatform.android) {
      return 'https://bouncing-unquote-lavender.ngrok-free.dev/api/v1';
    }
    return 'http://10.0.2.2:8000/api/v1';
  }

  static String get validatedBaseUrl {
    final uri = Uri.tryParse(baseUrl);
    if (uri == null ||
        !uri.hasAuthority ||
        (uri.scheme != 'https' && (kReleaseMode || uri.scheme != 'http'))) {
      throw StateError(
        'Configure a valid API_BASE_URL. Release builds require HTTPS.',
      );
    }
    return baseUrl.replaceFirst(RegExp(r'/+$'), '');
  }
}
