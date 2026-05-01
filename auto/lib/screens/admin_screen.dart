import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../widgets/terminal_card.dart';

class AdminScreen extends StatelessWidget {
  const AdminScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      child: Column(
        children: [
          _globalStatus(),
          const SizedBox(height: 8),
          _usersTable(),
          const SizedBox(height: 8),
          _globalOverrides(),
          const SizedBox(height: 8),
          _auditLogs(),
          const SizedBox(height: 16),
        ],
      ),
    );
  }

  Widget _globalStatus() {
    return TerminalCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('SYSTEM STATUS',
              style: monoStyle(
                  fontSize: 9,
                  color: AppColors.dimText,
                  letterSpacing: 2)),
          const SizedBox(height: 10),
          Row(
            children: [
              _statusItem('USERS ONLINE', '3', AppColors.green),
              _statusItem('ACTIVE TRADES', '5', AppColors.cyan),
              _statusItem('TOTAL P&L', '+\$2,140', AppColors.green),
              _statusItem('CPU', '12%', AppColors.text),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              _statusItem('MEMORY', '340MB', AppColors.text),
              _statusItem('DB CONN', 'OK', AppColors.green),
              _statusItem('REDIS', 'OK', AppColors.green),
              _statusItem('MT5 API', 'LIVE', AppColors.green),
            ],
          ),
        ],
      ),
    );
  }

  Widget _statusItem(String l, String v, Color c) {
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

  Widget _usersTable() {
    final users = [
      _User('admin@lot.app', 'admin', true, 14, 847.20),
      _User('trader1@lot.app', 'trader', true, 8, 312.50),
      _User('viewer@lot.app', 'viewer', false, 0, 0),
      _User('trader2@lot.app', 'trader', true, 12, -45.80),
    ];

    return Container(
      decoration: BoxDecoration(
        color: AppColors.surface,
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        children: [
          TerminalSectionHeader(
            title: 'USERS',
            trailing: TerminalBadge(
                label: '${users.where((u) => u.online).length} ONLINE',
                color: AppColors.green),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            color: AppColors.bg,
            child: Row(
              children: [
                _colHeader('USER', 3),
                _colHeader('ROLE', 2),
                _colHeader('STATUS', 2),
                _colHeader('TRADES', 1),
                _colHeader('P&L', 2),
              ],
            ),
          ),
          ...users.map((u) => Column(
                children: [
                  Container(height: 1, color: AppColors.border),
                  _userRow(u),
                ],
              )),
        ],
      ),
    );
  }

  Widget _colHeader(String l, int flex) {
    return Expanded(
      flex: flex,
      child: Text(l,
          style: monoStyle(
              fontSize: 8, color: AppColors.dimText, letterSpacing: 1)),
    );
  }

  Widget _userRow(_User u) {
    final roleColor = u.role == 'admin'
        ? AppColors.amber
        : u.role == 'trader'
            ? AppColors.cyan
            : AppColors.dimText;
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      child: Row(
        children: [
          Expanded(
            flex: 3,
            child: Text(u.email,
                style: monoStyle(fontSize: 9, color: AppColors.text),
                overflow: TextOverflow.ellipsis),
          ),
          Expanded(
            flex: 2,
            child: TerminalBadge(
                label: u.role.toUpperCase(), color: roleColor),
          ),
          Expanded(
            flex: 2,
            child: Row(
              children: [
                Container(
                  width: 6,
                  height: 6,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: u.online ? AppColors.green : AppColors.dimText,
                  ),
                ),
                const SizedBox(width: 4),
                Text(u.online ? 'ON' : 'OFF',
                    style: monoStyle(
                        fontSize: 9,
                        color: u.online
                            ? AppColors.green
                            : AppColors.dimText)),
              ],
            ),
          ),
          Expanded(
            flex: 1,
            child: Text('${u.trades}',
                style: monoStyle(
                    fontSize: 10,
                    color: AppColors.text,
                    fontWeight: FontWeight.bold)),
          ),
          Expanded(
            flex: 2,
            child: Text(
                '${u.pnl >= 0 ? "+" : ""}\$${u.pnl.toStringAsFixed(2)}',
                style: monoStyle(
                    fontSize: 10,
                    color: u.pnl >= 0 ? AppColors.green : AppColors.red,
                    fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );
  }

  Widget _globalOverrides() {
    return TerminalCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('GLOBAL OVERRIDES',
              style: monoStyle(
                  fontSize: 9,
                  color: AppColors.dimText,
                  letterSpacing: 2)),
          const SizedBox(height: 10),
          _overrideRow('Max Global Risk', '0.5%', AppColors.cyan),
          _overrideRow('Max Daily Loss (all)', '5.0%', AppColors.amber),
          _overrideRow('Kill Switch', 'ARMED', AppColors.red),
          _overrideRow('New Registration', 'DISABLED', AppColors.dimText),
          _overrideRow('Maintenance Mode', 'OFF', AppColors.green),
        ],
      ),
    );
  }

  Widget _overrideRow(String l, String v, Color c) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Text(l, style: monoStyle(fontSize: 10, color: AppColors.text)),
          const Spacer(),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
            decoration: BoxDecoration(
              border: Border.all(color: c.withValues(alpha: 0.3)),
              color: c.withValues(alpha: 0.08),
            ),
            child: Text(v,
                style: monoStyle(
                    fontSize: 10, color: c, fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );
  }

  Widget _auditLogs() {
    final logs = [
      _Log('14:23:05', 'admin@lot.app', 'START_TRADING', AppColors.green),
      _Log('14:18:32', 'admin@lot.app', 'UPDATE_RISK 0.5%', AppColors.cyan),
      _Log('13:52:10', 'trader1@lot.app', 'STOP_TRADING', AppColors.red),
      _Log('13:41:22', 'admin@lot.app', 'CHANGE_ROLE trader2→admin', AppColors.amber),
      _Log('12:58:44', 'admin@lot.app', 'EMERGENCY_STOP', AppColors.red),
      _Log('12:30:01', 'system', 'DAILY_RESET', AppColors.dimText),
    ];

    return Container(
      decoration: BoxDecoration(
        color: AppColors.surface,
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        children: [
          TerminalSectionHeader(
            title: 'AUDIT LOG',
            trailing: Text('EXPORT >',
                style: monoStyle(fontSize: 9, color: AppColors.cyan)),
          ),
          ...logs.map((log) => Column(
                children: [
                  Container(height: 1, color: AppColors.border),
                  Padding(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 12, vertical: 6),
                    child: Row(
                      children: [
                        Text(log.time,
                            style: monoStyle(
                                fontSize: 9, color: AppColors.dimText)),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(log.user,
                              style: monoStyle(
                                  fontSize: 9, color: AppColors.text),
                              overflow: TextOverflow.ellipsis),
                        ),
                        const SizedBox(width: 8),
                        TerminalBadge(
                            label: log.action, color: log.color),
                      ],
                    ),
                  ),
                ],
              )),
        ],
      ),
    );
  }
}

class _User {
  final String email, role;
  final bool online;
  final int trades;
  final double pnl;
  _User(this.email, this.role, this.online, this.trades, this.pnl);
}

class _Log {
  final String time, user, action;
  final Color color;
  _Log(this.time, this.user, this.action, this.color);
}
