import 'package:flutter/material.dart';
import '../../core/network/api_client.dart';
import '../../providers/session.dart';
import '../../widgets/clinical_widgets.dart';

/// Public registration with an isolated active screening workspace.
class SignUpScreen extends StatefulWidget {
  final Session session;
  const SignUpScreen({super.key, required this.session});
  @override
  State<SignUpScreen> createState() => _SignUpScreenState();
}

class _SignUpScreenState extends State<SignUpScreen> {
  final _form = GlobalKey<FormState>();
  final _name = TextEditingController(), _email = TextEditingController();
  final _phone = TextEditingController();
  final _password = TextEditingController(),
      _confirmation = TextEditingController();
  bool _busy = false, _hidden = true;
  String? _error;

  @override
  void dispose() {
    for (final controller in [
      _name,
      _email,
      _phone,
      _password,
      _confirmation,
    ]) {
      controller.dispose();
    }
    super.dispose();
  }

  Future<void> _submit() async {
    if (_busy || !_form.currentState!.validate()) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final message = await widget.session.auth.signup(
        _name.text.trim(),
        _email.text.trim(),
        _phone.text.trim(),
        _password.text,
        _confirmation.text,
      );
      if (mounted) {
        Navigator.of(context).pop(message);
      }
      _password.clear();
      _confirmation.clear();
    } catch (e) {
      if (mounted) {
        setState(
          () => _error = e is ApiFailure
              ? e.message
              : 'Unable to register. Please try again.',
        );
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Widget _fields() => Form(
    key: _form,
    child: Column(
      children: [
        TextFormField(
          controller: _name,
          maxLength: 120,
          autofillHints: const [AutofillHints.name],
          decoration: const InputDecoration(labelText: 'Full name'),
          validator: (v) =>
              (v?.trim().length ?? 0) < 2 ? 'Enter your full name.' : null,
        ),
        TextFormField(
          controller: _email,
          keyboardType: TextInputType.emailAddress,
          autofillHints: const [AutofillHints.email],
          decoration: const InputDecoration(labelText: 'Email address'),
          validator: (v) =>
              !RegExp(r'^[^\s@]+@[^\s@]+\.[^\s@]+$').hasMatch(v?.trim() ?? '')
              ? 'Enter a valid email address.'
              : null,
        ),
        TextFormField(
          controller: _phone,
          keyboardType: TextInputType.phone,
          autofillHints: const [AutofillHints.telephoneNumber],
          maxLength: 25,
          decoration: const InputDecoration(labelText: 'Phone number'),
          validator: (v) {
            final value = v?.trim() ?? '';
            final digits = value.replaceAll(RegExp(r'[^0-9]'), '');
            return !RegExp(r'^\+?[0-9 ()-]+$').hasMatch(value) ||
                    digits.length < 7 ||
                    digits.length > 15
                ? 'Enter a valid phone number (7 to 15 digits).'
                : null;
          },
        ),
        TextFormField(
          controller: _password,
          obscureText: _hidden,
          maxLength: 128,
          autofillHints: const [AutofillHints.newPassword],
          decoration: InputDecoration(
            labelText: 'Password',
            suffixIcon: IconButton(
              tooltip: _hidden ? 'Show passwords' : 'Hide passwords',
              onPressed: () => setState(() => _hidden = !_hidden),
              icon: Icon(
                _hidden
                    ? Icons.visibility_off_outlined
                    : Icons.visibility_outlined,
              ),
            ),
          ),
          validator: (v) =>
              (v?.length ?? 0) < 12 ? 'Use at least 12 characters.' : null,
        ),
        TextFormField(
          controller: _confirmation,
          obscureText: _hidden,
          maxLength: 128,
          decoration: const InputDecoration(labelText: 'Confirm password'),
          validator: (v) => v != _password.text || (v?.isEmpty ?? true)
              ? 'Passwords must match.'
              : null,
        ),
        const SizedBox(height: 24),
        ErrorNotice(_error),
        PrimaryAction('Create account', busy: _busy, onPressed: _submit),
      ],
    ),
  );

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Sign up')),
    body: SafeArea(
      child: PageBody(
        children: [
          const BrandMark(),
          const SizedBox(height: 24),
          const SectionHeading(
            'Create your account',
            subtitle:
                'Create an account to start screening in your private workspace.',
          ),
          ClinicalCard(child: _fields()),
          TextButton(
            onPressed: _busy ? null : () => Navigator.of(context).pop(),
            child: const Text('Already have an account? Log in'),
          ),
        ],
      ),
    ),
  );
}
