import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:firebase_auth/firebase_auth.dart' hide AuthProvider;
import '../theme/app_theme.dart';
import '../providers/auth_provider.dart';

class AuthScreen extends StatefulWidget {
  const AuthScreen({super.key});

  @override
  State<AuthScreen> createState() => _AuthScreenState();
}

class _AuthScreenState extends State<AuthScreen> {
  final GoogleSignIn _googleSignIn = GoogleSignIn(
    scopes: ['email', 'profile'],
    serverClientId: '252783816592-napc8trqt16crjuamnmfbais1cjedrl8.apps.googleusercontent.com',
  );

  Future<void> _handleGoogleLogin() async {
    final auth = context.read<AuthProvider>();

    try {
      final googleUser = await _googleSignIn.signIn();
      if (googleUser == null) return;

      final googleAuth = await googleUser.authentication;

      final credential = GoogleAuthProvider.credential(
        accessToken: googleAuth.accessToken,
        idToken: googleAuth.idToken,
      );

      final userCredential =
          await FirebaseAuth.instance.signInWithCredential(credential);

      final firebaseToken = await userCredential.user?.getIdToken();
      if (firebaseToken == null) {
        auth.setError('Failed to get Firebase ID token');
        return;
      }

      await auth.loginWithGoogle(firebaseToken);
    } catch (e) {
      auth.setError(e.toString());
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();

    return Scaffold(
      backgroundColor: AppColors.bg,
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 32),
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
                const SizedBox(height: 8),
                Text('TRADING TERMINAL',
                    style: monoStyle(
                        fontSize: 10,
                        color: AppColors.dimText,
                        letterSpacing: 4)),
                const SizedBox(height: 48),
                Text('AUTHENTICATION',
                    style: monoStyle(
                        fontSize: 11,
                        color: AppColors.dimText,
                        letterSpacing: 3)),
                const SizedBox(height: 8),
                Text('Sign in with your Google account to access the trading terminal.',
                    textAlign: TextAlign.center,
                    style: monoStyle(fontSize: 10, color: AppColors.dimText)),
                const SizedBox(height: 32),
                if (auth.error != null) ...[
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(10),
                    margin: const EdgeInsets.only(bottom: 16),
                    color: AppColors.red.withValues(alpha: 0.1),
                    child: Text(auth.error!,
                        style: monoStyle(fontSize: 9, color: AppColors.red)),
                  ),
                ],
                GestureDetector(
                  onTap: auth.isLoading ? null : _handleGoogleLogin,
                  child: Container(
                    width: double.infinity,
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    decoration: BoxDecoration(
                      border: Border.all(color: AppColors.cyan),
                      color: AppColors.cyan.withValues(alpha: 0.08),
                    ),
                    child: Center(
                      child: auth.isLoading
                          ? const SizedBox(
                              width: 16,
                              height: 16,
                              child: CircularProgressIndicator(
                                  strokeWidth: 2, color: AppColors.cyan),
                            )
                          : Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                const Icon(Icons.g_mobiledata,
                                    color: AppColors.cyan, size: 22),
                                const SizedBox(width: 8),
                                Text('SIGN IN WITH GOOGLE',
                                    style: monoStyle(
                                        fontSize: 12,
                                        color: AppColors.cyan,
                                        fontWeight: FontWeight.bold,
                                        letterSpacing: 2)),
                              ],
                            ),
                    ),
                  ),
                ),
                const SizedBox(height: 32),
                Container(
                  padding: const EdgeInsets.all(12),
                  color: AppColors.surface,
                  child: Column(
                    children: [
                      Row(
                        children: [
                          const Icon(Icons.security, color: AppColors.dimText, size: 14),
                          const SizedBox(width: 8),
                          Text('SECURE CONNECTION',
                              style: monoStyle(
                                  fontSize: 9,
                                  color: AppColors.dimText,
                                  letterSpacing: 1)),
                        ],
                      ),
                      const SizedBox(height: 6),
                      Text(
                          'Authentication is handled by Google Firebase. '
                          'Your credentials are never stored on our servers.',
                          style: monoStyle(fontSize: 9, color: AppColors.dimText)),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
