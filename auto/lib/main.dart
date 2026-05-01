import 'package:flutter/material.dart';
import 'theme/app_theme.dart';
import 'screens/auth_screen.dart';
import 'screens/dashboard_screen.dart';
import 'screens/market_screen.dart';
import 'screens/trades_screen.dart';
import 'screens/config_screen.dart';
import 'screens/admin_screen.dart';

void main() {
  runApp(const LotApp());
}

class LotApp extends StatelessWidget {
  const LotApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'LOT Trading Terminal',
      debugShowCheckedModeBanner: false,
      theme: ThemeData.dark().copyWith(
        scaffoldBackgroundColor: AppColors.bg,
      ),
      home: const AppRoot(),
    );
  }
}

class AppRoot extends StatefulWidget {
  const AppRoot({super.key});

  @override
  State<AppRoot> createState() => _AppRootState();
}

class _AppRootState extends State<AppRoot> {
  bool _authenticated = false;

  @override
  Widget build(BuildContext context) {
    if (!_authenticated) {
      return AuthScreen(onLogin: () => setState(() => _authenticated = true));
    }
    return const AppShell();
  }
}

class AppShell extends StatefulWidget {
  const AppShell({super.key});

  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> {
  int _tab = 0;

  final _screens = const [
    DashboardScreen(),
    MarketScreen(),
    TradesScreen(),
    ConfigScreen(),
    AdminScreen(),
  ];

  final _labels = ['DASH', 'MARKET', 'TRADES', 'CONFIG', 'ADMIN'];
  final _icons = [
    Icons.dashboard,
    Icons.candlestick_chart,
    Icons.swap_vert,
    Icons.tune,
    Icons.admin_panel_settings,
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.bg,
      body: SafeArea(
        child: Column(
          children: [
            _header(),
            Expanded(child: _screens[_tab]),
            _bottomNav(),
          ],
        ),
      ),
    );
  }

  Widget _header() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: const BoxDecoration(
        color: AppColors.surface,
        border: Border(bottom: BorderSide(color: AppColors.border)),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            decoration: BoxDecoration(
              border: Border.all(color: AppColors.cyan, width: 1),
            ),
            child: Text('LOT',
                style: monoStyle(
                    fontSize: 16,
                    color: AppColors.cyan,
                    fontWeight: FontWeight.w900,
                    letterSpacing: 4)),
          ),
          const SizedBox(width: 12),
          Text(_labels[_tab],
              style: monoStyle(
                  fontSize: 11,
                  color: AppColors.dimText,
                  letterSpacing: 3)),
          const Spacer(),
          const Icon(Icons.notifications_none,
              color: AppColors.dimText, size: 20),
          const SizedBox(width: 12),
          const Icon(Icons.settings, color: AppColors.dimText, size: 20),
        ],
      ),
    );
  }

  Widget _bottomNav() {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 8),
      decoration: const BoxDecoration(
        color: AppColors.surface,
        border: Border(top: BorderSide(color: AppColors.border)),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: List.generate(5, (i) {
          final active = _tab == i;
          return GestureDetector(
            onTap: () => setState(() => _tab = i),
            behavior: HitTestBehavior.opaque,
            child: SizedBox(
              width: 60,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(_icons[i],
                      color: active ? AppColors.cyan : AppColors.dimText,
                      size: 20),
                  const SizedBox(height: 2),
                  Text(_labels[i],
                      style: monoStyle(
                          fontSize: 8,
                          color:
                              active ? AppColors.cyan : AppColors.dimText,
                          fontWeight: active
                              ? FontWeight.bold
                              : FontWeight.normal,
                          letterSpacing: 1)),
                ],
              ),
            ),
          );
        }),
      ),
    );
  }
}
