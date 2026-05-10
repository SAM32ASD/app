import 'api_client.dart';

class TradingService {
  static final TradingService _instance = TradingService._internal();
  factory TradingService() => _instance;
  TradingService._internal();

  final _api = ApiClient();

  /// Get current trading engine status.
  Future<Map<String, dynamic>> getStatus() async {
    final response = await _api.get('/trading/status');
    return response.data as Map<String, dynamic>;
  }

  /// Start the trading engine.
  Future<Map<String, dynamic>> startEngine() async {
    final response = await _api.post('/trading/start');
    return response.data as Map<String, dynamic>;
  }

  /// Stop the trading engine gracefully.
  Future<Map<String, dynamic>> stopEngine() async {
    final response = await _api.post('/trading/stop');
    return response.data as Map<String, dynamic>;
  }

  /// Trigger emergency stop — closes all positions immediately.
  Future<Map<String, dynamic>> emergencyStop() async {
    final response = await _api.post('/trading/emergency-stop');
    return response.data as Map<String, dynamic>;
  }

  /// Get trading engine configuration.
  Future<Map<String, dynamic>> getConfig() async {
    final response = await _api.get('/trading/config');
    return response.data as Map<String, dynamic>;
  }

  /// Update trading engine configuration.
  Future<Map<String, dynamic>> updateConfig(Map<String, dynamic> config) async {
    final response = await _api.put('/trading/config', data: config);
    return response.data as Map<String, dynamic>;
  }

  /// Get current open positions.
  Future<List<dynamic>> getPositions() async {
    final response = await _api.get('/trading/positions');
    return response.data as List<dynamic>;
  }

  /// Get trade history with pagination.
  Future<Map<String, dynamic>> getHistory({int page = 1, int limit = 20}) async {
    final response = await _api.get(
      '/trading/history',
      queryParameters: {'page': page, 'limit': limit},
    );
    return response.data as Map<String, dynamic>;
  }

  /// Get current market indicators / regime data.
  Future<Map<String, dynamic>> getMarketIndicators() async {
    final response = await _api.get('/market/indicators');
    return response.data as Map<String, dynamic>;
  }
}
