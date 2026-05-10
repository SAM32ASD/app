import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:firebase_core/firebase_core.dart';

import 'theme/app_theme.dart';
import 'services/api_client.dart';
import 'services/auth_service.dart';
import 'services/websocket_service.dart';
import 'services/trading_service.dart';
import 'services/notification_service.dart';
import 'providers/auth_provider.dart';
import 'providers/trading_provider.dart';
import 'providers/market_provider.dart';
import 'providers/config_provider.dart';
import 'providers/trade_history_provider.dart';
import 'providers/notification_provider.dart';
import 'screens/auth_screen.dart';
import 'screens/dashboard_screen.dart';
import 'screens/market_screen.dart';
import 'screens/trades_screen.dart';
import 'screens/config_screen.dart';
import 'screens/admin_screen.dart';
import 'screens/mt5_setup_screen.dart';
import 'widgets/trade_notification.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp();
  final notificationService = NotificationService();
  await notificationService.initialize();
  runApp(LotApp(notificationService: notificationService));
}

class LotApp extends StatelessWidget {
  final NotificationService notificationService;

  const LotApp({super.key, required this.notificationService});

  @override
  Widget build(BuildContext context) {
    final wsService = WebSocketService();

    return MultiProvider(
      providers: [
        ChangeNotifierProvider(
          create: (_) => AuthProvider(
            authService: AuthService(),
            apiClient: ApiClient(),
            webSocketService: wsService,
          ),
        ),
        ChangeNotifierProvider(
          create: (_) => TradingProvider(
            tradingService: TradingService(),
            webSocketService: wsService,
          ),
        ),
        ChangeNotifierProvider(
          create: (_) => MarketProvider(
            webSocketService: wsService,
            tradingService: TradingService(),
          ),
        ),
        ChangeNotifierProvider(create: (_) => ConfigProvider()),
        ChangeNotifierProvider(create: (_) => TradeHistoryProvider()),
        ChangeNotifierProvider(
          create: (_) => NotificationProvider(
            webSocketService: wsService,
            notificationService: notificationService,
          ),
        ),
      ],
      child: MaterialApp(
        title: 'LOT Trading Terminal',
        debugShowCheckedModeBanner: false,
        theme: ThemeData.dark().copyWith(
          scaffoldBackgroundColor: AppColors.bg,
        ),
        home: const AppRoot(),
      ),
    );
  }
}

class AppRoot extends StatefulWidget {
  const AppRoot({super.key});

  @override
  State<AppRoot> createState() => _AppRootState();
}

class _AppRootState extends State<AppRoot> {
  bool _mt5Connected = false;
  bool _mt5Checked = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      await context.read<AuthProvider>().checkAuth();
      if (mounted) _checkMt5Status();
    });
  }

  Future<void> _checkMt5Status() async {
    try {
      final resp = await ApiClient().get('/mt5/accounts');
      final data = resp.data as Map<String, dynamic>;
      final accounts = data['accounts'] as List<dynamic>;
      final hasConnected = accounts.any(
          (a) => (a as Map)['connection_status'] == 'CONNECTED');
      if (mounted) setState(() {
        _mt5Connected = hasConnected;
        _mt5Checked = true;
      });
    } catch (_) {
      if (mounted) setState(() {
        _mt5Connected = false;
        _mt5Checked = true;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();

    if (auth.isLoading || (!_mt5Checked && auth.isAuthenticated)) {
      return Scaffold(
        backgroundColor: AppColors.bg,
        body: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                decoration: BoxDecoration(
                  border: Border.all(color: AppColors.cyan, width: 1.5),
                ),
                child: Text('LOT',
                    style: monoStyle(
                        fontSize: 28,
                        color: AppColors.cyan,
                        fontWeight: FontWeight.w900,
                        letterSpacing: 8)),
              ),
              const SizedBox(height: 24),
              const SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  color: AppColors.cyan,
                ),
              ),
            ],
          ),
        ),
      );
    }

    if (!auth.isAuthenticated) {
      return const AuthScreen();
    }

    if (!_mt5Connected) {
      return MT5SetupScreen(
        onConnected: () => setState(() => _mt5Connected = true),
      );
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
  bool _showNotificationPanel = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<TradingProvider>().refreshStatus();
      context.read<ConfigProvider>().loadConfig();
    });
  }

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
    final notifProvider = context.watch<NotificationProvider>();

    // Show alert dialog if there's a pending alert
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (notifProvider.pendingAlert != null) {
        _showAlertModal(context, notifProvider);
      }
    });

    return Scaffold(
      backgroundColor: AppColors.bg,
      body: SafeArea(
        child: Stack(
          children: [
            Column(
              children: [
                _header(notifProvider),
                Expanded(child: _screens[_tab]),
                _bottomNav(),
              ],
            ),
            // Toast overlay
            _toastOverlay(notifProvider),
            // Notification panel
            if (_showNotificationPanel)
              Positioned.fill(
                child: NotificationPanel(
                  notifications: notifProvider.notifications,
                  onClose: () {
                    notifProvider.markAllRead();
                    setState(() => _showNotificationPanel = false);
                  },
                  onClearAll: () {
                    notifProvider.clearAll();
                    setState(() => _showNotificationPanel = false);
                  },
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _toastOverlay(NotificationProvider notifProvider) {
    if (notifProvider.toastQueue.isEmpty) return const SizedBox.shrink();

    return Positioned(
      top: 60,
      left: 0,
      right: 0,
      child: Column(
        children: [
          TradeToast(
            notification: notifProvider.toastQueue.first,
            onDismiss: () => notifProvider.dismissFirstToast(),
          ),
        ],
      ),
    );
  }

  void _showAlertModal(BuildContext context, NotificationProvider notifProvider) {
    final alert = notifProvider.pendingAlert!;
    notifProvider.dismissAlert();

    Color alertColor;
    IconData alertIcon;
    switch (alert.type) {
      case AlertType.emergency:
        alertColor = AppColors.red;
        alertIcon = Icons.warning_amber;
      case AlertType.connectionError:
        alertColor = AppColors.amber;
        alertIcon = Icons.wifi_off;
      case AlertType.engineStopped:
        alertColor = AppColors.red;
        alertIcon = Icons.error_outline;
    }

    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.surface,
        shape: RoundedRectangleBorder(
          side: BorderSide(color: alertColor, width: 2),
          borderRadius: BorderRadius.zero,
        ),
        title: Row(
          children: [
            Icon(alertIcon, color: alertColor, size: 24),
            const SizedBox(width: 10),
            Expanded(
              child: Text(alert.title,
                  style: monoStyle(
                      fontSize: 14,
                      color: alertColor,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 2)),
            ),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              color: alertColor.withValues(alpha: 0.08),
              child: Text(alert.message,
                  style: monoStyle(fontSize: 11, color: AppColors.text)),
            ),
            const SizedBox(height: 8),
            Text(
              '${alert.time.hour.toString().padLeft(2, '0')}:${alert.time.minute.toString().padLeft(2, '0')}:${alert.time.second.toString().padLeft(2, '0')}',
              style: monoStyle(fontSize: 9, color: AppColors.dimText),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              decoration: BoxDecoration(
                border: Border.all(color: alertColor),
              ),
              child: Text('ACKNOWLEDGE',
                  style: monoStyle(
                      fontSize: 11,
                      color: alertColor,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 1)),
            ),
          ),
        ],
      ),
    );
  }

  Widget _header(NotificationProvider notifProvider) {
    final auth = context.watch<AuthProvider>();
    final user = auth.user;
    final displayName = (user?['display_name'] as String?) ?? '';
    final email = (user?['email'] as String?) ?? '';
    final userLabel = displayName.isNotEmpty ? displayName.split(' ').first : email.split('@').first;

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
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(_labels[_tab],
                    style: monoStyle(
                        fontSize: 11,
                        color: AppColors.dimText,
                        letterSpacing: 3)),
                if (userLabel.isNotEmpty)
                  Text(userLabel,
                      style: monoStyle(fontSize: 9, color: AppColors.cyan),
                      overflow: TextOverflow.ellipsis),
              ],
            ),
          ),
          // MT5 account switch
          GestureDetector(
            onTap: () {
              Navigator.of(context).push(MaterialPageRoute(
                builder: (_) => MT5SetupScreen(
                  onConnected: () => Navigator.of(context).pop(),
                ),
              ));
            },
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
              margin: const EdgeInsets.only(right: 10),
              decoration: BoxDecoration(
                border: Border.all(color: AppColors.border),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.account_balance, color: AppColors.dimText, size: 12),
                  const SizedBox(width: 4),
                  Text('MT5', style: monoStyle(fontSize: 8, color: AppColors.dimText, letterSpacing: 1)),
                ],
              ),
            ),
          ),
          // Connection indicator
          Container(
            width: 8,
            height: 8,
            margin: const EdgeInsets.only(right: 10),
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: notifProvider.connected ? AppColors.green : AppColors.dimText,
            ),
          ),
          // Notification bell
          GestureDetector(
            onTap: () => setState(() => _showNotificationPanel = !_showNotificationPanel),
            child: Stack(
              children: [
                const Icon(Icons.notifications_none, color: AppColors.dimText, size: 20),
                if (notifProvider.unreadCount > 0)
                  Positioned(
                    right: 0,
                    top: 0,
                    child: Container(
                      width: 12,
                      height: 12,
                      decoration: const BoxDecoration(
                        shape: BoxShape.circle,
                        color: AppColors.red,
                      ),
                      child: Center(
                        child: Text(
                          notifProvider.unreadCount > 9 ? '9+' : '${notifProvider.unreadCount}',
                          style: monoStyle(fontSize: 7, color: Colors.white, fontWeight: FontWeight.bold),
                        ),
                      ),
                    ),
                  ),
              ],
            ),
          ),
          const SizedBox(width: 12),
          GestureDetector(
            onTap: () => context.read<AuthProvider>().logout(),
            child:
                const Icon(Icons.logout, color: AppColors.dimText, size: 20),
          ),
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
                          color: active ? AppColors.cyan : AppColors.dimText,
                          fontWeight:
                              active ? FontWeight.bold : FontWeight.normal,
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
