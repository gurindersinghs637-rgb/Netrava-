import 'package:flutter/material.dart';
import 'app_colors.dart';

/// Centralized text styles hierarchy matching the reference design.
class AppTextStyles {
  AppTextStyles._();
  static const TextStyle labelSm = TextStyle(
    fontSize: 12,
    fontWeight: FontWeight.w600,
  );
  static const TextStyle bodyMd = TextStyle(
    fontSize: 14,
    height: 1.5,
    color: AppColors.textSecondary,
  );

  static const TextStyle brandTitle = TextStyle(
    fontSize: 32,
    fontWeight: FontWeight.w800,
    color: AppColors.primaryGreen,
    letterSpacing: 3.5,
    height: 1.1,
  );

  static const TextStyle brandTagline = TextStyle(
    fontSize: 10.5,
    fontWeight: FontWeight.w600,
    color: AppColors.primaryGreen,
    letterSpacing: 4.0,
  );

  static const TextStyle welcomeHeaderDark = TextStyle(
    fontSize: 25,
    fontWeight: FontWeight.w700,
    color: AppColors.textPrimary,
    letterSpacing: -0.3,
  );

  static const TextStyle welcomeHeaderGreen = TextStyle(
    fontSize: 25,
    fontWeight: FontWeight.w800,
    color: AppColors.primaryGreen,
    letterSpacing: -0.3,
  );

  static const TextStyle welcomeSubtitle = TextStyle(
    fontSize: 15,
    fontWeight: FontWeight.w400,
    color: AppColors.textSecondary,
    height: 1.45,
  );

  static const TextStyle authButtonPrimary = TextStyle(
    fontSize: 15,
    fontWeight: FontWeight.w600,
    color: Colors.white,
    letterSpacing: 0.2,
  );

  static const TextStyle authButtonSecondary = TextStyle(
    fontSize: 15,
    fontWeight: FontWeight.w600,
    color: AppColors.textPrimary,
    letterSpacing: 0.2,
  );

  static const TextStyle loginPrompt = TextStyle(
    fontSize: 14,
    fontWeight: FontWeight.w400,
    color: AppColors.textSecondary,
  );

  static const TextStyle loginLink = TextStyle(
    fontSize: 15,
    fontWeight: FontWeight.w700,
    color: AppColors.primaryGreen,
  );

  static const TextStyle featureTitle = TextStyle(
    fontSize: 12.5,
    fontWeight: FontWeight.w600,
    color: AppColors.textPrimary,
    height: 1.25,
  );

  static const TextStyle footerText = TextStyle(
    fontSize: 9.5,
    fontWeight: FontWeight.w700,
    color: AppColors.textMuted,
    letterSpacing: 2.2,
  );

  static const TextStyle needHelp = TextStyle(
    fontSize: 13,
    fontWeight: FontWeight.w500,
    color: AppColors.textPrimary,
  );

  static const TextStyle dividerOr = TextStyle(
    fontSize: 11.5,
    fontWeight: FontWeight.w600,
    color: AppColors.textSecondary,
    letterSpacing: 1.5,
  );
}
