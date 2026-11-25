import 'dart:convert';
import 'package:dio/dio.dart';
import '../config/api_config.dart';

/// Normalizes FastAPI's top-level, detail-object, and binary-response errors.
class ApiFailure implements Exception {
  final int? status;
  final String code, message;
  final Map<String, dynamic>? extra;
  const ApiFailure(
    this.message, {
    this.status,
    this.code = 'NETWORK_ERROR',
    this.extra,
  });
  factory ApiFailure.fromDio(DioException e) {
    dynamic data = e.response?.data;
    if (data is List<int>) {
      try {
        data = jsonDecode(utf8.decode(data));
      } catch (_) {
        data = null;
      }
    }
    if (data is Map && data['detail'] is Map) data = data['detail'];
    if (data is Map) {
      var message =
          data['message']?.toString() ?? 'The request could not be completed.';
      final details = data['details'];
      if (details is List && details.isNotEmpty) {
        message =
            '$message ${details.map((d) => '${(d['loc'] as List).skip(1).join('.')}: ${d['msg']}').join('; ')}';
      }
      return ApiFailure(
        message,
        status: e.response?.statusCode,
        code: data['error']?.toString() ?? 'API_ERROR',
        extra: Map<String, dynamic>.from(data),
      );
    }
    final timeout =
        e.type == DioExceptionType.receiveTimeout ||
        e.type == DioExceptionType.sendTimeout ||
        e.type == DioExceptionType.connectionTimeout;
    return ApiFailure(
      timeout
          ? 'The request timed out. Check the saved record before repeating an upload or review.'
          : 'Cannot reach NETRAVA. Check your connection and backend availability.',
      status: e.response?.statusCode,
    );
  }
  @override
  String toString() => message;
}

/// Single authenticated transport. Never logs credentials or retries writes.
class ApiClient {
  final Dio dio;
  String? token;
  void Function()? onUnauthorized;
  ApiClient({Dio? transport})
    : dio =
          transport ??
          Dio(
            BaseOptions(
              baseUrl: ApiConfig.validatedBaseUrl,
              connectTimeout: const Duration(seconds: 15),
              sendTimeout: const Duration(seconds: 90),
              receiveTimeout: const Duration(minutes: 3),
            ),
          ) {
    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) {
          if (token != null && options.extra['public'] != true) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          handler.next(options);
        },
        onError: (error, handler) {
          // A late response from a previous session must not log out a new user.
          if (error.response?.statusCode == 401 &&
              error.requestOptions.extra['public'] != true &&
              token != null &&
              error.requestOptions.headers['Authorization'] ==
                  'Bearer $token') {
            onUnauthorized?.call();
          }
          handler.next(error);
        },
      ),
    );
  }
  Future<T> execute<T>(Future<T> Function() work) async {
    try {
      return await work();
    } on DioException catch (e) {
      throw ApiFailure.fromDio(e);
    }
  }
}
