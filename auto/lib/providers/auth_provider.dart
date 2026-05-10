import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:auto/services/api_client.dart';
import 'package:auto/services/auth_service.dart';
import 'package:auto/services/websocket_service.dart';

class AuthProvider extends ChangeNotifier {
  final AuthService _authService;
  // ignore: unused_field
  final ApiClient _apiClient;
  final WebSocketService _webSocketService;

  bool _isAuthenticated = false;
  Map<String, dynamic>? _user;
  bool _isLoading = false;
  String? _error;

  AuthProvider({
    required AuthService authService,
    required ApiClient apiClient,
    required WebSocketService webSocketService,
  })  : _authService = authService,
        _apiClient = apiClient,
        _webSocketService = webSocketService;

  // Getters
  bool get isAuthenticated => _isAuthenticated;
  Map<String, dynamic>? get user => _user;
  bool get isLoading => _isLoading;
  String? get error => _error;

  void setError(String message) {
    _error = message;
    notifyListeners();
  }

  /// Authenticate with Google ID token
  Future<void> loginWithGoogle(String idToken) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final response = await _authService.loginWithGoogle(idToken);
      _user = response;
      _isAuthenticated = true;
      _error = null;

      // Connect WebSocket after successful auth
      final token = await _authService.getStoredToken();
      if (token != null) {
        _webSocketService.connect(token);
      }
    } catch (e) {
      _error = e.toString();
      _isAuthenticated = false;
      _user = null;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Logout and clean up
  Future<void> logout() async {
    _isLoading = true;
    notifyListeners();

    try {
      _webSocketService.disconnect();
      await _authService.logout();
      await FirebaseAuth.instance.signOut();
      await GoogleSignIn().signOut();

      _isAuthenticated = false;
      _user = null;
      _error = null;
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Check stored token validity on startup
  Future<void> checkAuth() async {
    _isLoading = true;
    notifyListeners();

    try {
      final isValid = await _authService.verifyStoredToken();
      if (isValid) {
        _user = await _authService.getCurrentUser();
        _isAuthenticated = true;

        // Connect WebSocket if token is valid
        final token = await _authService.getStoredToken();
        if (token != null) {
          _webSocketService.connect(token);
        }
      } else {
        _isAuthenticated = false;
        _user = null;
      }
      _error = null;
    } catch (e) {
      _isAuthenticated = false;
      _user = null;
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  @override
  void dispose() {
    // WebSocket cleanup handled by logout or externally
    super.dispose();
  }
}
