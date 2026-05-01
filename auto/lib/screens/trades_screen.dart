import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../widgets/terminal_card.dart';

class TradesScreen extends StatefulWidget {
  const TradesScreen({super.key});

  @override
  State<TradesScreen> createState() => _TradesScreenState();
}

class _TradesScreenState extends State<TradesScreen> {
  String _filter = 'ALL';

  final _trades = [
    _Trade('14:23', 'BUY', 0.12, 2381.20, 2386.40, 45.20, true, 'SNIPER', 0),
    _Trade('14:18', 'SELL', 0.08, 2389.80, 2391.60, -12.80, false, 'M1', 0),
    _Trade('14:05', 'BUY', 0.15, 2376.50, 2381.70, 78.40, true, 'MICRO_5s', 1),
    _Trade('13:52', 'SELL', 0.10, 2392.10, 2388.30, 38.00, true, 'SNIPER', 0),
    _Trade('13:41', 'BUY', 0.20, 2370.80, 2368.50, -46.00, false, 'M5', 2),
    _Trade('13:30', 'BUY', 0.12, 2368.40, 2374.20, 69.60, true, 'SNIPER', 0),
    _Trade('13:15', 'SELL', 0.08, 2380.50, 2382.10, -12.80, false, 'MICRO_10s', 0),
    _Trade('12:58', 'BUY', 0.15, 2365.20, 2371.80, 99.00, true, 'SNIPER', 1),
    _Trade('12:42', 'SELL', 0.10, 2375.60, 2372.40, 32.00, true, 'M1', 0),
    _Trade('12:30', 'BUY', 0.12, 2362.80, 2360.50, -27.60, false, 'M5', 0),
  ];

  @override
  Widget build(BuildContext context) {
    final filtered = _filter == 'ALL'
        ? _trades
        : _filter == 'WIN'
            ? _trades.where((t) => t.win).toList()
            : _trades.where((t) => !t.win).toList();

    return Column(
      children: [
        _summary(),
        const SizedBox(height: 8),
        _filterRow(),
        const SizedBox(height: 4),
        Expanded(
          child: ListView.separated(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            itemCount: filtered.length,
            separatorBuilder: (_, __) => const SizedBox(height: 6),
            itemBuilder: (_, i) => _tradeCard(filtered[i]),
          ),
        ),
      ],
    );
  }

  Widget _summary() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(12, 8, 12, 0),
      child: TerminalCard(
        child: Row(
          children: [
            _summaryCol('TOTAL', '25', AppColors.text),
            _summaryCol('WINS', '17', AppColors.green),
            _summaryCol('LOSSES', '8', AppColors.red),
            _summaryCol('NET P&L', '+\$847', AppColors.green),
            _summaryCol('AVG WIN', '+\$52', AppColors.cyan),
          ],
        ),
      ),
    );
  }

  Widget _summaryCol(String l, String v, Color c) {
    return Expanded(
      child: Column(
        children: [
          Text(l,
              style: monoStyle(
                  fontSize: 7, color: AppColors.dimText, letterSpacing: 1)),
          const SizedBox(height: 2),
          Text(v,
              style: monoStyle(
                  fontSize: 12, color: c, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }

  Widget _filterRow() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 12),
      child: Row(
        children: ['ALL', 'WIN', 'LOSS'].map((f) {
          final active = _filter == f;
          return Expanded(
            child: GestureDetector(
              onTap: () => setState(() => _filter = f),
              child: Container(
                margin: EdgeInsets.only(right: f != 'LOSS' ? 4 : 0),
                padding: const EdgeInsets.symmetric(vertical: 6),
                decoration: BoxDecoration(
                  color: active
                      ? AppColors.cyan.withValues(alpha: 0.12)
                      : AppColors.surface,
                  border: Border.all(
                      color: active
                          ? AppColors.cyan.withValues(alpha: 0.5)
                          : AppColors.border),
                ),
                child: Center(
                  child: Text(f,
                      style: monoStyle(
                          fontSize: 10,
                          color:
                              active ? AppColors.cyan : AppColors.dimText,
                          fontWeight: active
                              ? FontWeight.bold
                              : FontWeight.normal,
                          letterSpacing: 1)),
                ),
              ),
            ),
          );
        }).toList(),
      ),
    );
  }

  Widget _tradeCard(_Trade tr) {
    final typeColor = tr.type == 'BUY' ? AppColors.green : AppColors.red;
    return TerminalCard(
      child: Column(
        children: [
          Row(
            children: [
              TerminalBadge(label: tr.type, color: typeColor),
              const SizedBox(width: 8),
              Text('${tr.lots} lots',
                  style: monoStyle(fontSize: 10, color: AppColors.text)),
              const SizedBox(width: 8),
              TerminalBadge(label: tr.source, color: AppColors.cyan),
              if (tr.gridIdx > 0) ...[
                const SizedBox(width: 4),
                TerminalBadge(
                    label: 'GRID #${tr.gridIdx}', color: AppColors.amber),
              ],
              const Spacer(),
              Text(tr.time,
                  style: monoStyle(fontSize: 10, color: AppColors.dimText)),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              _tradeDetail('ENTRY', tr.entry.toStringAsFixed(2)),
              _tradeDetail('EXIT', tr.exit.toStringAsFixed(2)),
              _tradeDetail(
                  'P&L',
                  '${tr.win ? "+" : ""}\$${tr.pnl.toStringAsFixed(2)}',
                  color: tr.win ? AppColors.green : AppColors.red),
              _tradeDetail(
                  'PIPS',
                  '${((tr.exit - tr.entry) * 10).abs().toStringAsFixed(1)}',
                  color: tr.win ? AppColors.green : AppColors.red),
            ],
          ),
        ],
      ),
    );
  }

  Widget _tradeDetail(String l, String v, {Color? color}) {
    return Expanded(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(l, style: monoStyle(fontSize: 8, color: AppColors.dimText)),
          Text(v,
              style: monoStyle(
                  fontSize: 11,
                  color: color ?? AppColors.text,
                  fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }
}

class _Trade {
  final String time, type, source;
  final double lots, entry, exit, pnl;
  final bool win;
  final int gridIdx;

  _Trade(this.time, this.type, this.lots, this.entry, this.exit, this.pnl,
      this.win, this.source, this.gridIdx);
}
