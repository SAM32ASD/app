import 'dart:async';

import 'package:shared_preferences/shared_preferences.dart';

import 'api_client.dart';
import 'app_exception.dart';

class AuthService {
  static final AuthService _instance = AuthService._internal();
  factory AuthService() => _instance;
  AuthService._internal() {
    // Listen for auth-expired events from the API client.
    ApiClient().onAuthExpired.listen((_) {
      _authStateController.add(false);
    });
  }

  final _api = ApiClient();
  final _authStateController = StreamController<bool>.broadcast();

  /// Emits true when authenticated, false when logged out or token expired.
  Stream<bool> get authState => _authStateController.stream;

  /// Check stored token on app start. Returns true if a valid session exists.
  Future<bool> checkAuth() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('access_token');
    if (token == null) {
      _authStateController.add(false);
      return false;
    }
    try {
      await verifyToken();
      _authStateController.add(true);
      return true;
    } on AppException {
      _authStateController.add(false);
      return false;
    }
  }

  /// Authenticate with a Google ID token. Returns user data map.
  Future<Map<String, dynamic>> loginWithGoogle(String idToken) async {
    final response = await _api.post(
      '/auth/google',
      data: {'id_token': idToken},
    );
    final data = response.data as Map<String, dynamic>;
    await _api.setTokens(
      data['access_token'] as String,
      data['refresh_token'] as String,
    );
    _authStateController.add(true);
    return data['user'] as Map<String, dynamic>;
  }

  /// Refresh the current access token using the stored refresh token.
  Future<void> refreshToken() async {
    final prefs = await SharedPreferences.getInstance();
    final refresh = prefs.getString('refresh_token');
    if (refresh == null) {
      throw const AppException('No refresh token available');
    }
    final response = await _api.post(
      '/auth/refresh',
      data: {'refresh_token': refresh},
    );
    final data = response.data as Map<String, dynamic>;
    await _api.setTokens(
      data['access_token'] as String,
      data['refresh_token'] as String,
    );
  }

  /// Log out: notify server, clear local tokens, emit state.
  Future<void> logout() async {
    try {
      await _api.post('/auth/logout');
    } catch (_) {
      // Best-effort server notification
    }
    await _api.clearTokens();
    _authStateController.add(false);
  }

  /// Verify the current access token is still valid.
  Future<void> verifyToken() async {
    await _api.post('/auth/verify');
  }

  /// Check if stored token is still valid. Returns true/false.
  Future<bool> verifyStoredToken() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('access_token');
    if (token == null) return false;
    try {
      await verifyToken();
      return true;
    } catch (_) {
      return false;
    }
  }

  /// Get stored access token (for WebSocket connection).
  Future<String?> getStoredToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('access_token');
  }

  /// Get current user info from the server.
  Future<Map<String, dynamic>?> getCurrentUser() async {
    try {
      final response = await _api.post('/auth/verify');
      return response.data as Map<String, dynamic>?;
    } catch (_) {
      return null;
    }
  }
}
