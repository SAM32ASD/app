import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../theme/app_theme.dart';
import '../widgets/terminal_card.dart';
import '../providers/auth_provider.dart';
import '../services/admin_service.dart';

class AdminScreen extends StatefulWidget {
  const AdminScreen({super.key});

  @override
  State<AdminScreen> createState() => _AdminScreenState();
}

class _AdminScreenState extends State<AdminScreen> {
  final _adminService = AdminService();

  List<Map<String, dynamic>> _users = [];
  List<Map<String, dynamic>> _logs = [];
  bool _loadingUsers = true;
  bool _loadingLogs = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    await Future.wait([_loadUsers(), _loadAuditLogs()]);
  }

  Future<void> _loadUsers() async {
    setState(() => _loadingUsers = true);
    try {
      final users = await _adminService.getUsers();
      setState(() {
        _users = users;
        _loadingUsers = false;
        _error = null;
      });
    } catch (e) {
      setState(() {
        _loadingUsers = false;
        _error = e.toString();
      });
    }
  }

  Future<void> _loadAuditLogs() async {
    setState(() => _loadingLogs = true);
    try {
      final data = await _adminService.getAuditLogs();
      final logs = (data['logs'] as List<dynamic>?) ?? [];
      setState(() {
        _logs = logs.map((e) => Map<String, dynamic>.from(e as Map)).toList();
        _loadingLogs = false;
      });
    } catch (_) {
      setState(() => _loadingLogs = false);
    }
  }

  Future<void> _changeRole(String userId, String newRole) async {
    try {
      await _adminService.updateUserRole(userId, newRole);
      await _loadUsers();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to update role: $e'),
            backgroundColor: AppColors.red,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final role = auth.user?['role'] as String? ?? '';

    if (role != 'admin') {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.lock, color: AppColors.dimText, size: 32),
            const SizedBox(height: 12),
            Text('ACCESS DENIED',
                style: monoStyle(
                    fontSize: 12,
                    color: AppColors.red,
                    letterSpacing: 3,
                    fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Text('Admin privileges required',
                style: monoStyle(fontSize: 10, color: AppColors.dimText)),
          ],
        ),
      );
    }

    return RefreshIndicator(
      color: AppColors.cyan,
      backgroundColor: AppColors.surface,
      onRefresh: _loadData,
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        child: Column(
          children: [
            if (_error != null) _errorBanner(),
            _usersSection(),
            const SizedBox(height: 8),
            _auditSection(),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }

  Widget _errorBanner() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(10),
      margin: const EdgeInsets.only(bottom: 8),
      color: AppColors.red.withValues(alpha: 0.1),
      child: Text(_error!,
          style: monoStyle(fontSize: 9, color: AppColors.red)),
    );
  }

  Widget _usersSection() {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.surface,
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        children: [
          TerminalSectionHeader(
            title: 'USERS',
            trailing: _loadingUsers
                ? const SizedBox(
                    width: 12,
                    height: 12,
                    child: CircularProgressIndicator(
                        strokeWidth: 1.5, color: AppColors.cyan),
                  )
                : TerminalBadge(
                    label: '${_users.where((u) => u['is_online'] == true).length} ONLINE',
                    color: AppColors.green),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            color: AppColors.bg,
            child: Row(
              children: [
                _colHeader('USER', 3),
                _colHeader('ROLE', 2),
                _colHeader('STATUS', 1),
              ],
            ),
          ),
          if (_loadingUsers)
            const Padding(
              padding: EdgeInsets.all(20),
              child: CircularProgressIndicator(
                  strokeWidth: 2, color: AppColors.cyan),
            )
          else
            ..._users.map((u) => Column(
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

  Widget _userRow(Map<String, dynamic> u) {
    final email = u['email'] as String? ?? '';
    final role = u['role'] as String? ?? 'viewer';
    final isOnline = u['is_online'] as bool? ?? false;
    final userId = u['id'] as String? ?? '';
    final displayName = u['display_name'] as String? ?? '';

    final roleColor = role == 'admin'
        ? AppColors.amber
        : role == 'trader'
            ? AppColors.cyan
            : AppColors.dimText;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      child: Row(
        children: [
          Expanded(
            flex: 3,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (displayName.isNotEmpty)
                  Text(displayName,
                      style: monoStyle(fontSize: 9, color: AppColors.text),
                      overflow: TextOverflow.ellipsis),
                Text(email,
                    style: monoStyle(
                        fontSize: displayName.isNotEmpty ? 8 : 9,
                        color: displayName.isNotEmpty
                            ? AppColors.dimText
                            : AppColors.text),
                    overflow: TextOverflow.ellipsis),
              ],
            ),
          ),
          Expanded(
            flex: 2,
            child: GestureDetector(
              onTap: () => _showRoleDialog(userId, email, role),
              child: TerminalBadge(label: role.toUpperCase(), color: roleColor),
            ),
          ),
          Expanded(
            flex: 1,
            child: Row(
              children: [
                Container(
                  width: 6,
                  height: 6,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: isOnline ? AppColors.green : AppColors.dimText,
                  ),
                ),
                const SizedBox(width: 4),
                Text(isOnline ? 'ON' : 'OFF',
                    style: monoStyle(
                        fontSize: 9,
                        color: isOnline ? AppColors.green : AppColors.dimText)),
              ],
            ),
          ),
        ],
      ),
    );
  }

  void _showRoleDialog(String userId, String email, String currentRole) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.surface,
        shape: RoundedRectangleBorder(
          side: const BorderSide(color: AppColors.border),
          borderRadius: BorderRadius.zero,
        ),
        title: Text('CHANGE ROLE',
            style: monoStyle(
                fontSize: 12,
                color: AppColors.cyan,
                letterSpacing: 2,
                fontWeight: FontWeight.bold)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(email,
                style: monoStyle(fontSize: 10, color: AppColors.text)),
            const SizedBox(height: 16),
            ...['admin', 'trader', 'viewer'].map((role) {
              final isActive = role == currentRole;
              final color = role == 'admin'
                  ? AppColors.amber
                  : role == 'trader'
                      ? AppColors.cyan
                      : AppColors.dimText;
              return GestureDetector(
                onTap: isActive
                    ? null
                    : () {
                        Navigator.pop(ctx);
                        _changeRole(userId, role);
                      },
                child: Container(
                  width: double.infinity,
                  padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 12),
                  margin: const EdgeInsets.only(bottom: 6),
                  decoration: BoxDecoration(
                    border: Border.all(
                        color: isActive ? color : AppColors.border),
                    color: isActive ? color.withValues(alpha: 0.12) : null,
                  ),
                  child: Row(
                    children: [
                      Text(role.toUpperCase(),
                          style: monoStyle(
                              fontSize: 11,
                              color: isActive ? color : AppColors.text,
                              fontWeight: FontWeight.bold,
                              letterSpacing: 1)),
                      const Spacer(),
                      if (isActive)
                        Text('CURRENT',
                            style: monoStyle(
                                fontSize: 8, color: AppColors.dimText)),
                    ],
                  ),
                ),
              );
            }),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: Text('CANCEL',
                style: monoStyle(fontSize: 10, color: AppColors.dimText)),
          ),
        ],
      ),
    );
  }

  Widget _auditSection() {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.surface,
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        children: [
          TerminalSectionHeader(
            title: 'AUDIT LOG',
            trailing: _loadingLogs
                ? const SizedBox(
                    width: 12,
                    height: 12,
                    child: CircularProgressIndicator(
                        strokeWidth: 1.5, color: AppColors.cyan),
                  )
                : Text('${_logs.length} ENTRIES',
                    style: monoStyle(fontSize: 9, color: AppColors.dimText)),
          ),
          if (_loadingLogs)
            const Padding(
              padding: EdgeInsets.all(20),
              child: CircularProgressIndicator(
                  strokeWidth: 2, color: AppColors.cyan),
            )
          else if (_logs.isEmpty)
            Padding(
              padding: const EdgeInsets.all(20),
              child: Text('No audit logs yet',
                  style: monoStyle(fontSize: 10, color: AppColors.dimText)),
            )
          else
            ..._logs.map((log) {
              final action = log['action'] as String? ?? '';
              final details = log['details'] as String? ?? '';
              final createdAt = log['created_at'] as String? ?? '';
              final time = createdAt.length >= 19
                  ? createdAt.substring(11, 19)
                  : createdAt;

              Color actionColor = AppColors.dimText;
              if (action.contains('ROLE')) actionColor = AppColors.amber;
              if (action.contains('START') || action.contains('LOGIN')) {
                actionColor = AppColors.green;
              }
              if (action.contains('STOP') || action.contains('EMERGENCY')) {
                actionColor = AppColors.red;
              }

              return Column(
                children: [
                  Container(height: 1, color: AppColors.border),
                  Padding(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 12, vertical: 6),
                    child: Row(
                      children: [
                        Text(time,
                            style: monoStyle(
                                fontSize: 9, color: AppColors.dimText)),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                              details.isNotEmpty ? details : action,
                              style: monoStyle(
                                  fontSize: 9, color: AppColors.text),
                              overflow: TextOverflow.ellipsis),
                        ),
                        const SizedBox(width: 8),
                        TerminalBadge(label: action, color: actionColor),
                      ],
                    ),
                  ),
                ],
              );
            }),
        ],
      ),
    );
  }
}
