import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../utils/constants.dart';

class ApiService {
  final Dio _dio = Dio(BaseOptions(baseUrl: ApiConstants.baseUrl));
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  ApiService() {
    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          final token = await _storage.read(key: 'auth_token');
          if (token != null) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          return handler.next(options);
        },
      ),
    );
  }

  Future<String?> login(String username, String password) async {
    try {
      final response = await _dio.post(
        ApiConstants.loginEndpoint,
        data: {'username': username, 'password': password},
        options: Options(contentType: Headers.formUrlEncodedContentType),
      );
      final token = response.data['access_token'];
      await _storage.write(key: 'auth_token', value: token);
      return token;
    } catch (e) {
      throw Exception('Failed to login: $e');
    }
  }

  Future<void> register(String email, String password, String fullName) async {
    try {
      await _dio.post(
        ApiConstants.registerEndpoint,
        data: {
          'email': email,
          'password': password,
          'full_name': fullName,
          'role': 'user',
        },
      );
    } catch (e) {
      throw Exception('Failed to register: $e');
    }
  }

  Future<dynamic> getUserInfo() async {
    try {
      final response = await _dio.get(ApiConstants.userInfoEndpoint);
      return response.data;
    } catch (e) {
      throw Exception('Failed to get user info: $e');
    }
  }

  Future<void> logout() async {
    await _storage.delete(key: 'auth_token');
  }
}
