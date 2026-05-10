import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:auto/services/trading_service.dart';
import 'package:auto/services/websocket_service.dart';

enum EngineStatus { running, stopped, emergency, error }

class TradingProvider extends ChangeNotifier {
  final TradingService _tradingService;
  final WebSocketService _webSocketService;

  // Engine state
  EngineStatus _engineStatus = EngineStatus.stopped;
  double _balance = 0.0;
  double _equity = 0.0;
  double _pnlToday = 0.0;
  double _floatingPl = 0.0;
  int _tradesToday = 0;
  double _winRate = 0.0;

  // Positions
  List<Map<String, dynamic>> _positions = [];

  // Sniper module
  double _sniperScore = 0.0;
  String _sniperDirection = 'NEUTRAL';
  double _sniperStrength = 0.0;

  // Regime detection
  String _regime = 'UNKNOWN';
  double _regimeConfidence = 0.0;

  // Adaptive risk
  double _adaptiveThreshold = 0.0;
  bool _adaptiveSafeMode = false;
  int _consecutiveLosses = 0;
  bool _highVolatilityMode = false;
  double _currentVolatility = 0.0;

  // WebSocket subscriptions
  StreamSubscription? _tickSubscription;
  StreamSubscription? _positionSubscription;
  StreamSubscription? _statusSubscription;
  StreamSubscription? _tradeClosedSubscription;
  StreamSubscription? _regimeSubscription;

  TradingProvider({
    required TradingService tradingService,
    required WebSocketService webSocketService,
  })  : _tradingService = tradingService,
        _webSocketService = webSocketService {
    _subscribeToEvents();
  }

  // Getters
  EngineStatus get engineStatus => _engineStatus;
  double get balance => _balance;
  double get equity => _equity;
  double get pnlToday => _pnlToday;
  double get floatingPl => _floatingPl;
  int get tradesToday => _tradesToday;
  double get winRate => _winRate;
  List<Map<String, dynamic>> get positions => List.unmodifiable(_positions);
  double get sniperScore => _sniperScore;
  String get sniperDirection => _sniperDirection;
  double get sniperStrength => _sniperStrength;
  String get regime => _regime;
  double get regimeConfidence => _regimeConfidence;
  double get adaptiveThreshold => _adaptiveThreshold;
  bool get adaptiveSafeMode => _adaptiveSafeMode;
  int get consecutiveLosses => _consecutiveLosses;
  bool get highVolatilityMode => _highVolatilityMode;
  double get currentVolatility => _currentVolatility;

  /// Subscribe to WebSocket events
  void _subscribeToEvents() {
    _tickSubscription = _webSocketService.on('tick.update').listen((data) {
      _updatePricesFromTick(data);
    });

    _positionSubscription =
        _webSocketService.on('position.update').listen((data) {
      _updatePositions(data);
    });

    _statusSubscription = _webSocketService.on('robot.status').listen((data) {
      _updateStatus(data);
    });

    _tradeClosedSubscription =
        _webSocketService.on('trade.closed').listen((data) {
      refreshStatus();
    });

    _regimeSubscription = _webSocketService.on('regime.update').listen((data) {
      _updateRegime(data);
    });
  }

  void _updatePricesFromTick(Map<String, dynamic> data) {
    // Update floating P&L from tick data if available
    if (data.containsKey('floating_pl')) {
      _floatingPl = (data['floating_pl'] as num).toDouble();
    }
    if (data.containsKey('equity')) {
      _equity = (data['equity'] as num).toDouble();
    }
    notifyListeners();
  }

  void _updatePositions(Map<String, dynamic> data) {
    if (data.containsKey('positions')) {
      _positions = List<Map<String, dynamic>>.from(data['positions']);
    }
    if (data.containsKey('floating_pl')) {
      _floatingPl = (data['floating_pl'] as num).toDouble();
    }
    notifyListeners();
  }

  void _updateStatus(Map<String, dynamic> data) {
    if (data.containsKey('status')) {
      _engineStatus = _parseEngineStatus(data['status']);
    }
    if (data.containsKey('balance')) {
      _balance = (data['balance'] as num).toDouble();
    }
    if (data.containsKey('equity')) {
      _equity = (data['equity'] as num).toDouble();
    }
    if (data.containsKey('pnl_today')) {
      _pnlToday = (data['pnl_today'] as num).toDouble();
    }
    if (data.containsKey('trades_today')) {
      _tradesToday = data['trades_today'] as int;
    }
    if (data.containsKey('win_rate')) {
      _winRate = (data['win_rate'] as num).toDouble();
    }
    if (data.containsKey('sniper_score')) {
      _sniperScore = (data['sniper_score'] as num).toDouble();
    }
    if (data.containsKey('sniper_direction')) {
      _sniperDirection = data['sniper_direction'] as String;
    }
    if (data.containsKey('sniper_strength')) {
      _sniperStrength = (data['sniper_strength'] as num).toDouble();
    }
    if (data.containsKey('adaptive_threshold')) {
      _adaptiveThreshold = (data['adaptive_threshold'] as num).toDouble();
    }
    if (data.containsKey('adaptive_safe_mode')) {
      _adaptiveSafeMode = data['adaptive_safe_mode'] as bool;
    }
    if (data.containsKey('consecutive_losses')) {
      _consecutiveLosses = data['consecutive_losses'] as int;
    }
    if (data.containsKey('high_volatility_mode')) {
      _highVolatilityMode = data['high_volatility_mode'] as bool;
    }
    if (data.containsKey('current_volatility')) {
      _currentVolatility = (data['current_volatility'] as num).toDouble();
    }
    notifyListeners();
  }

  void _updateRegime(Map<String, dynamic> data) {
    if (data.containsKey('regime')) {
      _regime = data['regime'] as String;
    }
    if (data.containsKey('confidence')) {
      _regimeConfidence = (data['confidence'] as num).toDouble();
    }
    if (data.containsKey('current_volatility')) {
      _currentVolatility = (data['current_volatility'] as num).toDouble();
    }
    if (data.containsKey('high_volatility_mode')) {
      _highVolatilityMode = data['high_volatility_mode'] as bool;
    }
    notifyListeners();
  }

  EngineStatus _parseEngineStatus(String status) {
    switch (status.toUpperCase()) {
      case 'RUNNING':
        return EngineStatus.running;
      case 'STOPPED':
        return EngineStatus.stopped;
      case 'EMERGENCY':
        return EngineStatus.emergency;
      case 'ERROR':
        return EngineStatus.error;
      default:
        return EngineStatus.stopped;
    }
  }

  /// Start the trading engine
  Future<void> startEngine() async {
    try {
      await _tradingService.startEngine();
      _engineStatus = EngineStatus.running;
      notifyListeners();
    } catch (e) {
      _engineStatus = EngineStatus.error;
      notifyListeners();
      rethrow;
    }
  }

  /// Stop the trading engine
  Future<void> stopEngine() async {
    try {
      await _tradingService.stopEngine();
      _engineStatus = EngineStatus.stopped;
      notifyListeners();
    } catch (e) {
      _engineStatus = EngineStatus.error;
      notifyListeners();
      rethrow;
    }
  }

  /// Emergency stop - close all positions immediately
  Future<void> emergencyStop() async {
    try {
      await _tradingService.emergencyStop();
      _engineStatus = EngineStatus.emergency;
      notifyListeners();
    } catch (e) {
      _engineStatus = EngineStatus.error;
      notifyListeners();
      rethrow;
    }
  }

  /// Refresh full status from API
  Future<void> refreshStatus() async {
    try {
      final status = await _tradingService.getStatus();
      _engineStatus = _parseEngineStatus(
          status['robot_status'] ?? status['status'] ?? 'STOPPED');
      _balance = (status['balance'] as num?)?.toDouble() ?? _balance;
      _equity = (status['equity'] as num?)?.toDouble() ?? _equity;
      _pnlToday = (status['today_realized_pl'] as num?)?.toDouble() ??
          (status['pnl_today'] as num?)?.toDouble() ?? _pnlToday;
      _floatingPl =
          (status['floating_pl'] as num?)?.toDouble() ?? _floatingPl;
      _tradesToday = (status['trades_today'] as int?) ?? _tradesToday;
      _winRate = (status['win_rate'] as num?)?.toDouble() ?? _winRate;
      _sniperScore =
          (status['sniper_last_score'] as num?)?.toDouble() ?? _sniperScore;
      _sniperDirection = _directionLabel(
          status['sniper_last_direction']);
      _sniperStrength =
          (status['sniper_last_strength'] as num?)?.toDouble() ?? _sniperStrength;
      _regime = (status['regime'] as String?) ?? _regime;
      _regimeConfidence =
          (status['regime_confidence'] as num?)?.toDouble() ?? _regimeConfidence;
      _adaptiveThreshold =
          (status['adaptive_threshold'] as num?)?.toDouble() ??
              _adaptiveThreshold;
      _adaptiveSafeMode =
          (status['adaptive_safe_mode'] as bool?) ?? _adaptiveSafeMode;
      _consecutiveLosses =
          (status['consecutive_losses'] as int?) ?? _consecutiveLosses;
      _highVolatilityMode =
          (status['high_volatility_mode'] as bool?) ?? _highVolatilityMode;
      _currentVolatility =
          (status['current_volatility'] as num?)?.toDouble() ??
              _currentVolatility;
      notifyListeners();
    } catch (e) {
      _engineStatus = EngineStatus.error;
      notifyListeners();
    }
  }

  String _directionLabel(dynamic dir) {
    if (dir == null) return _sniperDirection;
    if (dir is String) return dir;
    if (dir is int) {
      if (dir > 0) return 'BUY';
      if (dir < 0) return 'SELL';
      return 'NEUTRAL';
    }
    return _sniperDirection;
  }

  /// Load current open positions
  Future<void> loadPositions() async {
    try {
      final positions = await _tradingService.getPositions();
      _positions = List<Map<String, dynamic>>.from(positions);
      notifyListeners();
    } catch (e) {
      rethrow;
    }
  }

  @override
  void dispose() {
    _tickSubscription?.cancel();
    _positionSubscription?.cancel();
    _statusSubscription?.cancel();
    _tradeClosedSubscription?.cancel();
    _regimeSubscription?.cancel();
    super.dispose();
  }
}
