import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:auto/services/trading_service.dart';
import 'package:auto/services/websocket_service.dart';

class MarketProvider extends ChangeNotifier {
  final TradingService _tradingService;
  final WebSocketService _webSocketService;

  double _bid = 0.0;
  double _ask = 0.0;
  double _spread = 0.0;
  double _prevBid = 0.0;
  DateTime? _lastTickTime;

  double _atr = 0.0;
  String _volatilityStatus = 'NORMAL';

  Map<String, dynamic> _indicators = {};

  StreamSubscription? _tickSubscription;

  MarketProvider({
    required WebSocketService webSocketService,
    required TradingService tradingService,
  })  : _webSocketService = webSocketService,
        _tradingService = tradingService {
    _subscribeToTicks();
  }

  double get bid => _bid;
  double get ask => _ask;
  double get spread => _spread;
  double get prevBid => _prevBid;
  DateTime? get lastTickTime => _lastTickTime;
  double get atr => _atr;
  String get volatilityStatus => _volatilityStatus;
  Map<String, dynamic> get indicators => Map.unmodifiable(_indicators);

  void _subscribeToTicks() {
    _tickSubscription = _webSocketService.on('tick.update').listen((data) {
      _handleTickUpdate(data);
    });
  }

  void _handleTickUpdate(Map<String, dynamic> data) {
    _prevBid = _bid;
    if (data.containsKey('bid')) {
      _bid = (data['bid'] as num).toDouble();
    }
    if (data.containsKey('ask')) {
      _ask = (data['ask'] as num).toDouble();
    }
    if (data.containsKey('spread')) {
      _spread = (data['spread'] as num).toDouble();
    } else if (_bid > 0 && _ask > 0) {
      _spread = _ask - _bid;
    }
    if (data.containsKey('time')) {
      final t = data['time'];
      if (t is num) {
        _lastTickTime = DateTime.fromMillisecondsSinceEpoch((t * 1000).toInt());
      }
    } else {
      _lastTickTime = DateTime.now();
    }
    notifyListeners();
  }

  Future<void> loadIndicators() async {
    try {
      _indicators = await _tradingService.getMarketIndicators();
      final vol = _indicators['volatility'] as Map<String, dynamic>? ?? {};
      _atr = (vol['normalized_atr'] as num?)?.toDouble() ?? _atr;
      _volatilityStatus = (vol['status'] as String?) ?? _volatilityStatus;
      notifyListeners();
    } catch (_) {}
  }

  @override
  void dispose() {
    _tickSubscription?.cancel();
    super.dispose();
  }
}
