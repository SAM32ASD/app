import 'package:flutter/foundation.dart';
import 'package:auto/services/trading_service.dart';

class TradeHistoryProvider extends ChangeNotifier {
  final TradingService _tradingService = TradingService();

  List<Map<String, dynamic>> _trades = [];
  bool _isLoading = false;
  bool _hasMore = true;
  int _currentPage = 1;
  String? _error;

  static const int _pageSize = 20;

  List<Map<String, dynamic>> get trades => List.unmodifiable(_trades);
  bool get isLoading => _isLoading;
  bool get hasMore => _hasMore;
  int get currentPage => _currentPage;
  String? get error => _error;

  Future<void> loadTrades({bool refresh = false}) async {
    if (_isLoading) return;

    if (refresh) {
      _currentPage = 1;
      _hasMore = true;
    }

    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final response = await _tradingService.getHistory(
        page: _currentPage,
        limit: _pageSize,
      );

      final List<dynamic> newTrades = response['trades'] ?? [];
      final int totalCount = (response['total'] as int?) ?? 0;

      if (refresh) {
        _trades = newTrades.cast<Map<String, dynamic>>();
      } else {
        _trades.addAll(newTrades.cast<Map<String, dynamic>>());
      }

      _hasMore = _trades.length < totalCount;
      _error = null;
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> loadMore() async {
    if (!_hasMore || _isLoading) return;
    _currentPage++;
    await loadTrades();
  }
}
