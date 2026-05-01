import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

class AuthScreen extends StatefulWidget {
  final VoidCallback onLogin;
  const AuthScreen({super.key, required this.onLogin});

  @override
  State<AuthScreen> createState() => _AuthScreenState();
}

class _AuthScreenState extends State<AuthScreen> {
  bool _isLogin = true;
  bool _showForgot = false;
  bool _obscure = true;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.bg,
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 32),
            child: _showForgot ? _forgotForm() : _authForm(),
          ),
        ),
      ),
    );
  }

  Widget _authForm() {
    return Column(
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
        const SizedBox(height: 8),
        Text('TRADING TERMINAL',
            style: monoStyle(
                fontSize: 10,
                color: AppColors.dimText,
                letterSpacing: 4)),
        const SizedBox(height: 40),
        Row(
          children: [
            _tabBtn('LOGIN', _isLogin),
            const SizedBox(width: 4),
            _tabBtn('REGISTER', !_isLogin),
          ],
        ),
        const SizedBox(height: 20),
        if (!_isLogin) ...[
          _field('DISPLAY NAME', Icons.person_outline),
          const SizedBox(height: 12),
        ],
        _field('EMAIL', Icons.email_outlined),
        const SizedBox(height: 12),
        _passwordField(),
        if (!_isLogin) ...[
          const SizedBox(height: 12),
          _field('CONFIRM PASSWORD', Icons.lock_outline, obscure: true),
        ],
        if (_isLogin) ...[
          const SizedBox(height: 10),
          Align(
            alignment: Alignment.centerRight,
            child: GestureDetector(
              onTap: () => setState(() => _showForgot = true),
              child: Text('FORGOT PASSWORD?',
                  style: monoStyle(
                      fontSize: 9,
                      color: AppColors.cyan,
                      letterSpacing: 1)),
            ),
          ),
        ],
        const SizedBox(height: 24),
        GestureDetector(
          onTap: widget.onLogin,
          child: Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(vertical: 14),
            decoration: BoxDecoration(
              color: AppColors.cyan.withValues(alpha: 0.12),
              border: Border.all(color: AppColors.cyan),
            ),
            child: Center(
              child: Text(
                _isLogin ? 'AUTHENTICATE' : 'CREATE ACCOUNT',
                style: monoStyle(
                    fontSize: 12,
                    color: AppColors.cyan,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 2),
              ),
            ),
          ),
        ),
        const SizedBox(height: 16),
        _divider(),
        const SizedBox(height: 16),
        _socialButton('SIGN IN WITH GOOGLE', Icons.g_mobiledata),
        const SizedBox(height: 30),
        GestureDetector(
          onTap: () => setState(() => _isLogin = !_isLogin),
          child: RichText(
            text: TextSpan(
              style: monoStyle(fontSize: 10, color: AppColors.dimText),
              children: [
                TextSpan(
                    text: _isLogin
                        ? 'No account? '
                        : 'Already have an account? '),
                TextSpan(
                  text: _isLogin ? 'REGISTER' : 'LOGIN',
                  style: monoStyle(
                      fontSize: 10,
                      color: AppColors.cyan,
                      fontWeight: FontWeight.bold),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _forgotForm() {
    return Column(
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
        const SizedBox(height: 30),
        Text('RESET PASSWORD',
            style: monoStyle(
                fontSize: 11,
                color: AppColors.dimText,
                letterSpacing: 3)),
        const SizedBox(height: 8),
        Text('Enter your email to receive a reset link',
            style: monoStyle(fontSize: 10, color: AppColors.dimText)),
        const SizedBox(height: 24),
        _field('EMAIL', Icons.email_outlined),
        const SizedBox(height: 20),
        Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(vertical: 14),
          decoration: BoxDecoration(
            color: AppColors.cyan.withValues(alpha: 0.12),
            border: Border.all(color: AppColors.cyan),
          ),
          child: Center(
            child: Text('SEND RESET LINK',
                style: monoStyle(
                    fontSize: 12,
                    color: AppColors.cyan,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 2)),
          ),
        ),
        const SizedBox(height: 20),
        GestureDetector(
          onTap: () => setState(() => _showForgot = false),
          child: Text('< BACK TO LOGIN',
              style: monoStyle(
                  fontSize: 10,
                  color: AppColors.cyan,
                  letterSpacing: 1)),
        ),
      ],
    );
  }

  Widget _tabBtn(String label, bool active) {
    return Expanded(
      child: GestureDetector(
        onTap: () => setState(() => _isLogin = label == 'LOGIN'),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 8),
          decoration: BoxDecoration(
            color: active
                ? AppColors.cyan.withValues(alpha: 0.1)
                : Colors.transparent,
            border: Border(
              bottom: BorderSide(
                color: active ? AppColors.cyan : AppColors.border,
                width: active ? 2 : 1,
              ),
            ),
          ),
          child: Center(
            child: Text(label,
                style: monoStyle(
                    fontSize: 10,
                    color: active ? AppColors.cyan : AppColors.dimText,
                    fontWeight:
                        active ? FontWeight.bold : FontWeight.normal,
                    letterSpacing: 2)),
          ),
        ),
      ),
    );
  }

  Widget _field(String label, IconData icon, {bool obscure = false}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label,
            style: monoStyle(
                fontSize: 9,
                color: AppColors.dimText,
                letterSpacing: 1)),
        const SizedBox(height: 4),
        Container(
          decoration: BoxDecoration(
            border: Border.all(color: AppColors.border),
            color: AppColors.surface,
          ),
          child: TextField(
            obscureText: obscure,
            style: monoStyle(fontSize: 12, color: AppColors.text),
            decoration: InputDecoration(
              prefixIcon: Icon(icon, color: AppColors.dimText, size: 18),
              border: InputBorder.none,
              contentPadding: const EdgeInsets.symmetric(
                  horizontal: 12, vertical: 10),
              hintText: label.toLowerCase(),
              hintStyle: monoStyle(
                  fontSize: 11,
                  color: AppColors.border),
            ),
          ),
        ),
      ],
    );
  }

  Widget _passwordField() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('PASSWORD',
            style: monoStyle(
                fontSize: 9,
                color: AppColors.dimText,
                letterSpacing: 1)),
        const SizedBox(height: 4),
        Container(
          decoration: BoxDecoration(
            border: Border.all(color: AppColors.border),
            color: AppColors.surface,
          ),
          child: TextField(
            obscureText: _obscure,
            style: monoStyle(fontSize: 12, color: AppColors.text),
            decoration: InputDecoration(
              prefixIcon: const Icon(Icons.lock_outline,
                  color: AppColors.dimText, size: 18),
              suffixIcon: GestureDetector(
                onTap: () => setState(() => _obscure = !_obscure),
                child: Icon(
                  _obscure
                      ? Icons.visibility_off_outlined
                      : Icons.visibility_outlined,
                  color: AppColors.dimText,
                  size: 18,
                ),
              ),
              border: InputBorder.none,
              contentPadding: const EdgeInsets.symmetric(
                  horizontal: 12, vertical: 10),
              hintText: 'password',
              hintStyle: monoStyle(
                  fontSize: 11, color: AppColors.border),
            ),
          ),
        ),
      ],
    );
  }

  Widget _divider() {
    return Row(
      children: [
        Expanded(child: Container(height: 1, color: AppColors.border)),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12),
          child:
              Text('OR', style: monoStyle(fontSize: 9, color: AppColors.dimText)),
        ),
        Expanded(child: Container(height: 1, color: AppColors.border)),
      ],
    );
  }

  Widget _socialButton(String label, IconData icon) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 12),
      decoration: BoxDecoration(
        border: Border.all(color: AppColors.border),
        color: AppColors.surface,
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, color: AppColors.text, size: 20),
          const SizedBox(width: 8),
          Text(label,
              style: monoStyle(
                  fontSize: 10,
                  color: AppColors.text,
                  letterSpacing: 1)),
        ],
      ),
    );
  }
}
