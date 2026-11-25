import 'package:flutter/material.dart';
import '../core/theme/app_colors.dart';
import '../core/theme/app_text_styles.dart';

/// Shared rounded clinical card.
class ClinicalCard extends StatelessWidget {
  final Widget child;
  final Color? color;
  const ClinicalCard({super.key, required this.child, this.color});
  @override
  Widget build(BuildContext context) => Container(
    width: double.infinity,
    margin: const EdgeInsets.only(bottom: 16),
    child: Material(
      color: color ?? AppColors.cardWhite,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(24),
        side: const BorderSide(color: AppColors.border),
      ),
      clipBehavior: Clip.antiAlias,
      child: Padding(padding: const EdgeInsets.all(20), child: child),
    ),
  );
}

/// Friendly multiline errors for network and clinical validation responses.
class ErrorNotice extends StatelessWidget {
  final String? message;
  const ErrorNotice(this.message, {super.key});
  @override
  Widget build(BuildContext context) => message == null
      ? const SizedBox.shrink()
      : ClinicalCard(
          color: Theme.of(context).colorScheme.errorContainer,
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Icon(Icons.info_outline),
              const SizedBox(width: 12),
              Expanded(child: Text(message!, style: AppTextStyles.bodyMd)),
            ],
          ),
        );
}

/// Primary action that disables duplicate requests.
class PrimaryAction extends StatelessWidget {
  final String label;
  final VoidCallback? onPressed;
  final bool busy;
  final IconData icon;
  const PrimaryAction(
    this.label, {
    super.key,
    this.onPressed,
    this.busy = false,
    this.icon = Icons.arrow_forward_rounded,
  });
  @override
  Widget build(BuildContext context) => SizedBox(
    width: double.infinity,
    child: FilledButton.icon(
      onPressed: busy ? null : onPressed,
      icon: busy
          ? const SizedBox(
              width: 19,
              height: 19,
              child: CircularProgressIndicator(strokeWidth: 2),
            )
          : Icon(icon),
      label: Text(label),
    ),
  );
}

/// Consistent screen heading and supporting text.
class SectionHeading extends StatelessWidget {
  final String title;
  final String? subtitle;
  const SectionHeading(this.title, {super.key, this.subtitle});
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: 24),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(title, style: AppTextStyles.welcomeHeaderDark),
        if (subtitle != null) ...[
          const SizedBox(height: 8),
          Text(subtitle!, style: AppTextStyles.bodyMd),
        ],
      ],
    ),
  );
}

/// Key/value presentation that wraps long identifiers and clinical notes.
class ClinicalDataRow extends StatelessWidget {
  final String label;
  final Object? value;
  const ClinicalDataRow(this.label, this.value, {super.key});
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 7),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: AppTextStyles.labelSm.copyWith(color: AppColors.textSecondary),
        ),
        const SizedBox(height: 3),
        SelectableText(
          value?.toString() ?? 'Not recorded',
          style: AppTextStyles.bodyMd,
        ),
      ],
    ),
  );
}

/// Responsive scrollable content for phone and tablet layouts.
class PageBody extends StatelessWidget {
  final List<Widget> children;
  const PageBody({super.key, required this.children});
  @override
  Widget build(BuildContext context) => Align(
    alignment: Alignment.topCenter,
    child: ConstrainedBox(
      constraints: const BoxConstraints(maxWidth: 680),
      child: ListView(padding: const EdgeInsets.all(24), children: children),
    ),
  );
}

/// Reference-inspired brand lockup without network-dependent assets.
class BrandMark extends StatelessWidget {
  const BrandMark({super.key});
  @override
  Widget build(BuildContext context) => const Column(
    mainAxisSize: MainAxisSize.min,
    children: [
      Icon(Icons.spa_rounded, color: AppColors.primaryGreen, size: 54),
      Text('NETRAVA', style: AppTextStyles.brandTitle),
      SizedBox(height: 8),
      Text('SEE. DETECT. EXPLAIN.', style: AppTextStyles.brandTagline),
    ],
  );
}

/// Decision-support disclaimer shared by results and reports.
const clinicalDisclaimer =
    'AI supports clinical decisions. A qualified clinician must review the retinal images and findings before diagnosis.';
