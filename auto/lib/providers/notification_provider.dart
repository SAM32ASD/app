import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:auto/services/websocket_service.dart';
import 'package:auto/services/notification_service.dart';
import 'package:auto/widgets/trade_notification.dart';

enum AlertType { emergency, connectionError, engineStopped }

class AlertEvent {
  final AlertType type;
  final String title;
  final String message;
  final DateTime time;

  AlertEvent({required this.type, required this.title, required this.message})
      : time = DateTime.now();
}

class NotificationProvider extends ChangeNotifier {
  final WebSocketService _webSocketService;
  final NotificationService _notificationService;

  final List<TradeNotification> _notifications = [];
  final List<TradeNotification> _toastQueue = [];
  AlertEvent? _pendingAlert;
  int _unreadCount = 0;
  bool _connected = false;

  StreamSubscription? _tradeOpenedSub;
  StreamSubscription? _tradeClosedSub;
  StreamSubscription? _emergencySub;
  StreamSubscription? _statusSub;
  StreamSubscription? _connectionErrorSub;
  StreamSubscription? _wsStateSub;

  NotificationProvider({
    required WebSocketService webSocketService,
    required NotificationService notificationService,
  })  : _webSocketService = webSocketService,
        _notificationService = notificationService {
    _connected = webSocketService.connectionState == WsConnectionState.connected;
    _subscribe();
  }

  List<TradeNotification> get notifications => List.unmodifiable(_notifications);
  List<TradeNotification> get toastQueue => List.unmodifiable(_toastQueue);
  AlertEvent? get pendingAlert => _pendingAlert;
  int get unreadCount => _unreadCount;
  bool get connected => _connected;

  void _subscribe() {
    _tradeOpenedSub = _webSocketService.on('trade.opened').listen(_onTradeOpened);
    _tradeClosedSub = _webSocketService.on('trade.closed').listen(_onTradeClosed);
    _emergencySub = _webSocketService.on('emergency.triggered').listen(_onEmergency);
    _statusSub = _webSocketService.on('robot.status').listen(_onRobotStatus);
    _connectionErrorSub = _webSocketService.on('mt5.connection_error').listen(_onConnectionError);
    _wsStateSub = _webSocketService.connectionStateStream.listen((state) {
      _connected = state == WsConnectionState.connected;
      notifyListeners();
    });
  }

  void _onTradeOpened(Map<String, dynamic> data) {
    final type = (data['type'] as String?) ?? 'BUY';
    final lots = (data['lots'] as num?)?.toDouble() ?? 0.0;
    final price = (data['price'] as num?)?.toDouble() ?? 0.0;
    final source = (data['source'] as String?) ?? '';

    _notificationService.showTradeOpened(
      type: type,
      lots: lots,
      price: price,
      source: source,
    );

    final n = TradeNotification(
      type: type,
      lots: lots,
      pnl: 0.0,
      source: 'OPENED $source',
      time: DateTime.now(),
    );
    _addNotification(n);
  }

  void _onTradeClosed(Map<String, dynamic> data) {
    final type = (data['type'] as String?) ?? 'BUY';
    final lots = (data['volume'] as num?)?.toDouble() ??
        (data['lots'] as num?)?.toDouble() ?? 0.0;
    final profit = (data['profit'] as num?)?.toDouble() ?? 0.0;
    final source = (data['comment'] as String?) ??
        (data['source'] as String?) ?? '';

    _notificationService.showTradeClosed(
      type: type,
      lots: lots,
      profit: profit,
    );

    final n = TradeNotification(
      type: type,
      lots: lots,
      pnl: profit,
      source: source,
      time: DateTime.now(),
    );
    _addNotification(n);
    _addToast(n);
  }

  void _onEmergency(Map<String, dynamic> data) {
    final closedCount = (data['closed_count'] as int?) ?? 0;

    _notificationService.showEmergencyStop(closedCount: closedCount);

    _pendingAlert = AlertEvent(
      type: AlertType.emergency,
      title: 'EMERGENCY STOP',
      message: 'All positions closed ($closedCount). Engine halted immediately.',
    );
    notifyListeners();
  }

  void _onRobotStatus(Map<String, dynamic> data) {
    final status = (data['status'] as String?) ?? '';
    _connected = status.toUpperCase() == 'RUNNING';

    if (status.toUpperCase() == 'STOPPED') {
      _notificationService.showEngineStatus('STOPPED');
    } else if (status.toUpperCase() == 'RUNNING') {
      _notificationService.showEngineStatus('RUNNING');
    } else if (status.toUpperCase() == 'ERROR') {
      _pendingAlert = AlertEvent(
        type: AlertType.engineStopped,
        title: 'ENGINE ERROR',
        message: (data['message'] as String?) ?? 'Engine encountered an error and stopped.',
      );
      notifyListeners();
    }
    notifyListeners();
  }

  void _onConnectionError(Map<String, dynamic> data) {
    final message = (data['message'] as String?) ?? 'MT5 connection lost';

    _notificationService.showConnectionError(message);

    _pendingAlert = AlertEvent(
      type: AlertType.connectionError,
      title: 'CONNECTION ERROR',
      message: message,
    );
    notifyListeners();
  }

  void _addNotification(TradeNotification n) {
    _notifications.add(n);
    if (_notifications.length > 100) {
      _notifications.removeAt(0);
    }
    _unreadCount++;
    notifyListeners();
  }

  void _addToast(TradeNotification n) {
    _toastQueue.add(n);
    notifyListeners();
  }

  void dismissToast(int index) {
    if (index < _toastQueue.length) {
      _toastQueue.removeAt(index);
      notifyListeners();
    }
  }

  void dismissFirstToast() {
    if (_toastQueue.isNotEmpty) {
      _toastQueue.removeAt(0);
      notifyListeners();
    }
  }

  void dismissAlert() {
    _pendingAlert = null;
    notifyListeners();
  }

  void markAllRead() {
    _unreadCount = 0;
    notifyListeners();
  }

  void clearAll() {
    _notifications.clear();
    _unreadCount = 0;
    notifyListeners();
  }

  @override
  void dispose() {
    _tradeOpenedSub?.cancel();
    _tradeClosedSub?.cancel();
    _emergencySub?.cancel();
    _statusSub?.cancel();
    _connectionErrorSub?.cancel();
    _wsStateSub?.cancel();
    super.dispose();
  }
}
