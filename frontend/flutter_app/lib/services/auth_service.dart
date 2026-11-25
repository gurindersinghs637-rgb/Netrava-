import 'package:dio/dio.dart';
import '../core/network/api_client.dart';
import '../models/user.dart';

/// Email/password login and trusted profile retrieval.
class AuthService {
  final ApiClient api;
  AuthService(this.api);
  Future<Map<String, dynamic>> login(String email, String password) =>
      api.execute(
        () async => Map<String, dynamic>.from(
          (await api.dio.post(
            '/auth/login',
            data: {'email': email, 'password': password},
            options: Options(extra: {'public': true}),
          )).data,
        ),
      );
  Future<String> signup(
    String name,
    String email,
    String phone,
    String password,
    String confirmation,
  ) => api.execute(() async {
    final response = await api.dio.post(
      '/auth/signup',
      data: {
        'full_name': name,
        'email': email,
        'phone': phone,
        'password': password,
        'confirm_password': confirmation,
      },
      options: Options(extra: {'public': true}),
    );
    return response.data['message'] as String;
  });
  Future<String> forgotPassword(String email) => api.execute(() async {
    final response = await api.dio.post(
      '/auth/forgot-password',
      data: {'email': email},
      options: Options(extra: {'public': true}),
    );
    return response.data['message'] as String;
  });
  Future<UserProfile> me() => api.execute(
    () async => UserProfile.fromJson((await api.dio.get('/auth/me')).data),
  );
}
