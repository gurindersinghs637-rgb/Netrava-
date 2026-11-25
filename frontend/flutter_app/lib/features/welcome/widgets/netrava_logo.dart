import 'package:flutter/material.dart';
import '../../../core/constants/app_constants.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_text_styles.dart';

/// Reusable NetravaLogo Widget.
/// Draws the leaf symbol emblem with custom vector painting and branding typography.
class NetravaLogo extends StatelessWidget {
  final double size;

  const NetravaLogo({super.key, this.size = 1.0});

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        // Custom Painted Leaf Emblem matching the reference image
        SizedBox(
          width: 72 * size,
          height: 52 * size,
          child: CustomPaint(painter: _NetravaLeafPainter()),
        ),
        SizedBox(height: 8 * size),

        // Brand Name "NETRAVA"
        Text(
          AppConstants.appName,
          style: AppTextStyles.brandTitle.copyWith(
            fontSize: 32 * size,
            letterSpacing: 3.5 * size,
          ),
        ),
        SizedBox(height: 4 * size),

        // Tagline "SEE. DETECT. EXPLAIN."
        Text(
          AppConstants.appTagline,
          style: AppTextStyles.brandTagline.copyWith(
            fontSize: 10.5 * size,
            letterSpacing: 4.2 * size,
          ),
        ),
        SizedBox(height: 10 * size),

        // Horizontal accent line below logo
        Container(
          width: 32 * size,
          height: 3 * size,
          decoration: BoxDecoration(
            color: AppColors.secondaryGreen,
            borderRadius: BorderRadius.circular(2),
          ),
        ),
      ],
    );
  }
}

/// CustomPainter that renders the two organic leaf shapes from the reference image.
class _NetravaLeafPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final w = size.width;
    final h = size.height;

    // --- LEFT LEAF (Primary Dark Green) ---
    final leftLeafPaint = Paint()
      ..color = AppColors.primaryGreen
      ..style = PaintingStyle.fill
      ..isAntiAlias = true;

    final leftPath = Path();
    leftPath.moveTo(w * 0.49, h * 0.95);
    leftPath.cubicTo(
      w * 0.05,
      h * 0.85,
      w * 0.02,
      h * 0.28,
      w * 0.45,
      h * 0.04,
    );
    leftPath.cubicTo(
      w * 0.52,
      h * 0.35,
      w * 0.50,
      h * 0.70,
      w * 0.49,
      h * 0.95,
    );
    leftPath.close();
    canvas.drawPath(leftPath, leftLeafPaint);

    // Left Leaf Vein
    final veinPaint = Paint()
      ..color = AppColors.lightGreen.withValues(alpha: 0.6)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.8
      ..strokeCap = StrokeCap.round
      ..isAntiAlias = true;

    final leftVein = Path();
    leftVein.moveTo(w * 0.48, h * 0.90);
    leftVein.quadraticBezierTo(w * 0.26, h * 0.55, w * 0.32, h * 0.16);
    canvas.drawPath(leftVein, veinPaint);

    // --- RIGHT LEAF (Secondary Green) ---
    final rightLeafPaint = Paint()
      ..color = AppColors.secondaryGreen
      ..style = PaintingStyle.fill
      ..isAntiAlias = true;

    final rightPath = Path();
    rightPath.moveTo(w * 0.51, h * 0.95);
    rightPath.cubicTo(
      w * 0.50,
      h * 0.70,
      w * 0.48,
      h * 0.35,
      w * 0.55,
      h * 0.04,
    );
    rightPath.cubicTo(
      w * 0.98,
      h * 0.28,
      w * 0.95,
      h * 0.85,
      w * 0.51,
      h * 0.95,
    );
    rightPath.close();
    canvas.drawPath(rightPath, rightLeafPaint);

    // Right Leaf Vein
    final rightVein = Path();
    rightVein.moveTo(w * 0.52, h * 0.90);
    rightVein.quadraticBezierTo(w * 0.74, h * 0.55, w * 0.68, h * 0.16);
    canvas.drawPath(rightVein, veinPaint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
