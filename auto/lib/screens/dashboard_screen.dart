import 'package:flutter/material.dart';
import 'dart:math';
import 'dart:async';
import '../theme/app_theme.dart';
import '../widgets/terminal_card.dart';

class DashboardScreen extends StatefulWidget {
  final Stream<Map<String, dynamic>>? priceStream;
  const DashboardScreen({super.key, this.priceStream});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen>
    with TickerProviderStateMixin {
  late AnimationController _pulse;
  late AnimationController _priceFlash;
  late Timer _tickTimer;
  final _rng = Random();

  double _price = 2387.45;
  double _prevPrice = 2387.45;
  double _bid = 2387.42;
  double _ask = 2387.48;
  double _dayChange = 12.30;
  double _dayPct = 0.52;
  double _pnl = 847.20;
  double _realized = 623.00;
  double _floating = 224.20;
  double _balance = 12847.20;
  double _equity = 13071.40;
  int _wins = 17;
  int _total = 25;
  int _sniperScore = 82;
  double _pos1Pnl = 93.75;
  double _pos2Pnl = 130.45;

  @override
  void initState() {
    super.initState();
    _pulse = AnimationController(
        vsync: this, duration: const Duration(seconds: 2))
      ..repeat(reverse: true);
    _priceFlash = AnimationController(
        vsync: this, duration: const Duration(milliseconds: 300));

    _tickTimer = Timer.periodic(const Duration(milliseconds: 800), (_) {
      _simulateTick();
    });
  }

  void _simulateTick() {
    setState(() {
      _prevPrice = _price;
      final delta = (_rng.nextDouble() - 0.48) * 1.2;
      _price = (_price + delta);
      _bid = _price - 0.03;
      _ask = _price + 0.03;
      _dayChange += delta * 0.1;
      _dayPct = _dayChange / _price * 100;

      _floating += delta * 0.5;
      _pnl = _realized + _floating;
      _equity = _balance + _floating;

      _pos1Pnl += (_rng.nextDouble() - 0.45) * 2;
      _pos2Pnl += (_rng.nextDouble() - 0.45) * 2;

      _sniperScore = (_sniperScore + (_rng.nextInt(5) - 2)).clamp(60, 98);
    });
    _priceFlash.forward(from: 0);
  }

  @override
  void dispose() {
    _pulse.dispose();
    _priceFlash.dispose();
    _tickTimer.cancel();
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
          const SizedBox(height: 8),
          _history(),
          const SizedBox(height: 16),
        ],
      ),
    );
  }

  Widget _statusBar() {
    return AnimatedBuilder(
      animation: _pulse,
      builder: (_, __) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        decoration: BoxDecoration(
          color: AppColors.green.withValues(alpha: 0.08),
          border: Border.all(color: AppColors.green.withValues(alpha: 0.3)),
        ),
        child: Row(
          children: [
            Container(
              width: 8,
              height: 8,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: AppColors.green
                    .withValues(alpha: 0.5 + _pulse.value * 0.5),
                boxShadow: [
                  BoxShadow(
                      color: AppColors.green.withValues(alpha: 0.4),
                      blurRadius: 8),
                ],
              ),
            ),
            const SizedBox(width: 8),
            Text('ENGINE RUNNING',
                style: monoStyle(
                    fontSize: 11,
                    color: AppColors.green,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 1)),
            const Spacer(),
            Text('UPTIME 14h 32m',
                style: monoStyle(
                    fontSize: 10,
                    color: AppColors.green.withValues(alpha: 0.7))),
            const SizedBox(width: 12),
            Text('LAT 2.1ms',
                style: monoStyle(
                    fontSize: 10,
                    color: AppColors.green.withValues(alpha: 0.7))),
          ],
        ),
      ),
    );
  }

  Widget _marketTicker() {
    final priceUp = _price >= _prevPrice;
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
              AnimatedBuilder(
                animation: _priceFlash,
                builder: (_, __) => Container(
                  width: 8,
                  height: 8,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: flashColor
                        .withValues(alpha: 1.0 - _priceFlash.value),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              AnimatedBuilder(
                animation: _priceFlash,
                builder: (_, __) {
                  final bgAlpha = (1.0 - _priceFlash.value) * 0.15;
                  return Container(
                    color: flashColor.withValues(alpha: bgAlpha),
                    padding: const EdgeInsets.symmetric(horizontal: 2),
                    child: Text(
                      _price.toStringAsFixed(0).replaceAllMapped(
                          RegExp(r'(\d{1,3})(?=(\d{3})+(?!\d))'),
                          (m) => '${m[1]},'),
                      style: monoStyle(
                          fontSize: 32,
                          color: Colors.white,
                          fontWeight: FontWeight.w300),
                    ),
                  );
                },
              ),
              AnimatedBuilder(
                animation: _priceFlash,
                builder: (_, __) {
                  final bgAlpha = (1.0 - _priceFlash.value) * 0.2;
                  return Container(
                    color: flashColor.withValues(alpha: bgAlpha),
                    padding: const EdgeInsets.symmetric(horizontal: 1),
                    child: Text(
                      '.${(_price * 100 % 100).toInt().toString().padLeft(2, '0')}',
                      style: monoStyle(
                          fontSize: 22,
                          color: AppColors.cyan,
                          fontWeight: FontWeight.bold),
                    ),
                  );
                },
              ),
              const SizedBox(width: 12),
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                color: (_dayChange >= 0 ? AppColors.green : AppColors.red)
                    .withValues(alpha: 0.15),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                        _dayChange >= 0
                            ? Icons.arrow_drop_up
                            : Icons.arrow_drop_down,
                        color: _dayChange >= 0
                            ? AppColors.green
                            : AppColors.red,
                        size: 16),
                    Text(
                        '${_dayChange >= 0 ? "+" : ""}${_dayChange.toStringAsFixed(2)} (${_dayPct.toStringAsFixed(2)}%)',
                        style: monoStyle(
                            fontSize: 11,
                            color: _dayChange >= 0
                                ? AppColors.green
                                : AppColors.red)),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              _stat('BID', _bid.toStringAsFixed(2)),
              _stat('ASK', _ask.toStringAsFixed(2)),
              _stat('SPREAD', (_ask - _bid).toStringAsFixed(2)),
              _stat('ATR(14)', '18.4'),
              _stat('VOL', 'HIGH', highlight: true),
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
          TweenAnimationBuilder<double>(
            tween: Tween(end: _pnl),
            duration: const Duration(milliseconds: 500),
            builder: (_, val, __) => Text(
                '${val >= 0 ? "+" : ""}\$${val.toStringAsFixed(2)}',
                style: monoStyle(
                    fontSize: 22,
                    color: val >= 0 ? AppColors.green : AppColors.red,
                    fontWeight: FontWeight.bold)),
          ),
          const SizedBox(height: 4),
          Row(
            children: [
              _mini('Realized',
                  '+\$${_realized.toStringAsFixed(0)}', AppColors.green),
              const SizedBox(width: 8),
              _mini('Float',
                  '${_floating >= 0 ? "+" : ""}\$${_floating.toStringAsFixed(0)}',
                  AppColors.cyan),
            ],
          ),
          const SizedBox(height: 8),
          MiniBar(
              ratio: _wins / _total, color: AppColors.green),
          const SizedBox(height: 4),
          Text('Win Rate ${(_wins / _total * 100).toInt()}% ($_wins/$_total)',
              style: monoStyle(fontSize: 9, color: AppColors.dimText)),
        ],
      ),
    );
  }

  Widget _accountCard() {
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
          TweenAnimationBuilder<double>(
            tween: Tween(end: _balance),
            duration: const Duration(milliseconds: 500),
            builder: (_, val, __) => Text(
                '\$${val.toStringAsFixed(2)}',
                style: monoStyle(
                    fontSize: 22,
                    color: Colors.white,
                    fontWeight: FontWeight.bold)),
          ),
          const SizedBox(height: 4),
          Row(
            children: [
              _mini('Equity', '\$${_equity.toStringAsFixed(0)}',
                  AppColors.text),
              const SizedBox(width: 8),
              _mini('Margin', '\$1,240', AppColors.amber),
            ],
          ),
          const SizedBox(height: 8),
          const MiniBar(ratio: 0.32, color: AppColors.amber),
          const SizedBox(height: 4),
          Text('Daily Loss 0.8% / 3.0% max',
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
              TerminalBadge(label: 'ACTIVE', color: AppColors.cyan),
            ],
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              TweenAnimationBuilder<double>(
                tween: Tween(end: _sniperScore.toDouble()),
                duration: const Duration(milliseconds: 600),
                curve: Curves.easeOut,
                builder: (_, val, __) => SizedBox(
                  width: 60,
                  height: 60,
                  child: CustomPaint(
                    painter: _ArcPainter(val.toInt(), AppColors.cyan),
                    child: Center(
                      child: Text('${val.toInt()}',
                          style: monoStyle(
                              fontSize: 20,
                              color: AppColors.cyan,
                              fontWeight: FontWeight.bold)),
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  children: [
                    _sniperRow('Momentum', 0.78, AppColors.cyan),
                    const SizedBox(height: 4),
                    _sniperRow('Acceleration', 0.65, AppColors.green),
                    const SizedBox(height: 4),
                    _sniperRow('RSI Signal', 0.91, AppColors.amber),
                    const SizedBox(height: 4),
                    _sniperRow('Volume', 0.54, AppColors.dimText),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            color: AppColors.cyan.withValues(alpha: 0.08),
            child: Row(
              children: [
                const Icon(Icons.trending_up, color: AppColors.cyan, size: 14),
                const SizedBox(width: 6),
                Text('Signal: BUY  |  Confluence: 4/5  |  Micro-TF: BULLISH',
                    style: monoStyle(fontSize: 9, color: AppColors.cyan)),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _sniperRow(String l, double v, Color c) {
    return Row(
      children: [
        SizedBox(
            width: 80,
            child: Text(l,
                style: monoStyle(fontSize: 9, color: AppColors.dimText))),
        Expanded(child: MiniBar(ratio: v, color: c)),
        const SizedBox(width: 8),
        Text('${(v * 100).toInt()}',
            style: monoStyle(
                fontSize: 10, color: c, fontWeight: FontWeight.bold)),
      ],
    );
  }

  Widget _positions() {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.surface,
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        children: [
          TerminalSectionHeader(
            title: 'POSITIONS',
            trailing: TerminalBadge(label: '2 OPEN', color: AppColors.cyan),
          ),
          _posRow('BUY', '0.15', '2,381.20', '2,378.50', _pos1Pnl,
              AppColors.green, 'SNIPER'),
          Container(height: 1, color: AppColors.border),
          _posRow('SELL', '0.10', '2,389.80', '2,392.10', _pos2Pnl,
              AppColors.red, 'MICRO_5s'),
        ],
      ),
    );
  }

  Widget _posRow(String type, String lots, String entry, String sl,
      double pnl, Color c, String src) {
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
                Text('SL: $sl  |  $src',
                    style: monoStyle(fontSize: 9, color: AppColors.dimText)),
              ],
            ),
          ),
          TweenAnimationBuilder<double>(
            tween: Tween(end: pnl),
            duration: const Duration(milliseconds: 400),
            builder: (_, val, __) => Text(
                '${val >= 0 ? "+" : ""}\$${val.toStringAsFixed(2)}',
                style: monoStyle(
                    fontSize: 12,
                    color: pnlColor,
                    fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );
  }

  Widget _controls() {
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
                  child: TerminalButton(
                      label: 'STOP ENGINE',
                      color: AppColors.red,
                      icon: Icons.stop)),
              const SizedBox(width: 8),
              Expanded(
                  child: TerminalButton(
                      label: 'CLOSE ALL',
                      color: AppColors.amber,
                      icon: Icons.close)),
            ],
          ),
          const SizedBox(height: 8),
          Container(
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
          const SizedBox(height: 10),
          Row(
            children: [
              Text('RISK',
                  style: monoStyle(
                      fontSize: 9,
                      color: AppColors.dimText,
                      letterSpacing: 1)),
              const SizedBox(width: 12),
              Expanded(
                child: SliderTheme(
                  data: SliderThemeData(
                    activeTrackColor: AppColors.cyan,
                    inactiveTrackColor: AppColors.border,
                    thumbColor: AppColors.cyan,
                    trackHeight: 2,
                    thumbShape:
                        const RoundSliderThumbShape(enabledThumbRadius: 6),
                    overlayShape:
                        const RoundSliderOverlayShape(overlayRadius: 12),
                  ),
                  child: Slider(value: 0.5, onChanged: (_) {}),
                ),
              ),
              Text('0.50%',
                  style: monoStyle(
                      fontSize: 11,
                      color: AppColors.cyan,
                      fontWeight: FontWeight.bold)),
            ],
          ),
        ],
      ),
    );
  }

  Widget _history() {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.surface,
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        children: [
          TerminalSectionHeader(
            title: 'RECENT TRADES',
            trailing: Text('VIEW ALL >',
                style: monoStyle(fontSize: 9, color: AppColors.cyan)),
          ),
          _tradeRow('14:23', 'BUY', '0.12', '+\$45.20', true),
          Container(height: 1, color: AppColors.border),
          _tradeRow('14:18', 'SELL', '0.08', '-\$12.80', false),
          Container(height: 1, color: AppColors.border),
          _tradeRow('14:05', 'BUY', '0.15', '+\$78.40', true),
        ],
      ),
    );
  }

  Widget _tradeRow(String t, String ty, String l, String p, bool w) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      child: Row(
        children: [
          Text(t, style: monoStyle(fontSize: 10, color: AppColors.dimText)),
          const SizedBox(width: 8),
          Text(ty,
              style: monoStyle(
                  fontSize: 10,
                  color: ty == 'BUY' ? AppColors.green : AppColors.red,
                  fontWeight: FontWeight.bold)),
          const SizedBox(width: 8),
          Text('$l lots',
              style: monoStyle(fontSize: 10, color: AppColors.text)),
          const Spacer(),
          Text(p,
              style: monoStyle(
                  fontSize: 11,
                  color: w ? AppColors.green : AppColors.red,
                  fontWeight: FontWeight.bold)),
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
