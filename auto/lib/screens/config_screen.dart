import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../theme/app_theme.dart';
import '../widgets/terminal_card.dart';
import '../providers/config_provider.dart';

class ConfigScreen extends StatefulWidget {
  const ConfigScreen({super.key});

  @override
  State<ConfigScreen> createState() => _ConfigScreenState();
}

class _ConfigScreenState extends State<ConfigScreen> {
  @override
  Widget build(BuildContext context) {
    final cfg = context.watch<ConfigProvider>();

    if (cfg.isLoading) {
      return const Center(
        child: CircularProgressIndicator(color: AppColors.cyan, strokeWidth: 2),
      );
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      child: Column(
        children: [
          _section('TRADING ENGINE', [
            _toggleRow('Trading Enabled', cfg.tradingEnabled,
                (v) => cfg.updateField('trading_enabled', v)),
          ]),
          const SizedBox(height: 8),
          _section('RISK MANAGEMENT', [
            _sliderRow('Risk per Trade', cfg.riskPercent, 0.1, 2.0, '%',
                (v) => cfg.updateField('risk_percent', _round1(v))),
            _sliderRow('Max Daily Loss', cfg.maxDailyLoss, 1.0, 10.0, '%',
                (v) => cfg.updateField('max_daily_loss_percent', _round1(v))),
            _sliderRow('Max Margin Usage', cfg.maxMarginUsage, 10.0, 100.0, '%',
                (v) => cfg.updateField('max_margin_usage', _round1(v))),
            _sliderRow('Min Risk/Reward', cfg.minRiskRewardRatio, 1.0, 5.0, 'x',
                (v) => cfg.updateField('min_risk_reward_ratio', _round1(v))),
            _intRow('Max Consec. Losses', cfg.maxConsecutiveLosses, 3, 15,
                (v) => cfg.updateField('max_consecutive_losses', v)),
            _intRow('Max Trades/Day', cfg.maxTradesPerDay, 10, 1000,
                (v) => cfg.updateField('max_trades_per_day', v)),
          ]),
          const SizedBox(height: 8),
          _section('STOP LOSS', [
            _dropdownRow('SL Method', cfg.slMethod,
                ['hybrid', 'atr_adaptive', 'swings', 'sr', 'fixed'],
                (v) => cfg.updateField('sl_method', v)),
            _sliderRow('SL Min (pts)', cfg.slMin, 10.0, 100.0, '',
                (v) => cfg.updateField('sl_min', _round1(v))),
            _sliderRow('SL Max (pts)', cfg.slMax, 50.0, 500.0, '',
                (v) => cfg.updateField('sl_max', _round1(v))),
            _sliderRow('ATR Min Mult.', cfg.slAtrMinMultiplier, 0.1, 2.0, 'x',
                (v) => cfg.updateField('sl_atr_min_multiplier', _round2(v))),
            _sliderRow('ATR Max Mult.', cfg.slAtrMaxMultiplier, 0.5, 3.0, 'x',
                (v) => cfg.updateField('sl_atr_max_multiplier', _round2(v))),
            _toggleRow('Volatility Adj.', cfg.slUseVolatilityAdj,
                (v) => cfg.updateField('sl_use_volatility_adjustment', v)),
          ]),
          const SizedBox(height: 8),
          _section('SNIPER AI', [
            _toggleRow('Sniper AI Enabled', cfg.useSniperAi,
                (v) => cfg.updateField('use_sniper_ai', v)),
            _intRow('Min Score', cfg.sniperMinScore, 50, 95,
                (v) => cfg.updateField('sniper_min_score', v)),
            _intRow('Tick Window', cfg.sniperTickWindow, 10, 100,
                (v) => cfg.updateField('sniper_tick_window', v)),
            _toggleRow('Require Alignment', cfg.sniperRequireAlignment,
                (v) => cfg.updateField('sniper_require_alignment', v)),
            _sliderRow('Weak Signal Lot', cfg.weakSignalLotReduction, 0.3, 1.0, 'x',
                (v) => cfg.updateField('weak_signal_lot_reduction', _round2(v))),
          ]),
          const SizedBox(height: 8),
          _section('SNIPER WEIGHTS', [
            _sliderRow('Momentum', cfg.sniperWMomentum, 0.0, 50.0, '',
                (v) => cfg.updateField('sniper_w_momentum', _round1(v))),
            _sliderRow('Acceleration', cfg.sniperWAcceleration, 0.0, 50.0, '',
                (v) => cfg.updateField('sniper_w_acceleration', _round1(v))),
            _sliderRow('RSI', cfg.sniperWRsi, 0.0, 50.0, '',
                (v) => cfg.updateField('sniper_w_rsi', _round1(v))),
            _sliderRow('Volatility', cfg.sniperWVolatility, 0.0, 50.0, '',
                (v) => cfg.updateField('sniper_w_volatility', _round1(v))),
            _sliderRow('Confluence', cfg.sniperWConfluence, 0.0, 50.0, '',
                (v) => cfg.updateField('sniper_w_confluence', _round1(v))),
            _sliderRow('Volume', cfg.sniperWVolume, 0.0, 50.0, '',
                (v) => cfg.updateField('sniper_w_volume', _round1(v))),
          ]),
          const SizedBox(height: 8),
          _section('TRAILING STOP', [
            _sliderRow('Level 1 (BE)', cfg.trailingLevel1, 0.5, 3.0, 'x',
                (v) => cfg.updateField('trailing_level_1_multiplier', _round2(v))),
            _sliderRow('Level 2 (Lock 50%)', cfg.trailingLevel2, 1.5, 6.0, 'x',
                (v) => cfg.updateField('trailing_level_2_multiplier', _round2(v))),
            _sliderRow('Level 3 (Rapid)', cfg.trailingLevel3, 3.0, 10.0, 'x',
                (v) => cfg.updateField('trailing_level_3_multiplier', _round2(v))),
            _sliderRow('Rapid Mode ATR', cfg.rapidModeAtr, 0.1, 1.0, 'x',
                (v) => cfg.updateField('rapid_mode_atr_multiplier', _round2(v))),
            _intRow('Time-Based BE (min)', cfg.timeBasedBeMinutes, 3, 30,
                (v) => cfg.updateField('time_based_be_minutes', v)),
            _sliderRow('BE Profit Thresh.', cfg.timeBasedBeProfitThreshold, 0.1, 2.0, 'x SL',
                (v) => cfg.updateField('time_based_be_profit_threshold', _round2(v))),
            _sliderRow('High Vol Expansion', cfg.highVolTrailingExpansion, 0.0, 0.5, '',
                (v) => cfg.updateField('high_volatility_trailing_expansion', _round2(v))),
          ]),
          const SizedBox(height: 8),
          _section('MICRO TIMEFRAMES', [
            _toggleRow('Micro TF Enabled', cfg.useMicroTimeframes,
                (v) => cfg.updateField('use_micro_timeframes', v)),
            _toggleRow('5s', cfg.useMicro5s,
                (v) => cfg.updateField('use_micro_5s', v)),
            _toggleRow('10s', cfg.useMicro10s,
                (v) => cfg.updateField('use_micro_10s', v)),
            _toggleRow('15s', cfg.useMicro15s,
                (v) => cfg.updateField('use_micro_15s', v)),
            _toggleRow('20s', cfg.useMicro20s,
                (v) => cfg.updateField('use_micro_20s', v)),
            _toggleRow('30s', cfg.useMicro30s,
                (v) => cfg.updateField('use_micro_30s', v)),
            _intRow('Cooldown (sec)', cfg.microCooldownSec, 1, 15,
                (v) => cfg.updateField('micro_cooldown_sec', v)),
          ]),
          const SizedBox(height: 8),
          _section('POSITIONS / GRID', [
            _intRow('Max per Direction', cfg.maxPositionsPerDirection, 1, 5,
                (v) => cfg.updateField('max_positions_per_direction', v)),
            _intRow('Max Total', cfg.maxTotalPositions, 1, 10,
                (v) => cfg.updateField('max_total_positions', v)),
            _toggleRow('Allow Hedging', cfg.allowHedging,
                (v) => cfg.updateField('allow_hedging', v)),
            _toggleRow('Pyramiding Lots', cfg.usePyramidingLots,
                (v) => cfg.updateField('use_pyramiding_lots', v)),
            _sliderRow('Lot Multiplier', cfg.lotMultiplier, 0.1, 2.0, 'x',
                (v) => cfg.updateField('lot_multiplier', _round2(v))),
            _intRow('Entry Spacing (pts)', cfg.entrySpacingPoints, 20, 500,
                (v) => cfg.updateField('entry_spacing_points', v)),
          ]),
          const SizedBox(height: 8),
          _section('FILTERS', [
            _toggleRow('RSI Filter', cfg.useRsiFilter,
                (v) => cfg.updateField('use_rsi_filter', v)),
            _sliderRow('RSI Overbought', cfg.rsiOverbought, 60.0, 90.0, '',
                (v) => cfg.updateField('rsi_overbought', _round1(v))),
            _sliderRow('RSI Oversold', cfg.rsiOversold, 10.0, 40.0, '',
                (v) => cfg.updateField('rsi_oversold', _round1(v))),
            _toggleRow('ADX Filter', cfg.useAdxFilter,
                (v) => cfg.updateField('use_adx_filter', v)),
            _sliderRow('ADX Min Value', cfg.adxMinValue, 15.0, 40.0, '',
                (v) => cfg.updateField('adx_min_value', _round1(v))),
            _toggleRow('Spread Filter', cfg.useSpreadFilter,
                (v) => cfg.updateField('use_spread_filter', v)),
            _intRow('Max Spread (pts)', cfg.maxSpreadPoints, 50, 500,
                (v) => cfg.updateField('max_spread_points', v)),
            _toggleRow('Gap Filter', cfg.useGapFilter,
                (v) => cfg.updateField('use_gap_filter', v)),
            _toggleRow('Volatility Filter', cfg.useVolatilityFilter,
                (v) => cfg.updateField('use_volatility_filter', v)),
            _toggleRow('Allow High Vol Trading', cfg.allowHighVolTrading,
                (v) => cfg.updateField('allow_high_volatility_trading', v)),
            _sliderRow('High Vol Risk Factor', cfg.highVolRiskFactor, 0.1, 1.0, 'x',
                (v) => cfg.updateField('high_volatility_risk_factor', _round2(v))),
          ]),
          const SizedBox(height: 8),
          _section('TRADING SCHEDULE', [
            _timeRow('Start', cfg.tradingStartHour, cfg.tradingStartMinute,
                (h, m) {
              cfg.updateField('trading_start_hour', h);
              cfg.updateField('trading_start_minute', m);
            }),
            _timeRow('Stop', cfg.tradingStopHour, cfg.tradingStopMinute,
                (h, m) {
              cfg.updateField('trading_stop_hour', h);
              cfg.updateField('trading_stop_minute', m);
            }),
          ]),
          const SizedBox(height: 12),
          _saveButton(cfg),
          if (cfg.error != null) ...[
            const SizedBox(height: 8),
            Text(cfg.error!, style: monoStyle(fontSize: 9, color: AppColors.red)),
          ],
          const SizedBox(height: 16),
        ],
      ),
    );
  }

  Widget _saveButton(ConfigProvider cfg) {
    return GestureDetector(
      onTap: cfg.isSaving
          ? null
          : () async {
              await cfg.pushConfig();
              if (!mounted) return;
              ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                content: Text(
                  cfg.error != null ? 'ERROR: ${cfg.error}' : 'CONFIGURATION SAVED',
                  style: monoStyle(fontSize: 11, color: Colors.white, fontWeight: FontWeight.bold),
                ),
                backgroundColor: cfg.error != null ? AppColors.red : AppColors.green,
                duration: const Duration(seconds: 2),
              ));
            },
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(vertical: 12),
        decoration: BoxDecoration(
          color: AppColors.cyan.withValues(alpha: 0.12),
          border: Border.all(color: AppColors.cyan),
        ),
        child: Center(
          child: cfg.isSaving
              ? const SizedBox(
                  width: 16, height: 16,
                  child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.cyan))
              : Text('SAVE CONFIGURATION',
                  style: monoStyle(
                      fontSize: 12,
                      color: AppColors.cyan,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 2)),
        ),
      ),
    );
  }

  Widget _section(String title, List<Widget> children) {
    return TerminalCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title,
              style: monoStyle(
                  fontSize: 9,
                  color: AppColors.dimText,
                  letterSpacing: 2)),
          const SizedBox(height: 10),
          ...children,
        ],
      ),
    );
  }

  Widget _toggleRow(String label, bool value, ValueChanged<bool> onChanged) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          Expanded(
            child: Text(label, style: monoStyle(fontSize: 11, color: AppColors.text)),
          ),
          GestureDetector(
            onTap: () => onChanged(!value),
            child: Container(
              width: 40,
              height: 20,
              decoration: BoxDecoration(
                color: value ? AppColors.cyan.withValues(alpha: 0.2) : AppColors.border,
                border: Border.all(
                    color: value ? AppColors.cyan : AppColors.dimText.withValues(alpha: 0.3)),
              ),
              child: AnimatedAlign(
                duration: const Duration(milliseconds: 150),
                alignment: value ? Alignment.centerRight : Alignment.centerLeft,
                child: Container(
                  width: 16, height: 16,
                  margin: const EdgeInsets.symmetric(horizontal: 2),
                  color: value ? AppColors.cyan : AppColors.dimText,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _sliderRow(String label, double value, double min, double max,
      String unit, ValueChanged<double> onChanged) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Column(
        children: [
          Row(
            children: [
              Text(label, style: monoStyle(fontSize: 10, color: AppColors.text)),
              const Spacer(),
              Text('${value.toStringAsFixed(value == value.roundToDouble() ? 1 : 2)}$unit',
                  style: monoStyle(fontSize: 11, color: AppColors.cyan, fontWeight: FontWeight.bold)),
            ],
          ),
          SliderTheme(
            data: SliderThemeData(
              activeTrackColor: AppColors.cyan,
              inactiveTrackColor: AppColors.border,
              thumbColor: AppColors.cyan,
              trackHeight: 2,
              thumbShape: const RoundSliderThumbShape(enabledThumbRadius: 6),
              overlayShape: const RoundSliderOverlayShape(overlayRadius: 12),
            ),
            child: Slider(value: value.clamp(min, max), min: min, max: max, onChanged: onChanged),
          ),
        ],
      ),
    );
  }

  Widget _intRow(String label, int value, int min, int max, ValueChanged<int> onChanged) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          Expanded(
            child: Text(label, style: monoStyle(fontSize: 10, color: AppColors.text)),
          ),
          GestureDetector(
            onTap: value > min ? () => onChanged(value - 1) : null,
            child: Container(
              width: 28, height: 28,
              decoration: BoxDecoration(border: Border.all(color: AppColors.border), color: AppColors.surface),
              child: Icon(Icons.remove, size: 14, color: value > min ? AppColors.cyan : AppColors.border),
            ),
          ),
          Container(
            width: 50, height: 28,
            decoration: BoxDecoration(border: Border.all(color: AppColors.border), color: AppColors.bg),
            child: Center(
              child: Text('$value',
                  style: monoStyle(fontSize: 11, color: AppColors.cyan, fontWeight: FontWeight.bold)),
            ),
          ),
          GestureDetector(
            onTap: value < max ? () => onChanged(value + 1) : null,
            child: Container(
              width: 28, height: 28,
              decoration: BoxDecoration(border: Border.all(color: AppColors.border), color: AppColors.surface),
              child: Icon(Icons.add, size: 14, color: value < max ? AppColors.cyan : AppColors.border),
            ),
          ),
        ],
      ),
    );
  }

  Widget _dropdownRow(String label, String value, List<String> options, ValueChanged<String> onChanged) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          Text(label, style: monoStyle(fontSize: 10, color: AppColors.text)),
          const Spacer(),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8),
            decoration: BoxDecoration(border: Border.all(color: AppColors.border), color: AppColors.bg),
            child: DropdownButtonHideUnderline(
              child: DropdownButton<String>(
                value: options.contains(value) ? value : options.first,
                dropdownColor: AppColors.surface,
                style: monoStyle(fontSize: 10, color: AppColors.cyan, fontWeight: FontWeight.bold),
                iconEnabledColor: AppColors.cyan,
                iconSize: 16,
                items: options
                    .map((o) => DropdownMenuItem(
                        value: o,
                        child: Text(o.toUpperCase(), style: monoStyle(fontSize: 10, color: AppColors.cyan))))
                    .toList(),
                onChanged: (v) {
                  if (v != null) onChanged(v);
                },
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _timeRow(String label, int hour, int minute, void Function(int h, int m) onChanged) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          Text('$label Time', style: monoStyle(fontSize: 10, color: AppColors.text)),
          const Spacer(),
          GestureDetector(
            onTap: () async {
              final picked = await showTimePicker(
                context: context,
                initialTime: TimeOfDay(hour: hour, minute: minute),
                builder: (ctx, child) {
                  return Theme(
                    data: Theme.of(ctx).copyWith(
                      colorScheme: const ColorScheme.dark(
                        primary: AppColors.cyan,
                        surface: AppColors.surface,
                      ),
                    ),
                    child: child!,
                  );
                },
              );
              if (picked != null) {
                onChanged(picked.hour, picked.minute);
              }
            },
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                border: Border.all(color: AppColors.border),
                color: AppColors.bg,
              ),
              child: Text(
                '${hour.toString().padLeft(2, '0')}:${minute.toString().padLeft(2, '0')}',
                style: monoStyle(fontSize: 12, color: AppColors.cyan, fontWeight: FontWeight.bold),
              ),
            ),
          ),
        ],
      ),
    );
  }

  double _round1(double v) => double.parse(v.toStringAsFixed(1));
  double _round2(double v) => double.parse(v.toStringAsFixed(2));
}
