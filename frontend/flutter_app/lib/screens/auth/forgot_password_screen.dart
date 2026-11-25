import 'package:flutter/material.dart';
import '../../core/network/api_client.dart';
import '../../providers/session.dart';
import '../../widgets/clinical_widgets.dart';

/// Request a recovery email; password selection happens at the trusted reset page.
class ForgotPasswordScreen extends StatefulWidget {
  final Session session;
  final String initialEmail;
  const ForgotPasswordScreen({
    super.key,
    required this.session,
    this.initialEmail = '',
  });
  @override
  State<ForgotPasswordScreen> createState() => _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends State<ForgotPasswordScreen> {
  final _form = GlobalKey<FormState>();
  late final _email = TextEditingController(text: widget.initialEmail);
  bool _busy = false;
  String? _error, _message;
  @override
  void dispose() {
    _email.dispose();
    super.dispose();
  }

  Future<void> _send() async {
    if (_busy || !_form.currentState!.validate()) return;
    setState(() {
      _busy = true;
      _error = null;
      _message = null;
    });
    try {
      final message = await widget.session.auth.forgotPassword(
        _email.text.trim(),
      );
      if (mounted) {
        setState(() => _message = message);
      }
    } catch (e) {
      if (mounted) {
        setState(
          () => _error = e is ApiFailure
              ? e.message
              : 'Unable to request a reset email. Please try again.',
        );
      }
    } finally {
      if (mounted) {
        setState(() => _busy = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Forgot Password')),
    body: SafeArea(
      child: PageBody(
        children: [
          const BrandMark(),
          const SizedBox(height: 24),
          const SectionHeading(
            'Reset your password',
            subtitle:
                'Enter your NETRAVA email. Open the reset email to choose a new password, then return here to log in.',
          ),
          ClinicalCard(
            child: Form(
              key: _form,
              child: Column(
                children: [
                  TextFormField(
                    controller: _email,
                    keyboardType: TextInputType.emailAddress,
                    autofillHints: const [AutofillHints.email],
                    decoration: const InputDecoration(
                      labelText: 'Email address',
                    ),
                    validator: (v) =>
                        RegExp(
                          r'^[^\s@]+@[^\s@]+\.[^\s@]+$',
                        ).hasMatch(v?.trim() ?? '')
                        ? null
                        : 'Enter a valid email address.',
                  ),
                  const SizedBox(height: 24),
                  ErrorNotice(_error),
                  if (_message != null) Text(_message!),
                  PrimaryAction(
                    'Send reset email',
                    busy: _busy,
                    onPressed: _send,
                  ),
                ],
              ),
            ),
          ),
          TextButton(
            onPressed: _busy ? null : () => Navigator.of(context).pop(),
            child: const Text('Back to login'),
          ),
        ],
      ),
    ),
  );
}
