import 'package:flutter/material.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_text_styles.dart';

/// Reusable Feature Highlight Item displaying an icon box and two-line label.
class FeatureItem extends StatelessWidget {
  final Widget icon;
  final String label;

  const FeatureItem({super.key, required this.icon, required this.label});

  /// Factory for Shield / Early Detection
  factory FeatureItem.earlyDetection() {
    return const FeatureItem(
      icon: Icon(
        Icons.verified_user_outlined,
        color: AppColors.primaryGreen,
        size: 26,
      ),
      label: 'Early\nDetection',
    );
  }

  /// Factory for AI-Powered Analysis
  factory FeatureItem.aiAnalysis() {
    return const FeatureItem(
      icon: Icon(
        Icons.psychology_outlined,
        color: AppColors.primaryGreen,
        size: 26,
      ),
      label: 'AI-Powered\nAnalysis',
    );
  }

  /// Factory for Healthier Communities
  factory FeatureItem.healthierCommunities() {
    return const FeatureItem(
      icon: Icon(
        Icons.groups_outlined,
        color: AppColors.primaryGreen,
        size: 26,
      ),
      label: 'Healthier\nCommunities',
    );
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        // Rounded light-green container icon box
        Container(
          width: 54,
          height: 54,
          decoration: BoxDecoration(
            color: AppColors.featureIconBg,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(
              color: AppColors.primaryGreen.withValues(alpha: 0.08),
              width: 1,
            ),
          ),
          child: Center(child: icon),
        ),
        const SizedBox(height: 10),

        // 2-line Label
        Text(
          label,
          textAlign: TextAlign.center,
          style: AppTextStyles.featureTitle,
        ),
      ],
    );
  }
}
