import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

class TerminalCard extends StatelessWidget {
  final Widget child;
  final EdgeInsets? padding;

  const TerminalCard({super.key, required this.child, this.padding});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: padding ?? const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.surface,
        border: Border.all(color: AppColors.border),
      ),
      child: child,
    );
  }
}

class TerminalSectionHeader extends StatelessWidget {
  final String title;
  final Widget? trailing;

  const TerminalSectionHeader({super.key, required this.title, this.trailing});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: const BoxDecoration(
        border: Border(bottom: BorderSide(color: AppColors.border)),
      ),
      child: Row(
        children: [
          Text(title,
              style: monoStyle(
                  fontSize: 9,
                  color: AppColors.dimText,
                  letterSpacing: 2)),
          const Spacer(),
          if (trailing != null) trailing!,
        ],
      ),
    );
  }
}

class TerminalBadge extends StatelessWidget {
  final String label;
  final Color color;

  const TerminalBadge({super.key, required this.label, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      color: color.withValues(alpha: 0.12),
      child: Text(label,
          style: monoStyle(
              fontSize: 9, color: color, fontWeight: FontWeight.bold)),
    );
  }
}

class TerminalButton extends StatelessWidget {
  final String label;
  final Color color;
  final IconData icon;
  final VoidCallback? onTap;

  const TerminalButton({
    super.key,
    required this.label,
    required this.color,
    required this.icon,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 10),
        decoration: BoxDecoration(
          border: Border.all(color: color.withValues(alpha: 0.5)),
          color: color.withValues(alpha: 0.08),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, color: color, size: 14),
            const SizedBox(width: 6),
            Text(label,
                style: monoStyle(
                    fontSize: 10,
                    color: color,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 1)),
          ],
        ),
      ),
    );
  }
}

class MiniBar extends StatelessWidget {
  final double ratio;
  final Color color;

  const MiniBar({super.key, required this.ratio, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 3,
      color: AppColors.border,
      child: FractionallySizedBox(
        alignment: Alignment.centerLeft,
        widthFactor: ratio.clamp(0.0, 1.0),
        child: Container(color: color),
      ),
    );
  }
}
