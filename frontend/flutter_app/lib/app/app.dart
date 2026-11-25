import 'package:flutter/material.dart';
import '../core/theme/app_theme.dart';
import '../providers/session.dart';
import '../screens/auth/session_gate.dart';

/// Root Application Widget for NETRAVA.
class NetravaApp extends StatefulWidget {
  final Session? session;
  const NetravaApp({super.key, this.session});
  @override
  State<NetravaApp> createState() => _NetravaAppState();
}

class _NetravaAppState extends State<NetravaApp> {
  late final Session session = widget.session ?? Session();
  final _navigator = GlobalKey<NavigatorState>();
  String? _previousUser;
  @override
  void initState() {
    super.initState();
    session.addListener(_changed);
    session.restore();
  }

  void _changed() {
    final id = session.user?.id;
    if (_previousUser != id) {
      _previousUser = id;
      _navigator.currentState?.popUntil((route) => route.isFirst);
    }
    if (mounted) setState(() {});
  }

  @override
  void dispose() {
    session.removeListener(_changed);
    if (widget.session == null) {
      session.api.dio.close(force: true);
      session.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'NETRAVA',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      navigatorKey: _navigator,
      home: SessionGate(session: session),
    );
  }
}
