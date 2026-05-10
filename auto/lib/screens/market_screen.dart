import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../theme/app_theme.dart';
import '../widgets/terminal_card.dart';
import '../providers/market_provider.dart';

class MarketScreen extends StatelessWidget {
  const MarketScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      child: Column(
        children: [
          _priceHeader(),
          const SizedBox(height: 8),
          _chartPlaceholder(),
          const SizedBox(height: 8),
          _timeframeSelector(),
          const SizedBox(height: 8),
          _indicators(),
          const SizedBox(height: 8),
          _srLevels(),
          const SizedBox(height: 8),
          _microTimeframes(),
          const SizedBox(height: 8),
          _volatilityMonitor(),
          const SizedBox(height: 16),
        ],
      ),
    );
  }

  Widget _priceHeader() {
    return Builder(builder: (context) {
      final market = context.watch<MarketProvider>();
      final bid = market.bid;
      final spread = market.spread;
      final priceStr = bid > 0 ? bid.toStringAsFixed(2) : '-----.--';
      final wholePart = priceStr.split('.')[0];
      final decPart = priceStr.split('.').length > 1 ? '.${priceStr.split('.')[1]}' : '';

      return TerminalCard(
        child: Row(
          children: [
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('XAUUSD',
                    style: monoStyle(
                        fontSize: 10,
                        color: AppColors.dimText,
                        letterSpacing: 2)),
                const SizedBox(height: 4),
                Row(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(wholePart,
                        style: monoStyle(
                            fontSize: 28,
                            color: Colors.white,
                            fontWeight: FontWeight.w300)),
                    Text(decPart,
                        style: monoStyle(
                            fontSize: 18,
                            color: AppColors.cyan,
                            fontWeight: FontWeight.bold)),
                  ],
                ),
              ],
            ),
            const Spacer(),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  color: AppColors.green.withValues(alpha: 0.15),
                  child: Text(market.volatilityStatus,
                      style: monoStyle(fontSize: 11, color: AppColors.green)),
                ),
                const SizedBox(height: 4),
                Text('Spread: ${spread.toStringAsFixed(2)}',
                    style: monoStyle(fontSize: 9, color: AppColors.dimText)),
              ],
            ),
          ],
        ),
      );
    });
  }

  Widget _chartPlaceholder() {
    return Container(
      height: 200,
      decoration: BoxDecoration(
        color: AppColors.surface,
        border: Border.all(color: AppColors.border),
      ),
      child: Stack(
        children: [
          CustomPaint(
            size: const Size(double.infinity, 200),
            painter: _ChartGridPainter(),
          ),
          CustomPaint(
            size: const Size(double.infinity, 200),
            painter: _CandlePainter(),
          ),
          Positioned(
            top: 8,
            left: 8,
            child: Text('M5  OHLC',
                style: monoStyle(fontSize: 9, color: AppColors.dimText)),
          ),
          Positioned(
            top: 8,
            right: 8,
            child: Row(
              children: [
                Text('O 2385.2 ',
                    style: monoStyle(fontSize: 8, color: AppColors.dimText)),
                Text('H 2389.8 ',
                    style: monoStyle(fontSize: 8, color: AppColors.green)),
                Text('L 2383.1 ',
                    style: monoStyle(fontSize: 8, color: AppColors.red)),
                Text('C 2387.4',
                    style: monoStyle(fontSize: 8, color: AppColors.cyan)),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _timeframeSelector() {
    final tfs = ['M1', 'M5', 'M15', 'H1', 'H4', 'D1'];
    return Row(
      children: tfs.map((tf) {
        final active = tf == 'M5';
        return Expanded(
          child: Container(
            margin: EdgeInsets.only(right: tf != 'D1' ? 4 : 0),
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
              child: Text(tf,
                  style: monoStyle(
                      fontSize: 10,
                      color: active ? AppColors.cyan : AppColors.dimText,
                      fontWeight:
                          active ? FontWeight.bold : FontWeight.normal)),
            ),
          ),
        );
      }).toList(),
    );
  }

  Widget _indicators() {
    return TerminalCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('INDICATORS',
              style: monoStyle(
                  fontSize: 9,
                  color: AppColors.dimText,
                  letterSpacing: 2)),
          const SizedBox(height: 10),
          Row(
            children: [
              _indCard('RSI(14)', '58.3', AppColors.amber, 'NEUTRAL'),
              const SizedBox(width: 8),
              _indCard('ADX(14)', '32.1', AppColors.green, 'TRENDING'),
              const SizedBox(width: 8),
              _indCard('ATR(14)', '18.4', AppColors.cyan, 'MODERATE'),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              _indCard('MACD', '+2.14', AppColors.green, 'BULLISH'),
              const SizedBox(width: 8),
              _indCard('EMA(20)', '2,384.6', AppColors.text, 'ABOVE'),
              const SizedBox(width: 8),
              _indCard('EMA(50)', '2,379.2', AppColors.text, 'ABOVE'),
            ],
          ),
        ],
      ),
    );
  }

  Widget _indCard(String name, String val, Color c, String state) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(8),
        decoration: BoxDecoration(
          color: c.withValues(alpha: 0.05),
          border: Border.all(color: c.withValues(alpha: 0.15)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(name,
                style: monoStyle(fontSize: 8, color: AppColors.dimText)),
            const SizedBox(height: 2),
            Text(val,
                style: monoStyle(
                    fontSize: 13, color: c, fontWeight: FontWeight.bold)),
            const SizedBox(height: 2),
            Text(state,
                style: monoStyle(
                    fontSize: 7,
                    color: c.withValues(alpha: 0.7),
                    letterSpacing: 1)),
          ],
        ),
      ),
    );
  }

  Widget _srLevels() {
    return TerminalCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('SUPPORT / RESISTANCE',
              style: monoStyle(
                  fontSize: 9,
                  color: AppColors.dimText,
                  letterSpacing: 2)),
          const SizedBox(height: 10),
          _srRow('R3', '2,412.50', 'WEEKLY', AppColors.red, 0),
          _srRow('R2', '2,401.80', 'H4', AppColors.red, 1),
          _srRow('R1', '2,394.20', 'H1', AppColors.red, 2),
          Container(
            margin: const EdgeInsets.symmetric(vertical: 6),
            padding: const EdgeInsets.symmetric(vertical: 4),
            color: AppColors.cyan.withValues(alpha: 0.08),
            child: Center(
              child: Text('PRICE  2,387.45',
                  style: monoStyle(
                      fontSize: 10,
                      color: AppColors.cyan,
                      fontWeight: FontWeight.bold)),
            ),
          ),
          _srRow('S1', '2,380.60', 'H1', AppColors.green, 2),
          _srRow('S2', '2,372.30', 'H4', AppColors.green, 1),
          _srRow('S3', '2,358.10', 'WEEKLY', AppColors.green, 0),
        ],
      ),
    );
  }

  Widget _srRow(String label, String price, String tf, Color c, int strength) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(
        children: [
          SizedBox(
            width: 24,
            child: Text(label,
                style: monoStyle(
                    fontSize: 9, color: c, fontWeight: FontWeight.bold)),
          ),
          const SizedBox(width: 8),
          Text(price,
              style:
                  monoStyle(fontSize: 11, color: c, fontWeight: FontWeight.bold)),
          const Spacer(),
          Text(tf, style: monoStyle(fontSize: 8, color: AppColors.dimText)),
          const SizedBox(width: 8),
          Row(
            children: List.generate(
                3,
                (i) => Container(
                      width: 8,
                      height: 8,
                      margin: const EdgeInsets.only(left: 2),
                      color: i <= strength
                          ? c.withValues(alpha: 0.6)
                          : AppColors.border,
                    )),
          ),
        ],
      ),
    );
  }

  Widget _microTimeframes() {
    return TerminalCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text('MICRO TIMEFRAMES',
                  style: monoStyle(
                      fontSize: 9,
                      color: AppColors.dimText,
                      letterSpacing: 2)),
              const Spacer(),
              TerminalBadge(label: 'SYNTHETIC', color: AppColors.cyan),
            ],
          ),
          const SizedBox(height: 10),
          _microRow('5s', 'BULLISH', 'Hammer', AppColors.green, 0.72),
          const SizedBox(height: 4),
          _microRow('10s', 'BULLISH', 'Engulfing', AppColors.green, 0.85),
          const SizedBox(height: 4),
          _microRow('15s', 'NEUTRAL', '—', AppColors.dimText, 0.50),
          const SizedBox(height: 4),
          _microRow('20s', 'BEARISH', 'Doji', AppColors.red, 0.35),
          const SizedBox(height: 4),
          _microRow('30s', 'BULLISH', 'Hammer', AppColors.green, 0.68),
        ],
      ),
    );
  }

  Widget _microRow(
      String tf, String bias, String pattern, Color c, double score) {
    return Row(
      children: [
        SizedBox(
            width: 28,
            child: Text(tf,
                style: monoStyle(
                    fontSize: 10,
                    color: AppColors.text,
                    fontWeight: FontWeight.bold))),
        const SizedBox(width: 8),
        SizedBox(
            width: 55,
            child: Text(bias,
                style: monoStyle(
                    fontSize: 9, color: c, fontWeight: FontWeight.bold))),
        SizedBox(
            width: 65,
            child: Text(pattern,
                style: monoStyle(fontSize: 9, color: AppColors.dimText))),
        Expanded(child: MiniBar(ratio: score, color: c)),
        const SizedBox(width: 6),
        Text('${(score * 100).toInt()}',
            style: monoStyle(
                fontSize: 9, color: c, fontWeight: FontWeight.bold)),
      ],
    );
  }

  Widget _volatilityMonitor() {
    return TerminalCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text('VOLATILITY MONITOR',
                  style: monoStyle(
                      fontSize: 9,
                      color: AppColors.dimText,
                      letterSpacing: 2)),
              const Spacer(),
              TerminalBadge(label: 'HIGH VOL', color: AppColors.amber),
            ],
          ),
          const SizedBox(height: 10),
          _volRow('ATR(14)', '18.4', 0.74),
          const SizedBox(height: 4),
          _volRow('True Range', '22.1', 0.82),
          const SizedBox(height: 4),
          _volRow('Normalized ATR', '0.77%', 0.77),
          const SizedBox(height: 4),
          _volRow('Vol Ratio', '1.42x', 0.65),
          const SizedBox(height: 8),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            color: AppColors.amber.withValues(alpha: 0.08),
            child: Text(
                'Volatility above average — SL widened by 20%, lot size reduced',
                style: monoStyle(fontSize: 8, color: AppColors.amber)),
          ),
        ],
      ),
    );
  }

  Widget _volRow(String l, String v, double ratio) {
    return Row(
      children: [
        SizedBox(
            width: 100,
            child: Text(l,
                style: monoStyle(fontSize: 9, color: AppColors.dimText))),
        Expanded(child: MiniBar(ratio: ratio, color: AppColors.amber)),
        const SizedBox(width: 8),
        Text(v,
            style: monoStyle(
                fontSize: 10,
                color: AppColors.amber,
                fontWeight: FontWeight.bold)),
      ],
    );
  }
}

class _ChartGridPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final p = Paint()
      ..color = AppColors.border.withValues(alpha: 0.5)
      ..strokeWidth = 0.5;
    for (var i = 1; i < 5; i++) {
      final y = size.height * i / 5;
      canvas.drawLine(Offset(0, y), Offset(size.width, y), p);
    }
    for (var i = 1; i < 8; i++) {
      final x = size.width * i / 8;
      canvas.drawLine(Offset(x, 0), Offset(x, size.height), p);
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter old) => false;
}

class _CandlePainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final rng = [
      [0.6, 0.3, 0.7, 0.35, true],
      [0.35, 0.2, 0.5, 0.25, true],
      [0.25, 0.15, 0.4, 0.38, false],
      [0.38, 0.3, 0.5, 0.32, false],
      [0.32, 0.2, 0.45, 0.22, true],
      [0.22, 0.1, 0.35, 0.15, true],
      [0.15, 0.05, 0.3, 0.28, false],
      [0.28, 0.2, 0.4, 0.35, false],
      [0.35, 0.25, 0.5, 0.27, true],
      [0.27, 0.15, 0.38, 0.18, true],
      [0.18, 0.1, 0.3, 0.25, false],
      [0.25, 0.18, 0.38, 0.2, true],
      [0.2, 0.08, 0.32, 0.12, true],
      [0.12, 0.05, 0.25, 0.22, false],
      [0.22, 0.15, 0.35, 0.17, true],
      [0.17, 0.1, 0.28, 0.24, false],
      [0.24, 0.18, 0.38, 0.2, true],
      [0.2, 0.12, 0.3, 0.14, true],
      [0.14, 0.05, 0.25, 0.1, true],
      [0.1, 0.02, 0.2, 0.15, false],
    ];
    final w = size.width / (rng.length * 1.5);
    for (var i = 0; i < rng.length; i++) {
      final x = (i * 1.5 + 0.75) * w;
      final open = size.height * (rng[i][0] as double) + 20;
      final low = size.height * (rng[i][1] as double) + 20;
      final high = size.height * (rng[i][2] as double) + 20;
      final close = size.height * (rng[i][3] as double) + 20;
      final bull = rng[i][4] as bool;
      final color = bull ? AppColors.green : AppColors.red;
      canvas.drawLine(Offset(x, low), Offset(x, high),
          Paint()..color = color..strokeWidth = 1);
      final top = bull ? close : open;
      final bot = bull ? open : close;
      canvas.drawRect(
          Rect.fromLTRB(x - w / 3, top, x + w / 3, bot),
          Paint()..color = color);
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter old) => false;
}
