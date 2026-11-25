import 'package:flutter/material.dart';
import '../../core/constants/app_constants.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_text_styles.dart';
import 'widgets/auth_button.dart';
import 'widgets/background_decorations.dart';
import 'widgets/bottom_waves.dart';
import 'widgets/feature_item.dart';
import 'widgets/netrava_logo.dart';

/// The Main Welcome Screen for NETRAVA.
/// Reproduces the reference image design with responsive layout, custom widgets, and interaction behaviors.
class WelcomeScreen extends StatelessWidget {
  const WelcomeScreen({super.key});

  /// Displays help dialog
  void _showHelpDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (dialogContext) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: const Row(
          children: [
            Icon(
              Icons.help_outline_rounded,
              color: AppColors.primaryGreen,
              size: 28,
            ),
            SizedBox(width: 10),
            Text('Need help?'),
          ],
        ),
        content: const Text(
          'Contact the NETRAVA support team.',
          style: TextStyle(fontSize: 15, color: AppColors.textPrimary),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(),
            child: const Text(
              'OK',
              style: TextStyle(
                color: AppColors.primaryGreen,
                fontWeight: FontWeight.bold,
                fontSize: 16,
              ),
            ),
          ),
        ],
      ),
    );
  }

  /// Displays placeholder dialog for Google / Microsoft Sign-In
  void _showPlaceholderDialog(
    BuildContext context,
    String title,
    String message,
  ) {
    showDialog(
      context: context,
      builder: (dialogContext) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: Text(
          title,
          style: const TextStyle(
            color: AppColors.primaryGreen,
            fontWeight: FontWeight.bold,
          ),
        ),
        content: Text(
          message,
          style: const TextStyle(fontSize: 15, color: AppColors.textPrimary),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(),
            child: const Text(
              'OK',
              style: TextStyle(
                color: AppColors.primaryGreen,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      body: Stack(
        children: [
          // 1. Ambient Background Decorations
          const BackgroundDecorations(),

          // 2. Organic Bottom Waves Layer
          const Positioned(
            left: 0,
            right: 0,
            bottom: 0,
            child: NetravaBottomWaves(height: 200),
          ),

          // 3. Scrollable Main Content Stack
          SafeArea(
            child: Align(
              alignment: Alignment.topCenter,
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 440),
                child: LayoutBuilder(
                  builder: (context, constraints) {
                    return SingleChildScrollView(
                      physics: const BouncingScrollPhysics(),
                      padding: const EdgeInsets.symmetric(horizontal: 24),
                      child: ConstrainedBox(
                        constraints: BoxConstraints(
                          minHeight: constraints.maxHeight,
                        ),
                        child: IntrinsicHeight(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.center,
                            children: [
                              const SizedBox(height: 10),

                              // --- TOP-RIGHT: NEED HELP? ---
                              Align(
                                alignment: Alignment.topRight,
                                child: InkWell(
                                  onTap: () => _showHelpDialog(context),
                                  borderRadius: BorderRadius.circular(20),
                                  child: const Padding(
                                    padding: EdgeInsets.symmetric(
                                      horizontal: 8,
                                      vertical: 4,
                                    ),
                                    child: Row(
                                      mainAxisSize: MainAxisSize.min,
                                      children: [
                                        Text(
                                          AppConstants.helpText,
                                          style: AppTextStyles.needHelp,
                                        ),
                                        SizedBox(width: 5),
                                        Icon(
                                          Icons.help_outline_rounded,
                                          size: 18,
                                          color: AppColors.textPrimary,
                                        ),
                                      ],
                                    ),
                                  ),
                                ),
                              ),

                              const SizedBox(height: 12),

                              // --- BRANDING SECTION ---
                              const NetravaLogo(),

                              const SizedBox(height: 18),

                              // --- WELCOME MESSAGE ---
                              RichText(
                                textAlign: TextAlign.center,
                                text: const TextSpan(
                                  children: [
                                    TextSpan(
                                      text: AppConstants.welcomeTitlePrefix,
                                      style: AppTextStyles.welcomeHeaderDark,
                                    ),
                                    TextSpan(
                                      text: AppConstants.welcomeTitleName,
                                      style: AppTextStyles.welcomeHeaderGreen,
                                    ),
                                  ],
                                ),
                              ),
                              const SizedBox(height: 6),

                              const Text(
                                AppConstants.welcomeSubtitle,
                                textAlign: TextAlign.center,
                                style: AppTextStyles.welcomeSubtitle,
                              ),

                              const SizedBox(height: 22),

                              // --- AUTHENTICATION OPTIONS ---
                              AuthButton.email(
                                onTap: () => Navigator.pushNamed(
                                  context,
                                  AppConstants.routeLogin,
                                ),
                              ),
                              AuthButton.google(
                                onTap: () => _showPlaceholderDialog(
                                  context,
                                  'Google Sign-In',
                                  'Google Sign-In will be connected later.',
                                ),
                              ),
                              AuthButton.microsoft(
                                onTap: () => _showPlaceholderDialog(
                                  context,
                                  'Microsoft Sign-In',
                                  'Microsoft Sign-In will be connected later.',
                                ),
                              ),

                              const SizedBox(height: 16),

                              // --- DIVIDER WITH "OR" ---
                              const Row(
                                children: [
                                  Expanded(
                                    child: Divider(
                                      color: AppColors.dividerLine,
                                      thickness: 1,
                                      indent: 10,
                                      endIndent: 14,
                                    ),
                                  ),
                                  Text('OR', style: AppTextStyles.dividerOr),
                                  Expanded(
                                    child: Divider(
                                      color: AppColors.dividerLine,
                                      thickness: 1,
                                      indent: 14,
                                      endIndent: 10,
                                    ),
                                  ),
                                ],
                              ),

                              const SizedBox(height: 14),

                              // --- LOGIN PROMPT ---
                              Column(
                                children: [
                                  const Text(
                                    AppConstants.loginPrompt,
                                    style: AppTextStyles.loginPrompt,
                                  ),
                                  const SizedBox(height: 2),
                                  InkWell(
                                    onTap: () => Navigator.pushNamed(
                                      context,
                                      AppConstants.routeLogin,
                                    ),
                                    borderRadius: BorderRadius.circular(8),
                                    child: const Padding(
                                      padding: EdgeInsets.symmetric(
                                        horizontal: 8,
                                        vertical: 4,
                                      ),
                                      child: Text(
                                        AppConstants.loginAction,
                                        style: AppTextStyles.loginLink,
                                      ),
                                    ),
                                  ),
                                ],
                              ),

                              const SizedBox(height: 22),

                              // --- FEATURE HIGHLIGHTS ---
                              Row(
                                mainAxisAlignment:
                                    MainAxisAlignment.spaceEvenly,
                                children: [
                                  FeatureItem.earlyDetection(),
                                  FeatureItem.aiAnalysis(),
                                  FeatureItem.healthierCommunities(),
                                ],
                              ),

                              const SizedBox(
                                height: 70,
                              ), // Bottom padding above waves
                            ],
                          ),
                        ),
                      ),
                    );
                  },
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
