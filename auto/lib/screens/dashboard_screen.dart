import 'package:flutter/material.dart';
import 'dart:math';
import 'package:provider/provider.dart';
import '../theme/app_theme.dart';
import '../widgets/terminal_card.dart';
import '../providers/trading_provider.dart';
import '../providers/market_provider.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen>
    with TickerProviderStateMixin {
  late AnimationController _pulse;
  late AnimationController _priceFlash;

  @override
  void initState() {
    super.initState();
    _pulse = AnimationController(
        vsync: this, duration: const Duration(seconds: 2))
      ..repeat(reverse: true);
    _priceFlash = AnimationController(
        vsync: this, duration: const Duration(milliseconds: 300));
  }

  @override
  void dispose() {
    _pulse.dispose();
    _priceFlash.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      child: Column(
        children: [
          _statusBar(),
          const SizedBox(height: 8),
          _marketTicker(),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(child: _pnlCard()),
              const SizedBox(width: 8),
              Expanded(child: _accountCard()),
            ],
          ),
          const SizedBox(height: 8),
          _sniperPanel(),
          const SizedBox(height: 8),
          _positions(),
          const SizedBox(height: 8),
          _controls(),
          const SizedBox(height: 16),
        ],
      ),
    );
  }

  Widget _statusBar() {
    final trading = context.watch<TradingProvider>();
    final isRunning = trading.engineStatus == EngineStatus.running;
    final statusColor = isRunning ? AppColors.green : AppColors.red;
    final statusText = trading.engineStatus.name.toUpperCase();

    return AnimatedBuilder(
      animation: _pulse,
      builder: (_, __) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        decoration: BoxDecoration(
          color: statusColor.withValues(alpha: 0.08),
          border: Border.all(color: statusColor.withValues(alpha: 0.3)),
        ),
        child: Row(
          children: [
            Container(
              width: 8,
              height: 8,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: statusColor
                    .withValues(alpha: isRunning ? 0.5 + _pulse.value * 0.5 : 0.5),
                boxShadow: [
                  BoxShadow(
                      color: statusColor.withValues(alpha: 0.4),
                      blurRadius: 8),
                ],
              ),
            ),
            const SizedBox(width: 8),
            Text('ENGINE $statusText',
                style: monoStyle(
                    fontSize: 11,
                    color: statusColor,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 1)),
            const Spacer(),
            if (trading.adaptiveSafeMode)
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                color: AppColors.amber.withValues(alpha: 0.2),
                child: Text('SAFE MODE',
                    style: monoStyle(fontSize: 9, color: AppColors.amber, fontWeight: FontWeight.bold)),
              ),
            const SizedBox(width: 8),
            Text('${trading.regime}',
                style: monoStyle(
                    fontSize: 10,
                    color: statusColor.withValues(alpha: 0.7))),
          ],
        ),
      ),
    );
  }

  Widget _marketTicker() {
    final market = context.watch<MarketProvider>();
    final bid = market.bid;
    final ask = market.ask;
    final spread = market.spread;
    final priceUp = bid >= market.prevBid;
    final flashColor = priceUp ? AppColors.green : AppColors.red;

    return TerminalCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text('XAUUSD',
                  style: monoStyle(
                      fontSize: 10,
                      color: AppColors.dimText,
                      letterSpacing: 2)),
              const SizedBox(width: 8),
              TerminalBadge(label: 'GOLD', color: AppColors.amber),
              const Spacer(),
              Container(
                width: 8,
                height: 8,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: bid > 0 ? AppColors.green : AppColors.red,
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 2),
                child: Text(
                  bid > 0 ? bid.toStringAsFixed(0) : '---',
                  style: monoStyle(
                      fontSize: 32,
                      color: Colors.white,
                      fontWeight: FontWeight.w300),
                ),
              ),
              if (bid > 0)
                Text(
                  '.${((bid * 100) % 100).toInt().toString().padLeft(2, '0')}',
                  style: monoStyle(
                      fontSize: 22,
                      color: flashColor,
                      fontWeight: FontWeight.bold),
                ),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              _stat('BID', bid > 0 ? bid.toStringAsFixed(2) : '--'),
              _stat('ASK', ask > 0 ? ask.toStringAsFixed(2) : '--'),
              _stat('SPREAD', spread > 0 ? spread.toStringAsFixed(2) : '--'),
              _stat('ATR', market.atr > 0 ? market.atr.toStringAsFixed(1) : '--'),
              _stat('VOL', market.volatilityStatus, highlight: market.volatilityStatus == 'HIGH'),
            ],
          ),
        ],
      ),
    );
  }

  Widget _stat(String l, String v, {bool highlight = false}) {
    return Expanded(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(l,
              style: monoStyle(
                  fontSize: 9,
                  color: AppColors.dimText,
                  letterSpacing: 1)),
          const SizedBox(height: 2),
          Text(v,
              style: monoStyle(
                  fontSize: 11,
                  color: highlight ? AppColors.amber : AppColors.text,
                  fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }

  Widget _pnlCard() {
    final trading = context.watch<TradingProvider>();
    final pnl = trading.pnlToday + trading.floatingPl;
    final realized = trading.pnlToday;
    final floating = trading.floatingPl;

    return TerminalCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('P&L TODAY',
              style: monoStyle(
                  fontSize: 9,
                  color: AppColors.dimText,
                  letterSpacing: 2)),
          const SizedBox(height: 6),
          Text(
              '${pnl >= 0 ? "+" : ""}\$${pnl.toStringAsFixed(2)}',
              style: monoStyle(
                  fontSize: 22,
                  color: pnl >= 0 ? AppColors.green : AppColors.red,
                  fontWeight: FontWeight.bold)),
          const SizedBox(height: 4),
          Row(
            children: [
              _mini('Realized',
                  '${realized >= 0 ? "+" : ""}\$${realized.toStringAsFixed(0)}', AppColors.green),
              const SizedBox(width: 8),
              _mini('Float',
                  '${floating >= 0 ? "+" : ""}\$${floating.toStringAsFixed(0)}',
                  AppColors.cyan),
            ],
          ),
          const SizedBox(height: 8),
          MiniBar(
              ratio: trading.tradesToday > 0 ? trading.winRate / 100 : 0,
              color: AppColors.green),
          const SizedBox(height: 4),
          Text(
              'Win Rate ${trading.winRate.toStringAsFixed(0)}% (${trading.tradesToday} trades)',
              style: monoStyle(fontSize: 9, color: AppColors.dimText)),
        ],
      ),
    );
  }

  Widget _accountCard() {
    final trading = context.watch<TradingProvider>();

    return TerminalCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('ACCOUNT',
              style: monoStyle(
                  fontSize: 9,
                  color: AppColors.dimText,
                  letterSpacing: 2)),
          const SizedBox(height: 6),
          Text(
              '\$${trading.balance.toStringAsFixed(2)}',
              style: monoStyle(
                  fontSize: 22,
                  color: Colors.white,
                  fontWeight: FontWeight.bold)),
          const SizedBox(height: 4),
          Row(
            children: [
              _mini('Equity', '\$${trading.equity.toStringAsFixed(0)}',
                  AppColors.text),
              const SizedBox(width: 8),
              _mini('Losses', '${trading.consecutiveLosses}', AppColors.amber),
            ],
          ),
          const SizedBox(height: 8),
          MiniBar(
              ratio: trading.balance > 0
                  ? (trading.pnlToday.abs() / (trading.balance * 0.03)).clamp(0, 1)
                  : 0,
              color: AppColors.amber),
          const SizedBox(height: 4),
          Text(
              'Daily Loss ${trading.balance > 0 ? (trading.pnlToday.abs() / trading.balance * 100).toStringAsFixed(1) : "0.0"}% / 3.0% max',
              style: monoStyle(fontSize: 9, color: AppColors.dimText)),
        ],
      ),
    );
  }

  Widget _mini(String l, String v, Color c) {
    return Expanded(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(l, style: monoStyle(fontSize: 8, color: AppColors.dimText)),
          Text(v,
              style: monoStyle(
                  fontSize: 11, color: c, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }

  Widget _sniperPanel() {
    final trading = context.watch<TradingProvider>();
    final score = trading.sniperScore;

    Color scoreColor;
    if (score >= 80) {
      scoreColor = AppColors.green;
    } else if (score >= 65) {
      scoreColor = AppColors.cyan;
    } else if (score >= 57) {
      scoreColor = AppColors.amber;
    } else {
      scoreColor = AppColors.dimText;
    }

    return TerminalCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text('SNIPER AI',
                  style: monoStyle(
                      fontSize: 9,
                      color: AppColors.dimText,
                      letterSpacing: 2)),
              const SizedBox(width: 8),
              TerminalBadge(
                  label: trading.sniperDirection,
                  color: trading.sniperDirection == 'BUY'
                      ? AppColors.green
                      : trading.sniperDirection == 'SELL'
                          ? AppColors.red
                          : AppColors.dimText),
            ],
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              SizedBox(
                width: 60,
                height: 60,
                child: CustomPaint(
                  painter: _ArcPainter(score.toInt(), scoreColor),
                  child: Center(
                    child: Text('${score.toInt()}',
                        style: monoStyle(
                            fontSize: 20,
                            color: scoreColor,
                            fontWeight: FontWeight.bold)),
                  ),
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  children: [
                    _infoRow('Regime', trading.regime, AppColors.cyan),
                    const SizedBox(height: 4),
                    _infoRow('Confidence', '${trading.regimeConfidence.toStringAsFixed(0)}%', AppColors.green),
                    const SizedBox(height: 4),
                    _infoRow('Threshold', '${trading.adaptiveThreshold.toInt()}', AppColors.amber),
                    const SizedBox(height: 4),
                    _infoRow('Volatility', trading.highVolatilityMode ? 'HIGH' : 'NORMAL',
                        trading.highVolatilityMode ? AppColors.red : AppColors.dimText),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _infoRow(String l, String v, Color c) {
    return Row(
      children: [
        SizedBox(
            width: 80,
            child: Text(l,
                style: monoStyle(fontSize: 9, color: AppColors.dimText))),
        Expanded(
          child: Text(v,
              style: monoStyle(
                  fontSize: 10, color: c, fontWeight: FontWeight.bold)),
        ),
      ],
    );
  }

  Widget _positions() {
    final trading = context.watch<TradingProvider>();
    final positions = trading.positions;

    return Container(
      decoration: BoxDecoration(
        color: AppColors.surface,
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        children: [
          TerminalSectionHeader(
            title: 'POSITIONS',
            trailing: TerminalBadge(
                label: '${positions.length} OPEN', color: AppColors.cyan),
          ),
          if (positions.isEmpty)
            Padding(
              padding: const EdgeInsets.all(16),
              child: Text('No open positions',
                  style: monoStyle(fontSize: 10, color: AppColors.dimText)),
            ),
          ...positions.map((pos) {
            final isBuy = pos['type'] == 'POSITION_TYPE_BUY';
            final pnl = (pos['profit'] as num?)?.toDouble() ?? 0.0;
            final volume = (pos['volume'] as num?)?.toDouble() ?? 0.0;
            final openPrice = (pos['openPrice'] as num?)?.toDouble() ?? 0.0;
            final sl = (pos['stopLoss'] as num?)?.toDouble() ?? 0.0;

            return Column(
              children: [
                _posRow(
                  isBuy ? 'BUY' : 'SELL',
                  volume.toStringAsFixed(2),
                  openPrice.toStringAsFixed(2),
                  sl > 0 ? sl.toStringAsFixed(2) : '--',
                  pnl,
                  isBuy ? AppColors.green : AppColors.red,
                ),
                Container(height: 1, color: AppColors.border),
              ],
            );
          }),
        ],
      ),
    );
  }

  Widget _posRow(String type, String lots, String entry, String sl,
      double pnl, Color c) {
    final pnlColor = pnl >= 0 ? AppColors.green : AppColors.red;
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      child: Row(
        children: [
          TerminalBadge(label: type, color: c),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('$lots lots @ $entry',
                    style: monoStyle(fontSize: 10, color: AppColors.text)),
                Text('SL: $sl',
                    style: monoStyle(fontSize: 9, color: AppColors.dimText)),
              ],
            ),
          ),
          Text(
              '${pnl >= 0 ? "+" : ""}\$${pnl.toStringAsFixed(2)}',
              style: monoStyle(
                  fontSize: 12,
                  color: pnlColor,
                  fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }

  Widget _controls() {
    final trading = context.watch<TradingProvider>();
    final isRunning = trading.engineStatus == EngineStatus.running;

    return TerminalCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('CONTROLS',
              style: monoStyle(
                  fontSize: 9,
                  color: AppColors.dimText,
                  letterSpacing: 2)),
          const SizedBox(height: 10),
          Row(
            children: [
              Expanded(
                child: GestureDetector(
                  onTap: isRunning
                      ? () => trading.stopEngine()
                      : () => trading.startEngine(),
                  child: TerminalButton(
                    label: isRunning ? 'STOP ENGINE' : 'START ENGINE',
                    color: isRunning ? AppColors.red : AppColors.green,
                    icon: isRunning ? Icons.stop : Icons.play_arrow,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          GestureDetector(
            onTap: () => _confirmEmergencyStop(context, trading),
            child: Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(vertical: 14),
              decoration: BoxDecoration(
                color: AppColors.red.withValues(alpha: 0.1),
                border: Border.all(color: AppColors.red, width: 2),
              ),
              child: Center(
                child: Text('EMERGENCY STOP',
                    style: monoStyle(
                        fontSize: 13,
                        color: AppColors.red,
                        fontWeight: FontWeight.w900,
                        letterSpacing: 3)),
              ),
            ),
          ),
        ],
      ),
    );
  }

  void _confirmEmergencyStop(BuildContext context, TradingProvider trading) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.surface,
        title: Text('EMERGENCY STOP',
            style: monoStyle(fontSize: 14, color: AppColors.red, fontWeight: FontWeight.bold)),
        content: Text(
            'Close ALL positions and stop the engine immediately?',
            style: monoStyle(fontSize: 11, color: AppColors.text)),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: Text('CANCEL', style: monoStyle(fontSize: 11, color: AppColors.dimText)),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(ctx);
              trading.emergencyStop();
            },
            child: Text('CONFIRM', style: monoStyle(fontSize: 11, color: AppColors.red, fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );
  }
}

class _ArcPainter extends CustomPainter {
  final int score;
  final Color color;
  _ArcPainter(this.score, this.color);

  @override
  void paint(Canvas canvas, Size size) {
    final c = Offset(size.width / 2, size.height / 2);
    final r = size.width / 2 - 4;
    canvas.drawArc(Rect.fromCircle(center: c, radius: r), -pi / 2, 2 * pi,
        false, Paint()..color = AppColors.border..style = PaintingStyle.stroke..strokeWidth = 4);
    canvas.drawArc(Rect.fromCircle(center: c, radius: r), -pi / 2,
        2 * pi * (score / 100), false,
        Paint()..color = color..style = PaintingStyle.stroke..strokeWidth = 4..strokeCap = StrokeCap.round);
  }

  @override
  bool shouldRepaint(covariant CustomPainter old) => true;
}
