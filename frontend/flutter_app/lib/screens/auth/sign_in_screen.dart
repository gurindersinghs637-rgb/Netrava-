import 'package:flutter/material.dart';
import '../../core/network/api_client.dart';
import '../../providers/session.dart';
import '../../widgets/clinical_widgets.dart';
import 'sign_up_screen.dart';
import 'forgot_password_screen.dart';

/// Email/password sign-in using the existing backend contract.
class SignInScreen extends StatefulWidget {
  final Session session;
  const SignInScreen({super.key, required this.session});
  @override
  State<SignInScreen> createState() => _SignInScreenState();
}

class _SignInScreenState extends State<SignInScreen> {
  final _form = GlobalKey<FormState>();
  final _email = TextEditingController(), _password = TextEditingController();
  bool _hidden = true, _busy = false;
  String? _error;
  @override
  void dispose() {
    _email.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _login() async {
    if (_busy || !_form.currentState!.validate()) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await widget.session.login(_email.text.trim(), _password.text);
    } catch (e) {
      if (mounted) {
        setState(
          () => _error = e is ApiFailure
              ? e.message
              : 'Unable to save your secure session. Please retry.',
        );
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    body: SafeArea(
      child: PageBody(
        children: [
          const SizedBox(height: 36),
          const BrandMark(),
          const SizedBox(height: 40),
          const SectionHeading(
            'A clearer tomorrow.',
            subtitle:
                'Your intelligent companion for retinal screening. Sign in to your private workspace.',
          ),
          ClinicalCard(
            child: Form(
              key: _form,
              child: Column(
                children: [
                  TextFormField(
                    controller: _email,
                    keyboardType: TextInputType.emailAddress,
                    autofillHints: const [AutofillHints.username],
                    textInputAction: TextInputAction.next,
                    decoration: const InputDecoration(
                      labelText: 'Email address',
                      prefixIcon: Icon(Icons.mail_outline),
                    ),
                    validator: (v) =>
                        v == null ||
                            !RegExp(
                              r'^[^\s@]+@[^\s@]+\.[^\s@]+$',
                            ).hasMatch(v.trim())
                        ? 'Enter a valid email address.'
                        : null,
                  ),
                  const SizedBox(height: 20),
                  TextFormField(
                    controller: _password,
                    obscureText: _hidden,
                    autofillHints: const [AutofillHints.password],
                    onFieldSubmitted: (_) => _login(),
                    decoration: InputDecoration(
                      labelText: 'Password',
                      prefixIcon: const Icon(Icons.lock_outline),
                      suffixIcon: IconButton(
                        tooltip: _hidden ? 'Show password' : 'Hide password',
                        onPressed: () => setState(() => _hidden = !_hidden),
                        icon: Icon(
                          _hidden
                              ? Icons.visibility_off_outlined
                              : Icons.visibility_outlined,
                        ),
                      ),
                    ),
                    validator: (v) => (v?.length ?? 0) < 8
                        ? 'Use at least 8 characters.'
                        : null,
                  ),
                  const SizedBox(height: 24),
                  ErrorNotice(_error),
                  PrimaryAction('Log in', busy: _busy, onPressed: _login),
                  TextButton(
                    onPressed: _busy
                        ? null
                        : () => Navigator.of(context).push(
                            MaterialPageRoute<void>(
                              builder: (_) => ForgotPasswordScreen(
                                session: widget.session,
                                initialEmail: _email.text.trim(),
                              ),
                            ),
                          ),
                    child: const Text('Forgot Password?'),
                  ),
                ],
              ),
            ),
          ),
          TextButton(
            onPressed: _busy
                ? null
                : () async {
                    final message = await Navigator.of(context).push<String>(
                      MaterialPageRoute(
                        builder: (_) => SignUpScreen(session: widget.session),
                      ),
                    );
                    if (context.mounted && message != null) {
                      ScaffoldMessenger.of(
                        context,
                      ).showSnackBar(SnackBar(content: Text(message)));
                    }
                  },
            child: const Text('New to NETRAVA? Sign up'),
          ),
          const SizedBox(height: 12),
          const Text(
            'New accounts receive a private screening workspace. Your data stays within your workspace.',
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 36),
          const Center(child: Text('TOGETHER FOR CLEARER TOMORROWS')),
        ],
      ),
    ),
  );
}
