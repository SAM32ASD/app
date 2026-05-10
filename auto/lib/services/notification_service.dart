import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';

class NotificationService {
  static final NotificationService _instance = NotificationService._internal();
  factory NotificationService() => _instance;
  NotificationService._internal();

  final FlutterLocalNotificationsPlugin _plugin = FlutterLocalNotificationsPlugin();
  bool _initialized = false;

  Future<void> initialize() async {
    if (_initialized) return;
    if (kIsWeb) {
      _initialized = true;
      return;
    }

    const android = AndroidInitializationSettings('@mipmap/ic_launcher');
    const darwin = DarwinInitializationSettings(
      requestAlertPermission: true,
      requestBadgePermission: true,
      requestSoundPermission: true,
    );
    const settings = InitializationSettings(android: android, iOS: darwin, macOS: darwin);
    await _plugin.initialize(settings);
    _initialized = true;
  }

  Future<void> showTradeOpened({
    required String type,
    required double lots,
    required double price,
    required String source,
  }) async {
    await _show(
      id: 1,
      title: '$type OPENED',
      body: '${lots.toStringAsFixed(2)} lots @ ${price.toStringAsFixed(2)} [$source]',
      channel: 'trades',
      channelName: 'Trade Alerts',
    );
  }

  Future<void> showTradeClosed({
    required String type,
    required double lots,
    required double profit,
  }) async {
    final win = profit >= 0;
    await _show(
      id: 2,
      title: '$type CLOSED ${win ? "WIN" : "LOSS"}',
      body: '${lots.toStringAsFixed(2)} lots → ${win ? "+" : ""}\$${profit.toStringAsFixed(2)}',
      channel: 'trades',
      channelName: 'Trade Alerts',
    );
  }

  Future<void> showEmergencyStop({int closedCount = 0}) async {
    await _show(
      id: 3,
      title: 'EMERGENCY STOP',
      body: 'All positions closed ($closedCount). Engine halted.',
      channel: 'emergency',
      channelName: 'Emergency Alerts',
      importance: Importance.max,
      priority: Priority.high,
    );
  }

  Future<void> showEngineStatus(String status) async {
    await _show(
      id: 4,
      title: 'Engine $status',
      body: 'Trading engine is now ${status.toLowerCase()}.',
      channel: 'status',
      channelName: 'Engine Status',
    );
  }

  Future<void> showConnectionError(String message) async {
    await _show(
      id: 5,
      title: 'Connection Error',
      body: message,
      channel: 'errors',
      channelName: 'Errors',
      importance: Importance.high,
      priority: Priority.high,
    );
  }

  Future<void> _show({
    required int id,
    required String title,
    required String body,
    required String channel,
    required String channelName,
    Importance importance = Importance.defaultImportance,
    Priority priority = Priority.defaultPriority,
  }) async {
    if (kIsWeb) return;
    if (!_initialized) return;
    if (!Platform.isAndroid && !Platform.isIOS && !Platform.isMacOS) return;

    final androidDetails = AndroidNotificationDetails(
      channel,
      channelName,
      importance: importance,
      priority: priority,
      showWhen: true,
    );
    final darwinDetails = DarwinNotificationDetails();
    final details = NotificationDetails(android: androidDetails, iOS: darwinDetails, macOS: darwinDetails);
    await _plugin.show(id, title, body, details);
  }
}
