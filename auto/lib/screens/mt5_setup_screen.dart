import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../services/api_client.dart';

class MT5SetupScreen extends StatefulWidget {
  final VoidCallback onConnected;

  const MT5SetupScreen({super.key, required this.onConnected});

  @override
  State<MT5SetupScreen> createState() => _MT5SetupScreenState();
}

class _MT5SetupScreenState extends State<MT5SetupScreen> {
  final _serverController = TextEditingController(text: 'MetaQuotes-Demo');
  final _loginController = TextEditingController();
  final _passwordController = TextEditingController();

  bool _isLoading = false;
  bool _loadingAccounts = true;
  bool _obscurePassword = true;
  String? _error;
  String _statusMessage = '';
  List<Map<String, dynamic>> _accounts = [];

  final _api = ApiClient();

  @override
  void initState() {
    super.initState();
    _loadAccounts();
  }

  Future<void> _loadAccounts() async {
    try {
      final resp = await _api.get('/mt5/accounts');
      final data = resp.data as Map<String, dynamic>;
      final list = data['accounts'] as List<dynamic>;
      setState(() {
        _accounts = list.map((e) => Map<String, dynamic>.from(e as Map)).toList();
        _loadingAccounts = false;
      });
    } catch (_) {
      setState(() => _loadingAccounts = false);
    }
  }

  Future<void> _connectExisting(String accountId) async {
    setState(() {
      _isLoading = true;
      _error = null;
      _statusMessage = 'CONNECTING TO MT5...';
    });

    try {
      final connectResp = await _api.post('/mt5/accounts/$accountId/connect');
      final connectData = connectResp.data as Map<String, dynamic>;

      if (connectData['connection_status'] == 'CONNECTED' ||
          connectData['status'] == 'already_connected') {
        setState(() => _statusMessage = 'STARTING TRADING ENGINE...');

        await _api.post('/trading/start');

        setState(() => _statusMessage = 'CONNECTED');
        await Future.delayed(const Duration(milliseconds: 500));
        widget.onConnected();
      }
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _connectNew() async {
    final server = _serverController.text.trim();
    final login = _loginController.text.trim();
    final password = _passwordController.text.trim();

    if (server.isEmpty || login.isEmpty || password.isEmpty) {
      setState(() => _error = 'All fields are required');
      return;
    }

    setState(() {
      _isLoading = true;
      _error = null;
      _statusMessage = 'SAVING ACCOUNT...';
    });

    try {
      final createResp = await _api.post('/mt5/accounts', data: {
        'broker': server.split('-').first.trim(),
        'account_number': login,
        'password': password,
        'server': server,
      });
      final accountData = createResp.data as Map<String, dynamic>;
      final accountId = accountData['id'] as String;

      setState(() => _statusMessage = 'CONNECTING TO MT5...');

      final connectResp = await _api.post('/mt5/accounts/$accountId/connect');
      final connectData = connectResp.data as Map<String, dynamic>;

      if (connectData['connection_status'] == 'CONNECTED' ||
          connectData['status'] == 'already_connected') {
        setState(() => _statusMessage = 'STARTING TRADING ENGINE...');

        await _api.post('/trading/start');

        setState(() => _statusMessage = 'CONNECTED');
        await Future.delayed(const Duration(milliseconds: 500));
        widget.onConnected();
      }
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  void dispose() {
    _serverController.dispose();
    _loginController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.bg,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
          child: Column(
            children: [
              const SizedBox(height: 20),
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
              const SizedBox(height: 8),
              Text('MT5 CONNECTION',
                  style: monoStyle(
                      fontSize: 10,
                      color: AppColors.dimText,
                      letterSpacing: 4)),
              const SizedBox(height: 24),
              if (_loadingAccounts)
                const Padding(
                  padding: EdgeInsets.all(20),
                  child: CircularProgressIndicator(
                      strokeWidth: 2, color: AppColors.cyan),
                )
              else ...[
                if (_accounts.isNotEmpty) ...[
                  _existingAccountsSection(),
                  const SizedBox(height: 16),
                  _divider(),
                  const SizedBox(height: 16),
                ],
                _newAccountForm(),
              ],
              const SizedBox(height: 16),
              if (_error != null)
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(10),
                  margin: const EdgeInsets.only(bottom: 12),
                  color: AppColors.red.withValues(alpha: 0.1),
                  child: Text(_error!,
                      style: monoStyle(fontSize: 9, color: AppColors.red)),
                ),
              if (_isLoading && _statusMessage.isNotEmpty)
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(10),
                  margin: const EdgeInsets.only(bottom: 12),
                  color: AppColors.cyan.withValues(alpha: 0.08),
                  child: Row(
                    children: [
                      const SizedBox(
                        width: 12,
                        height: 12,
                        child: CircularProgressIndicator(
                            strokeWidth: 1.5, color: AppColors.cyan),
                      ),
                      const SizedBox(width: 10),
                      Text(_statusMessage,
                          style: monoStyle(
                              fontSize: 9,
                              color: AppColors.cyan,
                              letterSpacing: 1)),
                    ],
                  ),
                ),
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.all(12),
                color: AppColors.surface,
                child: Column(
                  children: [
                    Row(
                      children: [
                        const Icon(Icons.info_outline,
                            color: AppColors.dimText, size: 14),
                        const SizedBox(width: 8),
                        Text('CONNECTION INFO',
                            style: monoStyle(
                                fontSize: 9,
                                color: AppColors.dimText,
                                letterSpacing: 1)),
                      ],
                    ),
                    const SizedBox(height: 6),
                    Text(
                        'Your MT5 credentials are encrypted and stored securely. '
                        'The trading engine will start automatically after connection.',
                        style: monoStyle(fontSize: 9, color: AppColors.dimText)),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _existingAccountsSection() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surface,
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('SAVED ACCOUNTS',
              style: monoStyle(
                  fontSize: 9,
                  color: AppColors.dimText,
                  letterSpacing: 2)),
          const SizedBox(height: 12),
          ..._accounts.map((account) {
            final accountNumber = account['account_number'] as String? ?? '';
            final server = account['server'] as String? ?? '';
            final status = account['connection_status'] as String? ?? 'DISCONNECTED';
            final accountId = account['id'] as String;
            final isConnected = status == 'CONNECTED';

            return GestureDetector(
              onTap: _isLoading ? null : () => _connectExisting(accountId),
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.all(12),
                margin: const EdgeInsets.only(bottom: 8),
                decoration: BoxDecoration(
                  color: AppColors.bg,
                  border: Border.all(
                    color: isConnected ? AppColors.green : AppColors.border,
                  ),
                ),
                child: Row(
                  children: [
                    Container(
                      width: 32,
                      height: 32,
                      decoration: BoxDecoration(
                        border: Border.all(
                            color: isConnected
                                ? AppColors.green
                                : AppColors.dimText),
                      ),
                      child: Icon(
                        Icons.account_balance,
                        color: isConnected ? AppColors.green : AppColors.dimText,
                        size: 16,
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(accountNumber,
                              style: monoStyle(
                                  fontSize: 12,
                                  color: AppColors.text,
                                  fontWeight: FontWeight.bold)),
                          const SizedBox(height: 2),
                          Text(server,
                              style: monoStyle(
                                  fontSize: 9, color: AppColors.dimText)),
                        ],
                      ),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 8, vertical: 4),
                      color: isConnected
                          ? AppColors.green.withValues(alpha: 0.12)
                          : AppColors.cyan.withValues(alpha: 0.08),
                      child: Text(
                        isConnected ? 'CONNECTED' : 'CONNECT',
                        style: monoStyle(
                            fontSize: 8,
                            color: isConnected ? AppColors.green : AppColors.cyan,
                            fontWeight: FontWeight.bold,
                            letterSpacing: 1),
                      ),
                    ),
                  ],
                ),
              ),
            );
          }),
        ],
      ),
    );
  }

  Widget _divider() {
    return Row(
      children: [
        Expanded(child: Container(height: 1, color: AppColors.border)),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12),
          child: Text('OR ADD NEW',
              style: monoStyle(
                  fontSize: 8,
                  color: AppColors.dimText,
                  letterSpacing: 2)),
        ),
        Expanded(child: Container(height: 1, color: AppColors.border)),
      ],
    );
  }

  Widget _newAccountForm() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surface,
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('NEW MT5 ACCOUNT',
              style: monoStyle(
                  fontSize: 9,
                  color: AppColors.dimText,
                  letterSpacing: 2)),
          const SizedBox(height: 16),
          _inputField(
            label: 'SERVER',
            controller: _serverController,
            hint: 'MetaQuotes-Demo',
            icon: Icons.dns_outlined,
          ),
          const SizedBox(height: 12),
          _inputField(
            label: 'LOGIN',
            controller: _loginController,
            hint: 'Account number',
            icon: Icons.person_outline,
            keyboardType: TextInputType.number,
          ),
          const SizedBox(height: 12),
          _inputField(
            label: 'PASSWORD',
            controller: _passwordController,
            hint: 'Trading password',
            icon: Icons.lock_outline,
            obscure: _obscurePassword,
            suffixIcon: GestureDetector(
              onTap: () => setState(() => _obscurePassword = !_obscurePassword),
              child: Icon(
                _obscurePassword ? Icons.visibility_off : Icons.visibility,
                color: AppColors.dimText,
                size: 18,
              ),
            ),
          ),
          const SizedBox(height: 16),
          GestureDetector(
            onTap: _isLoading ? null : _connectNew,
            child: Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(vertical: 14),
              decoration: BoxDecoration(
                border: Border.all(
                    color: _isLoading ? AppColors.dimText : AppColors.cyan),
                color: _isLoading
                    ? AppColors.dimText.withValues(alpha: 0.05)
                    : AppColors.cyan.withValues(alpha: 0.08),
              ),
              child: Center(
                child: Text('CONNECT & START TRADING',
                    style: monoStyle(
                        fontSize: 12,
                        color: _isLoading ? AppColors.dimText : AppColors.cyan,
                        fontWeight: FontWeight.bold,
                        letterSpacing: 2)),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _inputField({
    required String label,
    required TextEditingController controller,
    required String hint,
    required IconData icon,
    bool obscure = false,
    Widget? suffixIcon,
    TextInputType? keyboardType,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label,
            style: monoStyle(
                fontSize: 8, color: AppColors.dimText, letterSpacing: 2)),
        const SizedBox(height: 4),
        Container(
          decoration: BoxDecoration(
            color: AppColors.bg,
            border: Border.all(color: AppColors.border),
          ),
          child: Row(
            children: [
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 10),
                child: Icon(icon, color: AppColors.dimText, size: 16),
              ),
              Expanded(
                child: TextField(
                  controller: controller,
                  obscureText: obscure,
                  keyboardType: keyboardType,
                  style: monoStyle(fontSize: 12, color: AppColors.text),
                  decoration: InputDecoration(
                    hintText: hint,
                    hintStyle: monoStyle(fontSize: 11, color: AppColors.dimText),
                    border: InputBorder.none,
                    contentPadding: const EdgeInsets.symmetric(vertical: 12),
                    isDense: true,
                  ),
                ),
              ),
              if (suffixIcon != null)
                Padding(
                  padding: const EdgeInsets.only(right: 10),
                  child: suffixIcon,
                ),
            ],
          ),
        ),
      ],
    );
  }
}
