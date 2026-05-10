import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../theme/app_theme.dart';
import '../widgets/terminal_card.dart';
import '../providers/trade_history_provider.dart';
import '../providers/trading_provider.dart';

class TradesScreen extends StatefulWidget {
  const TradesScreen({super.key});

  @override
  State<TradesScreen> createState() => _TradesScreenState();
}

class _TradesScreenState extends State<TradesScreen> {
  String _filter = 'ALL';

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<TradeHistoryProvider>().loadTrades(refresh: true);
    });
  }

  @override
  Widget build(BuildContext context) {
    final historyProvider = context.watch<TradeHistoryProvider>();
    final trading = context.watch<TradingProvider>();
    final trades = historyProvider.trades;

    final filtered = _filter == 'ALL'
        ? trades
        : _filter == 'WIN'
            ? trades.where((t) => (t['profit'] as num? ?? 0) > 0).toList()
            : trades.where((t) => (t['profit'] as num? ?? 0) <= 0).toList();

    return Column(
      children: [
        _summary(trading, trades),
        const SizedBox(height: 8),
        _filterRow(),
        const SizedBox(height: 4),
        Expanded(
          child: historyProvider.isLoading && trades.isEmpty
              ? const Center(
                  child: CircularProgressIndicator(
                      color: AppColors.cyan, strokeWidth: 2))
              : RefreshIndicator(
                  onRefresh: () =>
                      historyProvider.loadTrades(refresh: true),
                  color: AppColors.cyan,
                  child: ListView.separated(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    itemCount: filtered.length + (historyProvider.hasMore ? 1 : 0),
                    separatorBuilder: (_, __) => const SizedBox(height: 6),
                    itemBuilder: (_, i) {
                      if (i >= filtered.length) {
                        historyProvider.loadMore();
                        return const Padding(
                          padding: EdgeInsets.all(16),
                          child: Center(
                            child: CircularProgressIndicator(
                                color: AppColors.cyan, strokeWidth: 2),
                          ),
                        );
                      }
                      return _tradeCard(filtered[i]);
                    },
                  ),
                ),
        ),
      ],
    );
  }

  Widget _summary(TradingProvider trading, List<Map<String, dynamic>> trades) {
    final wins = trades.where((t) => (t['profit'] as num? ?? 0) > 0).length;
    final losses = trades.where((t) => (t['profit'] as num? ?? 0) <= 0).length;
    final netPl = trades.fold<double>(
        0, (sum, t) => sum + ((t['profit'] as num?)?.toDouble() ?? 0));
    final avgWin = wins > 0
        ? trades
                .where((t) => (t['profit'] as num? ?? 0) > 0)
                .fold<double>(0, (s, t) => s + ((t['profit'] as num?)?.toDouble() ?? 0)) /
            wins
        : 0.0;

    return Padding(
      padding: const EdgeInsets.fromLTRB(12, 8, 12, 0),
      child: TerminalCard(
        child: Row(
          children: [
            _summaryCol('TOTAL', '${trades.length}', AppColors.text),
            _summaryCol('WINS', '$wins', AppColors.green),
            _summaryCol('LOSSES', '$losses', AppColors.red),
            _summaryCol('NET P&L',
                '${netPl >= 0 ? "+" : ""}\$${netPl.toStringAsFixed(0)}',
                netPl >= 0 ? AppColors.green : AppColors.red),
            _summaryCol('AVG WIN', '+\$${avgWin.toStringAsFixed(0)}', AppColors.cyan),
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
                          color: active ? AppColors.cyan : AppColors.dimText,
                          fontWeight: active ? FontWeight.bold : FontWeight.normal,
                          letterSpacing: 1)),
                ),
              ),
            ),
          );
        }).toList(),
      ),
    );
  }

  Widget _tradeCard(Map<String, dynamic> trade) {
    final type = (trade['type'] as String?) ?? 'BUY';
    final profit = (trade['profit'] as num?)?.toDouble() ?? 0.0;
    final win = profit > 0;
    final lots = (trade['volume'] as num?)?.toDouble() ?? 0.0;
    final entry = (trade['openPrice'] as num?)?.toDouble() ?? 0.0;
    final exit = (trade['closePrice'] as num?)?.toDouble() ?? 0.0;
    final source = (trade['comment'] as String?) ?? '';
    final time = (trade['closeTime'] as String?) ?? '';

    final typeColor = type.contains('BUY') ? AppColors.green : AppColors.red;

    return TerminalCard(
      child: Column(
        children: [
          Row(
            children: [
              TerminalBadge(
                  label: type.contains('BUY') ? 'BUY' : 'SELL',
                  color: typeColor),
              const SizedBox(width: 8),
              Text('${lots.toStringAsFixed(2)} lots',
                  style: monoStyle(fontSize: 10, color: AppColors.text)),
              const SizedBox(width: 8),
              if (source.isNotEmpty)
                TerminalBadge(label: source.split(' ').first, color: AppColors.cyan),
              const Spacer(),
              Text(time.length >= 16 ? time.substring(11, 16) : time,
                  style: monoStyle(fontSize: 10, color: AppColors.dimText)),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              _tradeDetail('ENTRY', entry.toStringAsFixed(2)),
              _tradeDetail('EXIT', exit.toStringAsFixed(2)),
              _tradeDetail(
                  'P&L',
                  '${win ? "+" : ""}\$${profit.toStringAsFixed(2)}',
                  color: win ? AppColors.green : AppColors.red),
              _tradeDetail(
                  'PIPS',
                  '${((exit - entry).abs() / 0.01).toStringAsFixed(0)}',
                  color: win ? AppColors.green : AppColors.red),
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
