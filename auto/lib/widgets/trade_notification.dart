import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

class TradeNotification {
  final String type;
  final double lots;
  final double pnl;
  final String source;
  final DateTime time;
  final bool read;

  TradeNotification({
    required this.type,
    required this.lots,
    required this.pnl,
    required this.source,
    required this.time,
    this.read = false,
  });

  bool get isWin => pnl >= 0;
}

class TradeToast extends StatefulWidget {
  final TradeNotification notification;
  final VoidCallback onDismiss;

  const TradeToast({
    super.key,
    required this.notification,
    required this.onDismiss,
  });

  @override
  State<TradeToast> createState() => _TradeToastState();
}

class _TradeToastState extends State<TradeToast>
    with SingleTickerProviderStateMixin {
  late AnimationController _ctrl;
  late Animation<double> _slideAnim;
  late Animation<double> _fadeAnim;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
        vsync: this, duration: const Duration(milliseconds: 400));
    _slideAnim = Tween<double>(begin: -80, end: 0)
        .animate(CurvedAnimation(parent: _ctrl, curve: Curves.easeOutBack));
    _fadeAnim = Tween<double>(begin: 0, end: 1)
        .animate(CurvedAnimation(parent: _ctrl, curve: Curves.easeIn));
    _ctrl.forward();
    Future.delayed(const Duration(seconds: 4), () {
      if (mounted) {
        _ctrl.reverse().then((_) {
          if (mounted) widget.onDismiss();
        });
      }
    });
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final n = widget.notification;
    final color = n.isWin ? AppColors.green : AppColors.red;
    return AnimatedBuilder(
      animation: _ctrl,
      builder: (_, child) => Transform.translate(
        offset: Offset(0, _slideAnim.value),
        child: Opacity(opacity: _fadeAnim.value, child: child),
      ),
      child: Container(
        margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: AppColors.surface,
          border: Border.all(color: color.withValues(alpha: 0.5)),
          boxShadow: [
            BoxShadow(
                color: color.withValues(alpha: 0.15),
                blurRadius: 12,
                offset: const Offset(0, 4)),
          ],
        ),
        child: Row(
          children: [
            Container(
              width: 4,
              height: 40,
              color: color,
            ),
            const SizedBox(width: 10),
            Icon(
              n.isWin ? Icons.check_circle : Icons.cancel,
              color: color,
              size: 20,
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Row(
                    children: [
                      Text('${n.type} CLOSED',
                          style: monoStyle(
                              fontSize: 10,
                              color: color,
                              fontWeight: FontWeight.bold,
                              letterSpacing: 1)),
                      const SizedBox(width: 6),
                      Text('${n.lots} lots',
                          style: monoStyle(
                              fontSize: 9, color: AppColors.dimText)),
                      const SizedBox(width: 6),
                      Text(n.source,
                          style: monoStyle(
                              fontSize: 8, color: AppColors.cyan)),
                    ],
                  ),
                  const SizedBox(height: 2),
                  Text(
                    '${n.isWin ? "+" : ""}\$${n.pnl.toStringAsFixed(2)}',
                    style: monoStyle(
                        fontSize: 16,
                        color: color,
                        fontWeight: FontWeight.bold),
                  ),
                ],
              ),
            ),
            GestureDetector(
              onTap: () {
                _ctrl.reverse().then((_) {
                  if (mounted) widget.onDismiss();
                });
              },
              child: const Icon(Icons.close,
                  color: AppColors.dimText, size: 16),
            ),
          ],
        ),
      ),
    );
  }
}

class NotificationPanel extends StatelessWidget {
  final List<TradeNotification> notifications;
  final VoidCallback onClose;
  final VoidCallback onClearAll;

  const NotificationPanel({
    super.key,
    required this.notifications,
    required this.onClose,
    required this.onClearAll,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      color: AppColors.bg.withValues(alpha: 0.95),
      child: Column(
        children: [
          Container(
            padding:
                const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            decoration: const BoxDecoration(
              color: AppColors.surface,
              border:
                  Border(bottom: BorderSide(color: AppColors.border)),
            ),
            child: Row(
              children: [
                Text('NOTIFICATIONS',
                    style: monoStyle(
                        fontSize: 10,
                        color: AppColors.dimText,
                        letterSpacing: 2)),
                const Spacer(),
                GestureDetector(
                  onTap: onClearAll,
                  child: Text('CLEAR ALL',
                      style: monoStyle(
                          fontSize: 9,
                          color: AppColors.cyan,
                          letterSpacing: 1)),
                ),
                const SizedBox(width: 16),
                GestureDetector(
                  onTap: onClose,
                  child: const Icon(Icons.close,
                      color: AppColors.dimText, size: 18),
                ),
              ],
            ),
          ),
          Expanded(
            child: notifications.isEmpty
                ? Center(
                    child: Text('No notifications',
                        style: monoStyle(
                            fontSize: 11, color: AppColors.dimText)),
                  )
                : ListView.separated(
                    padding: const EdgeInsets.all(12),
                    itemCount: notifications.length,
                    separatorBuilder: (_, __) =>
                        const SizedBox(height: 6),
                    itemBuilder: (_, i) {
                      final n = notifications[notifications.length - 1 - i];
                      final color =
                          n.isWin ? AppColors.green : AppColors.red;
                      return Container(
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: AppColors.surface,
                          border: Border.all(
                              color: color.withValues(alpha: 0.2)),
                        ),
                        child: Row(
                          children: [
                            Container(
                              width: 3,
                              height: 36,
                              color: color,
                            ),
                            const SizedBox(width: 10),
                            Expanded(
                              child: Column(
                                crossAxisAlignment:
                                    CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    children: [
                                      Text('${n.type} CLOSED',
                                          style: monoStyle(
                                              fontSize: 9,
                                              color: color,
                                              fontWeight: FontWeight.bold)),
                                      const SizedBox(width: 6),
                                      Text('${n.lots} lots',
                                          style: monoStyle(
                                              fontSize: 8,
                                              color: AppColors.dimText)),
                                      const SizedBox(width: 6),
                                      Text(n.source,
                                          style: monoStyle(
                                              fontSize: 8,
                                              color: AppColors.cyan)),
                                    ],
                                  ),
                                  Text(
                                    '${n.isWin ? "+" : ""}\$${n.pnl.toStringAsFixed(2)}',
                                    style: monoStyle(
                                        fontSize: 14,
                                        color: color,
                                        fontWeight: FontWeight.bold),
                                  ),
                                ],
                              ),
                            ),
                            Text(
                              '${n.time.hour.toString().padLeft(2, '0')}:${n.time.minute.toString().padLeft(2, '0')}:${n.time.second.toString().padLeft(2, '0')}',
                              style: monoStyle(
                                  fontSize: 8,
                                  color: AppColors.dimText),
                            ),
                          ],
                        ),
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }
}
