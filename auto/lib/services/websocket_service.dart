import 'dart:async';
import 'dart:convert';
import 'dart:math';

import 'package:flutter/foundation.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

enum WsConnectionState { disconnected, connecting, connected }

class WebSocketService {
  static final WebSocketService _instance = WebSocketService._internal();
  factory WebSocketService() => _instance;
  WebSocketService._internal();

  WebSocketChannel? _channel;
  final _eventController = StreamController<Map<String, dynamic>>.broadcast();
  final _connectionStateController = StreamController<WsConnectionState>.broadcast();
  Timer? _reconnectTimer;
  int _reconnectAttempts = 0;
  bool _intentionalDisconnect = false;
  String? _currentToken;
  WsConnectionState _connectionState = WsConnectionState.disconnected;

  static const _maxBackoff = Duration(seconds: 30);

  Stream<Map<String, dynamic>> get events => _eventController.stream;

  Stream<WsConnectionState> get connectionStateStream => _connectionStateController.stream;
  WsConnectionState get connectionState => _connectionState;

  Stream<Map<String, dynamic>> on(String eventType) =>
      _eventController.stream.where((msg) => msg['type'] == eventType);

  Stream<Map<String, dynamic>> get tickUpdates => on('tick.update');
  Stream<Map<String, dynamic>> get positionUpdates => on('position.update');
  Stream<Map<String, dynamic>> get tradeOpened => on('trade.opened');
  Stream<Map<String, dynamic>> get tradeClosed => on('trade.closed');
  Stream<Map<String, dynamic>> get robotStatus => on('robot.status');
  Stream<Map<String, dynamic>> get emergencyTriggered => on('emergency.triggered');
  Stream<Map<String, dynamic>> get regimeUpdates => on('regime.update');

  void connect(String token) {
    _currentToken = token;
    _intentionalDisconnect = false;
    _reconnectAttempts = 0;
    _connect();
  }

  void _connect() {
    _setConnectionState(WsConnectionState.connecting);
    final host = kIsWeb ? 'localhost:8000' : '10.28.145.41:8000';
    final uri = Uri.parse('ws://$host/api/v1/ws/trading?token=$_currentToken');

    try {
      _channel = WebSocketChannel.connect(uri);
      _channel!.stream.listen(
        _onMessage,
        onError: _onError,
        onDone: _onDone,
      );
      _reconnectAttempts = 0;
      _setConnectionState(WsConnectionState.connected);
    } catch (e) {
      _setConnectionState(WsConnectionState.disconnected);
      _scheduleReconnect();
    }
  }

  void _onMessage(dynamic message) {
    try {
      final raw = jsonDecode(message as String) as Map<String, dynamic>;
      // Backend sends {"event": "...", "data": {...}}
      // Normalize to {"type": "...", ...data}
      if (raw.containsKey('event')) {
        final eventType = raw['event'] as String;
        final payload = raw['data'] as Map<String, dynamic>? ?? {};
        final normalized = Map<String, dynamic>.from(payload);
        normalized['type'] = eventType;
        _eventController.add(normalized);
      } else {
        _eventController.add(raw);
      }
    } catch (_) {}
  }

  void _onError(dynamic error) {
    debugPrint('WebSocket error: $error');
    _setConnectionState(WsConnectionState.disconnected);
    _scheduleReconnect();
  }

  void _onDone() {
    _setConnectionState(WsConnectionState.disconnected);
    if (!_intentionalDisconnect) {
      _scheduleReconnect();
    }
  }

  void _scheduleReconnect() {
    _reconnectTimer?.cancel();
    final backoff = Duration(
      seconds: min(pow(2, _reconnectAttempts).toInt(), _maxBackoff.inSeconds),
    );
    _reconnectAttempts++;
    _reconnectTimer = Timer(backoff, _connect);
  }

  void _setConnectionState(WsConnectionState state) {
    if (_connectionState != state) {
      _connectionState = state;
      _connectionStateController.add(state);
    }
  }

  void send(Map<String, dynamic> message) {
    _channel?.sink.add(jsonEncode(message));
  }

  void disconnect() {
    _intentionalDisconnect = true;
    _reconnectTimer?.cancel();
    _channel?.sink.close();
    _channel = null;
    _setConnectionState(WsConnectionState.disconnected);
  }
}
