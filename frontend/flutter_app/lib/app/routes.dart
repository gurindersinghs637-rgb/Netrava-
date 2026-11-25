import 'package:flutter/material.dart';
import '../core/constants/app_constants.dart';
import '../features/welcome/welcome_screen.dart';
import '../screens/login_screen.dart';

/// Navigation routes setup for NETRAVA application.
class AppRoutes {
  AppRoutes._();

  static Map<String, WidgetBuilder> get routes {
    return {
      AppConstants.routeWelcome: (context) => const WelcomeScreen(),
      AppConstants.routeLogin: (context) => const LoginScreen(),
    };
  }
}
