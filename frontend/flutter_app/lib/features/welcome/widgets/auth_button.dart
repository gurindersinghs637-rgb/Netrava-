import 'package:flutter/material.dart';
import '../../../core/theme/app_colors.dart';

enum AuthButtonType { primaryDark, secondaryLight }

/// Reusable Authentication Button Widget with ripple effect, elevation, and custom branding icons.
class AuthButton extends StatelessWidget {
  final String text;
  final Widget icon;
  final VoidCallback onTap;
  final AuthButtonType type;

  const AuthButton({
    super.key,
    required this.text,
    required this.icon,
    required this.onTap,
    this.type = AuthButtonType.secondaryLight,
  });

  /// Factory for Email Primary Button
  factory AuthButton.email({
    required VoidCallback onTap,
    String text = 'Continue with Email',
  }) {
    return AuthButton(
      text: text,
      onTap: onTap,
      type: AuthButtonType.primaryDark,
      icon: const Icon(Icons.email_outlined, color: Colors.white, size: 22),
    );
  }

  /// Factory for Google Button
  factory AuthButton.google({
    required VoidCallback onTap,
    String text = 'Continue with Google',
  }) {
    return AuthButton(
      text: text,
      onTap: onTap,
      type: AuthButtonType.secondaryLight,
      icon: const _GoogleLogoWidget(),
    );
  }

  /// Factory for Microsoft Button
  factory AuthButton.microsoft({
    required VoidCallback onTap,
    String text = 'Continue with Microsoft',
  }) {
    return AuthButton(
      text: text,
      onTap: onTap,
      type: AuthButtonType.secondaryLight,
      icon: const _MicrosoftLogoWidget(),
    );
  }

  @override
  Widget build(BuildContext context) {
    final bool isPrimary = type == AuthButtonType.primaryDark;

    final Color bgColor = isPrimary
        ? AppColors.primaryGreen
        : AppColors.cardWhite;
    final Color textColor = isPrimary ? Colors.white : AppColors.textPrimary;
    final Color arrowColor = isPrimary ? Colors.white : AppColors.textPrimary;

    return Container(
      height: 54,
      margin: const EdgeInsets.symmetric(vertical: 6.5),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(28),
        border: isPrimary
            ? null
            : Border.all(color: AppColors.border, width: 1.2),
        boxShadow: [
          BoxShadow(
            color: isPrimary
                ? AppColors.primaryGreen.withValues(alpha: 0.2)
                : Colors.black.withValues(alpha: 0.04),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(28),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(28),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20),
            child: Row(
              children: [
                // Left Icon
                SizedBox(width: 26, height: 26, child: Center(child: icon)),
                const SizedBox(width: 14),

                // Button Text
                Expanded(
                  child: Text(
                    text,
                    style: TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.w600,
                      color: textColor,
                      letterSpacing: 0.1,
                    ),
                  ),
                ),

                // Right Arrow Icon
                Icon(Icons.arrow_forward_rounded, color: arrowColor, size: 20),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

/// Custom Vector Widget for Authentic Google 'G' Logo.
class _GoogleLogoWidget extends StatelessWidget {
  const _GoogleLogoWidget();

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 22,
      height: 22,
      child: CustomPaint(painter: _GoogleGPainter()),
    );
  }
}

class _GoogleGPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final double w = size.width;
    final double h = size.height;
    final center = Offset(w / 2, h / 2);
    final radius = w / 2;

    final rect = Rect.fromCircle(center: center, radius: radius);

    // Blue arc (Right)
    final bluePaint = Paint()
      ..color = const Color(0xFF4285F4)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3.8;
    canvas.drawArc(rect, -0.6, 2.0, false, bluePaint);

    // Horizontal bar of G
    final blueFill = Paint()..color = const Color(0xFF4285F4);
    canvas.drawRect(
      Rect.fromLTRB(w * 0.45, h * 0.40, w * 0.95, h * 0.60),
      blueFill,
    );

    // Green arc (Bottom)
    final greenPaint = Paint()
      ..color = const Color(0xFF34A853)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3.8;
    canvas.drawArc(rect, 1.4, 1.4, false, greenPaint);

    // Yellow arc (Bottom Left)
    final yellowPaint = Paint()
      ..color = const Color(0xFFFBBC05)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3.8;
    canvas.drawArc(rect, 2.8, 1.0, false, yellowPaint);

    // Red arc (Top)
    final redPaint = Paint()
      ..color = const Color(0xEAEE4335)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3.8;
    canvas.drawArc(rect, 3.8, 1.8, false, redPaint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

/// Custom Vector Widget for Authentic Microsoft Logo (4 squares).
class _MicrosoftLogoWidget extends StatelessWidget {
  const _MicrosoftLogoWidget();

  @override
  Widget build(BuildContext context) {
    const double size = 19;
    const double gap = 2;
    const double tileSize = (size - gap) / 2;

    return SizedBox(
      width: size,
      height: size,
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                width: tileSize,
                height: tileSize,
                color: const Color(0xFFF25022),
              ), // Red
              const SizedBox(width: gap),
              Container(
                width: tileSize,
                height: tileSize,
                color: const Color(0xFF7FBA00),
              ), // Green
            ],
          ),
          const SizedBox(height: gap),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                width: tileSize,
                height: tileSize,
                color: const Color(0xFF00A4EF),
              ), // Blue
              const SizedBox(width: gap),
              Container(
                width: tileSize,
                height: tileSize,
                color: const Color(0xFFFFB900),
              ), // Yellow
            ],
          ),
        ],
      ),
    );
  }
}
