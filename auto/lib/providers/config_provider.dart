import 'package:flutter/foundation.dart';
import 'package:auto/services/trading_service.dart';

class ConfigProvider extends ChangeNotifier {
  final TradingService _tradingService = TradingService();

  Map<String, dynamic> _config = {};
  bool _isLoading = false;
  bool _isSaving = false;
  String? _error;

  Map<String, dynamic> get config => Map.unmodifiable(_config);
  bool get isLoading => _isLoading;
  bool get isSaving => _isSaving;
  String? get error => _error;

  // Trading Engine
  bool get tradingEnabled => (_config['trading_enabled'] as bool?) ?? true;

  // Risk Management
  double get riskPercent => (_config['risk_percent'] as num?)?.toDouble() ?? 0.5;
  double get maxDailyLoss => (_config['max_daily_loss_percent'] as num?)?.toDouble() ?? 3.0;
  int get maxConsecutiveLosses => (_config['max_consecutive_losses'] as int?) ?? 8;
  int get maxTradesPerDay => (_config['max_trades_per_day'] as int?) ?? 500;
  double get maxMarginUsage => (_config['max_margin_usage'] as num?)?.toDouble() ?? 60.0;
  double get minRiskRewardRatio => (_config['min_risk_reward_ratio'] as num?)?.toDouble() ?? 2.0;

  // Stop Loss
  String get slMethod => (_config['sl_method'] as String?) ?? 'hybrid';
  double get slMin => (_config['sl_min'] as num?)?.toDouble() ?? 30.0;
  double get slMax => (_config['sl_max'] as num?)?.toDouble() ?? 180.0;
  double get slAtrMinMultiplier => (_config['sl_atr_min_multiplier'] as num?)?.toDouble() ?? 0.4;
  double get slAtrMaxMultiplier => (_config['sl_atr_max_multiplier'] as num?)?.toDouble() ?? 1.0;
  bool get slUseVolatilityAdj => (_config['sl_use_volatility_adjustment'] as bool?) ?? true;

  // Sniper AI
  bool get useSniperAi => (_config['use_sniper_ai'] as bool?) ?? true;
  int get sniperMinScore => (_config['sniper_min_score'] as int?) ?? 57;
  int get sniperTickWindow => (_config['sniper_tick_window'] as int?) ?? 40;
  bool get sniperRequireAlignment => (_config['sniper_require_alignment'] as bool?) ?? true;
  double get sniperWMomentum => (_config['sniper_w_momentum'] as num?)?.toDouble() ?? 25.0;
  double get sniperWAcceleration => (_config['sniper_w_acceleration'] as num?)?.toDouble() ?? 20.0;
  double get sniperWRsi => (_config['sniper_w_rsi'] as num?)?.toDouble() ?? 25.0;
  double get sniperWVolatility => (_config['sniper_w_volatility'] as num?)?.toDouble() ?? 10.0;
  double get sniperWConfluence => (_config['sniper_w_confluence'] as num?)?.toDouble() ?? 15.0;
  double get sniperWVolume => (_config['sniper_w_volume'] as num?)?.toDouble() ?? 15.0;
  double get weakSignalLotReduction => (_config['weak_signal_lot_reduction'] as num?)?.toDouble() ?? 0.7;

  // Trailing Stop
  double get trailingLevel1 => (_config['trailing_level_1_multiplier'] as num?)?.toDouble() ?? 1.5;
  double get trailingLevel2 => (_config['trailing_level_2_multiplier'] as num?)?.toDouble() ?? 3.0;
  double get trailingLevel3 => (_config['trailing_level_3_multiplier'] as num?)?.toDouble() ?? 5.0;
  double get rapidModeAtr => (_config['rapid_mode_atr_multiplier'] as num?)?.toDouble() ?? 0.3;
  int get timeBasedBeMinutes => (_config['time_based_be_minutes'] as int?) ?? 10;
  double get timeBasedBeProfitThreshold => (_config['time_based_be_profit_threshold'] as num?)?.toDouble() ?? 0.5;
  double get highVolTrailingExpansion => (_config['high_volatility_trailing_expansion'] as num?)?.toDouble() ?? 0.2;

  // Micro Timeframes
  bool get useMicroTimeframes => (_config['use_micro_timeframes'] as bool?) ?? true;
  bool get useMicro5s => (_config['use_micro_5s'] as bool?) ?? true;
  bool get useMicro10s => (_config['use_micro_10s'] as bool?) ?? true;
  bool get useMicro15s => (_config['use_micro_15s'] as bool?) ?? true;
  bool get useMicro20s => (_config['use_micro_20s'] as bool?) ?? true;
  bool get useMicro30s => (_config['use_micro_30s'] as bool?) ?? true;
  int get microCooldownSec => (_config['micro_cooldown_sec'] as int?) ?? 3;

  // Positions / Grid
  int get maxPositionsPerDirection => (_config['max_positions_per_direction'] as int?) ?? 1;
  int get maxTotalPositions => (_config['max_total_positions'] as int?) ?? 2;
  bool get allowHedging => (_config['allow_hedging'] as bool?) ?? false;
  bool get usePyramidingLots => (_config['use_pyramiding_lots'] as bool?) ?? false;
  double get lotMultiplier => (_config['lot_multiplier'] as num?)?.toDouble() ?? 0.5;
  int get entrySpacingPoints => (_config['entry_spacing_points'] as int?) ?? 120;

  // Filters
  bool get useRsiFilter => (_config['use_rsi_filter'] as bool?) ?? true;
  double get rsiOverbought => (_config['rsi_overbought'] as num?)?.toDouble() ?? 72.0;
  double get rsiOversold => (_config['rsi_oversold'] as num?)?.toDouble() ?? 28.0;
  bool get useAdxFilter => (_config['use_adx_filter'] as bool?) ?? false;
  double get adxMinValue => (_config['adx_min_value'] as num?)?.toDouble() ?? 25.0;
  bool get useSpreadFilter => (_config['use_spread_filter'] as bool?) ?? true;
  int get maxSpreadPoints => (_config['max_spread_points'] as int?) ?? 300;
  bool get useGapFilter => (_config['use_gap_filter'] as bool?) ?? true;
  bool get useVolatilityFilter => (_config['use_volatility_filter'] as bool?) ?? true;
  bool get allowHighVolTrading => (_config['allow_high_volatility_trading'] as bool?) ?? true;
  double get highVolRiskFactor => (_config['high_volatility_risk_factor'] as num?)?.toDouble() ?? 0.5;

  // Schedule
  int get tradingStartHour => (_config['trading_start_hour'] as int?) ?? 8;
  int get tradingStartMinute => (_config['trading_start_minute'] as int?) ?? 0;
  int get tradingStopHour => (_config['trading_stop_hour'] as int?) ?? 22;
  int get tradingStopMinute => (_config['trading_stop_minute'] as int?) ?? 0;

  Future<void> loadConfig() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      _config = await _tradingService.getConfig();
      _error = null;
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> saveConfig(Map<String, dynamic> newConfig) async {
    _isSaving = true;
    _error = null;
    notifyListeners();

    try {
      await _tradingService.updateConfig(newConfig);
      _config = Map<String, dynamic>.from(newConfig);
      _error = null;
    } catch (e) {
      _error = e.toString();
    } finally {
      _isSaving = false;
      notifyListeners();
    }
  }

  void updateField(String key, dynamic value) {
    final updated = Map<String, dynamic>.from(_config);
    updated[key] = value;
    _config = updated;
    notifyListeners();
  }

  Future<void> pushConfig() async {
    _isSaving = true;
    notifyListeners();
    try {
      await _tradingService.updateConfig(_config);
      _error = null;
    } catch (e) {
      _error = e.toString();
    } finally {
      _isSaving = false;
      notifyListeners();
    }
  }
}
