import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../widgets/terminal_card.dart';

class ConfigScreen extends StatefulWidget {
  const ConfigScreen({super.key});

  @override
  State<ConfigScreen> createState() => _ConfigScreenState();
}

class _ConfigScreenState extends State<ConfigScreen> {
  double _risk = 0.5;
  String _slMethod = 'hybrid';
  bool _sniperAi = true;
  int _sniperMin = 70;
  bool _microTf = true;
  int _maxPosPerDir = 1;
  int _maxTotalPos = 2;
  bool _hedging = false;
  bool _tradingEnabled = true;
  int _maxTradesPerDay = 500;
  double _maxDailyLoss = 3.0;
  int _maxConsLosses = 8;
  TimeOfDay _startTime = const TimeOfDay(hour: 8, minute: 0);
  TimeOfDay _stopTime = const TimeOfDay(hour: 22, minute: 0);

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      child: Column(
        children: [
          _section('TRADING ENGINE', [
            _toggleRow('Trading Enabled', _tradingEnabled,
                (v) => setState(() => _tradingEnabled = v)),
          ]),
          const SizedBox(height: 8),
          _section('RISK MANAGEMENT', [
            _sliderRow('Risk per Trade', _risk, 0.1, 2.0, '%',
                (v) => setState(() => _risk = v)),
            _sliderRow('Max Daily Loss', _maxDailyLoss, 1.0, 10.0, '%',
                (v) => setState(() => _maxDailyLoss = v)),
            _intRow('Max Consec. Losses', _maxConsLosses, 3, 15,
                (v) => setState(() => _maxConsLosses = v)),
            _intRow('Max Trades/Day', _maxTradesPerDay, 10, 1000,
                (v) => setState(() => _maxTradesPerDay = v)),
          ]),
          const SizedBox(height: 8),
          _section('STOP LOSS', [
            _dropdownRow('SL Method', _slMethod,
                ['hybrid', 'atr', 'swings', 'sr', 'fixed'],
                (v) => setState(() => _slMethod = v)),
          ]),
          const SizedBox(height: 8),
          _section('SNIPER AI', [
            _toggleRow('Sniper AI Enabled', _sniperAi,
                (v) => setState(() => _sniperAi = v)),
            _intRow('Min Score', _sniperMin, 50, 95,
                (v) => setState(() => _sniperMin = v)),
          ]),
          const SizedBox(height: 8),
          _section('MICRO TIMEFRAMES', [
            _toggleRow('Micro TF Enabled', _microTf,
                (v) => setState(() => _microTf = v)),
          ]),
          const SizedBox(height: 8),
          _section('POSITIONS', [
            _intRow('Max per Direction', _maxPosPerDir, 1, 5,
                (v) => setState(() => _maxPosPerDir = v)),
            _intRow('Max Total', _maxTotalPos, 1, 10,
                (v) => setState(() => _maxTotalPos = v)),
            _toggleRow('Allow Hedging', _hedging,
                (v) => setState(() => _hedging = v)),
          ]),
          const SizedBox(height: 8),
          _section('SCHEDULE', [
            _timeRow('Start Time', _startTime,
                (t) => setState(() => _startTime = t)),
            _timeRow('Stop Time', _stopTime,
                (t) => setState(() => _stopTime = t)),
          ]),
          const SizedBox(height: 8),
          _saveButton(),
          const SizedBox(height: 16),
        ],
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
          Text(label,
              style: monoStyle(fontSize: 11, color: AppColors.text)),
          const Spacer(),
          GestureDetector(
            onTap: () => onChanged(!value),
            child: Container(
              width: 40,
              height: 20,
              decoration: BoxDecoration(
                color: value
                    ? AppColors.cyan.withValues(alpha: 0.2)
                    : AppColors.border,
                border: Border.all(
                    color: value
                        ? AppColors.cyan
                        : AppColors.dimText.withValues(alpha: 0.3)),
              ),
              child: AnimatedAlign(
                duration: const Duration(milliseconds: 150),
                alignment:
                    value ? Alignment.centerRight : Alignment.centerLeft,
                child: Container(
                  width: 16,
                  height: 16,
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
              Text(label,
                  style: monoStyle(fontSize: 10, color: AppColors.text)),
              const Spacer(),
              Text('${value.toStringAsFixed(1)}$unit',
                  style: monoStyle(
                      fontSize: 11,
                      color: AppColors.cyan,
                      fontWeight: FontWeight.bold)),
            ],
          ),
          SliderTheme(
            data: SliderThemeData(
              activeTrackColor: AppColors.cyan,
              inactiveTrackColor: AppColors.border,
              thumbColor: AppColors.cyan,
              trackHeight: 2,
              thumbShape: const RoundSliderThumbShape(enabledThumbRadius: 6),
              overlayShape:
                  const RoundSliderOverlayShape(overlayRadius: 12),
            ),
            child: Slider(
              value: value,
              min: min,
              max: max,
              onChanged: onChanged,
            ),
          ),
        ],
      ),
    );
  }

  Widget _intRow(
      String label, int value, int min, int max, ValueChanged<int> onChanged) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          Text(label,
              style: monoStyle(fontSize: 10, color: AppColors.text)),
          const Spacer(),
          GestureDetector(
            onTap: value > min ? () => onChanged(value - 1) : null,
            child: Container(
              width: 28,
              height: 28,
              decoration: BoxDecoration(
                border: Border.all(color: AppColors.border),
                color: AppColors.surface,
              ),
              child: Icon(Icons.remove,
                  size: 14,
                  color: value > min ? AppColors.cyan : AppColors.border),
            ),
          ),
          Container(
            width: 50,
            height: 28,
            decoration: BoxDecoration(
              border: Border.all(color: AppColors.border),
              color: AppColors.bg,
            ),
            child: Center(
              child: Text('$value',
                  style: monoStyle(
                      fontSize: 11,
                      color: AppColors.cyan,
                      fontWeight: FontWeight.bold)),
            ),
          ),
          GestureDetector(
            onTap: value < max ? () => onChanged(value + 1) : null,
            child: Container(
              width: 28,
              height: 28,
              decoration: BoxDecoration(
                border: Border.all(color: AppColors.border),
                color: AppColors.surface,
              ),
              child: Icon(Icons.add,
                  size: 14,
                  color: value < max ? AppColors.cyan : AppColors.border),
            ),
          ),
        ],
      ),
    );
  }

  Widget _dropdownRow(String label, String value, List<String> options,
      ValueChanged<String> onChanged) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          Text(label,
              style: monoStyle(fontSize: 10, color: AppColors.text)),
          const Spacer(),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8),
            decoration: BoxDecoration(
              border: Border.all(color: AppColors.border),
              color: AppColors.bg,
            ),
            child: DropdownButtonHideUnderline(
              child: DropdownButton<String>(
                value: value,
                dropdownColor: AppColors.surface,
                style: monoStyle(
                    fontSize: 10,
                    color: AppColors.cyan,
                    fontWeight: FontWeight.bold),
                iconEnabledColor: AppColors.cyan,
                iconSize: 16,
                items: options
                    .map((o) => DropdownMenuItem(
                        value: o,
                        child: Text(o.toUpperCase(),
                            style: monoStyle(
                                fontSize: 10, color: AppColors.cyan))))
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

  Widget _timeRow(
      String label, TimeOfDay value, ValueChanged<TimeOfDay> onChanged) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          Text(label,
              style: monoStyle(fontSize: 10, color: AppColors.text)),
          const Spacer(),
          GestureDetector(
            onTap: () async {
              final picked = await showTimePicker(
                context: context,
                initialTime: value,
                builder: (ctx, child) {
                  return Theme(
                    data: ThemeData.dark().copyWith(
                      colorScheme: const ColorScheme.dark(
                        primary: AppColors.cyan,
                        surface: AppColors.surface,
                      ),
                    ),
                    child: child!,
                  );
                },
              );
              if (picked != null) onChanged(picked);
            },
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
              decoration: BoxDecoration(
                border: Border.all(color: AppColors.border),
                color: AppColors.bg,
              ),
              child: Text(
                '${value.hour.toString().padLeft(2, '0')}:${value.minute.toString().padLeft(2, '0')} UTC',
                style: monoStyle(
                    fontSize: 11,
                    color: AppColors.cyan,
                    fontWeight: FontWeight.bold),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _saveButton() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 12),
      decoration: BoxDecoration(
        color: AppColors.cyan.withValues(alpha: 0.12),
        border: Border.all(color: AppColors.cyan),
      ),
      child: Center(
        child: Text('SAVE CONFIGURATION',
            style: monoStyle(
                fontSize: 12,
                color: AppColors.cyan,
                fontWeight: FontWeight.bold,
                letterSpacing: 2)),
      ),
    );
  }
}
