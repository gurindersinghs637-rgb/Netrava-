import 'package:flutter/material.dart';

/// Centralized color palette for the NETRAVA application based on the reference design.
class AppColors {
  AppColors._();
  static const Color referralBackground = Color(0xFFFEF0E0);

  // Primary palette matching NETRAVA reference
  static const Color primaryGreen = Color(0xFF075E4D); // Rich deep forest green
  static const Color secondaryGreen = Color(0xFF3C9A78); // Vibrant leaf green
  static const Color accentMint = Color(0xFF90CBB5); // Soft mint accent
  static const Color lightGreen = Color(0xFFEAF7F1); // Light background tint
  static const Color featureIconBg = Color(
    0xFFE5F5EE,
  ); // Soft mint box background

  // Wave painter layered green shades
  static const Color waveDark = Color(0xFF075E4D);
  static const Color waveMedium = Color(0xFF23846C);
  static const Color waveLight = Color(0xFF5EB395);
  static const Color waveSoftTint = Color(0xFFA5DEC8);

  // Backgrounds
  static const Color background = Color(
    0xFFF5FAF7,
  ); // Off-white mint background
  static const Color cardWhite = Color(0xFFFFFFFF);

  // Text colors
  static const Color textPrimary = Color(0xFF1E293B); // Dark navy / charcoal
  static const Color textSecondary = Color(0xFF5C6B73); // Muted slate gray
  static const Color textMuted = Color(
    0xFF4A7C70,
  ); // Muted teal-green for footer

  // Borders & Dividers
  static const Color border = Color(0xFFE0ECE6);
  static const Color dividerLine = Color(0xFFD3E2DC);

  // Shadows
  static const Color buttonShadow = Color(0x10075E4D);
}
