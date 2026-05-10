import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'app_exception.dart';

class ApiClient {
  static final ApiClient _instance = ApiClient._internal();
  factory ApiClient() => _instance;

  late final Dio _dio;
  final _authExpiredController = StreamController<void>.broadcast();

  Stream<void> get onAuthExpired => _authExpiredController.stream;

  static const _accessTokenKey = 'access_token';
  static const _refreshTokenKey = 'refresh_token';

  ApiClient._internal() {
    final baseUrl = kIsWeb
        ? 'http://localhost:8000/api/v1'
        : 'http://10.28.145.41:8000/api/v1';

    _dio = Dio(BaseOptions(
      baseUrl: baseUrl,
      connectTimeout: const Duration(seconds: 30),
      receiveTimeout: const Duration(seconds: 60),
      headers: {'Content-Type': 'application/json'},
    ));

    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final prefs = await SharedPreferences.getInstance();
        final token = prefs.getString(_accessTokenKey);
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        handler.next(options);
      },
      onError: (error, handler) async {
        if (error.response?.statusCode == 401) {
          final refreshed = await _attemptTokenRefresh();
          if (refreshed) {
            // Retry the original request with new token
            final prefs = await SharedPreferences.getInstance();
            final newToken = prefs.getString(_accessTokenKey);
            final opts = error.requestOptions;
            opts.headers['Authorization'] = 'Bearer $newToken';
            try {
              final response = await _dio.fetch(opts);
              return handler.resolve(response);
            } on DioException catch (e) {
              return handler.reject(e);
            }
          } else {
            _authExpiredController.add(null);
          }
        }
        handler.next(error);
      },
    ));
  }

  /// Configure a custom base URL (useful for tests or non-default hosts).
  void setBaseUrl(String url) {
    _dio.options.baseUrl = url;
  }

  Future<bool> _attemptTokenRefresh() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final refreshToken = prefs.getString(_refreshTokenKey);
      if (refreshToken == null) return false;

      final response = await Dio().post(
        '${_dio.options.baseUrl}/auth/refresh',
        data: {'refresh_token': refreshToken},
        options: Options(headers: {'Content-Type': 'application/json'}),
      );

      if (response.statusCode == 200) {
        final data = response.data as Map<String, dynamic>;
        await setTokens(
          data['access_token'] as String,
          data['refresh_token'] as String,
        );
        return true;
      }
      return false;
    } catch (_) {
      return false;
    }
  }

  Future<void> setTokens(String access, String refresh) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_accessTokenKey, access);
    await prefs.setString(_refreshTokenKey, refresh);
  }

  Future<void> clearTokens() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_accessTokenKey);
    await prefs.remove(_refreshTokenKey);
  }

  Future<Response> get(String path, {Map<String, dynamic>? queryParameters}) async {
    try {
      return await _dio.get(path, queryParameters: queryParameters);
    } on DioException catch (e) {
      throw AppException(
        e.message ?? 'GET request failed',
        statusCode: e.response?.statusCode,
        originalError: e,
      );
    }
  }

  Future<Response> post(String path, {dynamic data}) async {
    try {
      return await _dio.post(path, data: data);
    } on DioException catch (e) {
      throw AppException(
        e.message ?? 'POST request failed',
        statusCode: e.response?.statusCode,
        originalError: e,
      );
    }
  }

  Future<Response> put(String path, {dynamic data, Map<String, dynamic>? queryParameters}) async {
    try {
      return await _dio.put(path, data: data, queryParameters: queryParameters);
    } on DioException catch (e) {
      throw AppException(
        e.message ?? 'PUT request failed',
        statusCode: e.response?.statusCode,
        originalError: e,
      );
    }
  }

  Future<Response> delete(String path, {dynamic data}) async {
    try {
      return await _dio.delete(path, data: data);
    } on DioException catch (e) {
      throw AppException(
        e.message ?? 'DELETE request failed',
        statusCode: e.response?.statusCode,
        originalError: e,
      );
    }
  }
}
