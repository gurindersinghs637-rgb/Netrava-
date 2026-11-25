import 'package:flutter/material.dart';
import '../../../core/constants/app_constants.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_text_styles.dart';

/// Reusable NetravaBottomWaves Widget.
/// Draws multi-layered organic flowing healthcare wave shapes and leaf decorations
/// matching the bottom section of the reference design.
class NetravaBottomWaves extends StatelessWidget {
  final double height;

  const NetravaBottomWaves({super.key, this.height = 220});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: height,
      width: double.infinity,
      child: Stack(
        alignment: Alignment.bottomCenter,
        children: [
          // Wave Painter Background
          Positioned.fill(child: CustomPaint(painter: _WavePainter())),

          // Footer Text overlay positioned near the bottom center
          Positioned(
            bottom: 24,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Text(
                  AppConstants.footerTagline,
                  style: AppTextStyles.footerText,
                ),
                const SizedBox(height: 6),
                Container(
                  width: 28,
                  height: 3,
                  decoration: BoxDecoration(
                    color: AppColors.primaryGreen,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _WavePainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final w = size.width;
    final h = size.height;

    // --- LAYER 1: Soft Mint Light Tint Wave (Backmost) ---
    final paintLightTint = Paint()
      ..color = const Color(0xFFD5F0E4).withValues(alpha: 0.7)
      ..style = PaintingStyle.fill
      ..isAntiAlias = true;

    final pathLight = Path();
    pathLight.moveTo(0, h * 0.35);
    pathLight.quadraticBezierTo(w * 0.25, h * 0.05, w * 0.55, h * 0.30);
    pathLight.quadraticBezierTo(w * 0.80, h * 0.50, w, h * 0.20);
    pathLight.lineTo(w, h);
    pathLight.lineTo(0, h);
    pathLight.close();
    canvas.drawPath(pathLight, paintLightTint);

    // --- LAYER 2: Medium Mint Wave ---
    final paintMediumMint = Paint()
      ..color = const Color(0xFF88CBB1).withValues(alpha: 0.65)
      ..style = PaintingStyle.fill
      ..isAntiAlias = true;

    final pathMedium = Path();
    pathMedium.moveTo(0, h * 0.55);
    pathMedium.quadraticBezierTo(w * 0.35, h * 0.25, w * 0.70, h * 0.55);
    pathMedium.quadraticBezierTo(w * 0.88, h * 0.70, w, h * 0.45);
    pathMedium.lineTo(w, h);
    pathMedium.lineTo(0, h);
    pathMedium.close();
    canvas.drawPath(pathMedium, paintMediumMint);

    // --- LAYER 3: Secondary Green Wave ---
    final paintSecondaryGreen = Paint()
      ..color = AppColors.secondaryGreen.withValues(alpha: 0.55)
      ..style = PaintingStyle.fill
      ..isAntiAlias = true;

    final pathSecondary = Path();
    pathSecondary.moveTo(0, h * 0.70);
    pathSecondary.quadraticBezierTo(w * 0.28, h * 0.50, w * 0.60, h * 0.72);
    pathSecondary.quadraticBezierTo(w * 0.82, h * 0.88, w, h * 0.62);
    pathSecondary.lineTo(w, h);
    pathSecondary.lineTo(0, h);
    pathSecondary.close();
    canvas.drawPath(pathSecondary, paintSecondaryGreen);

    // --- LAYER 4: Primary Dark Green Base Wave (Frontmost) ---
    final paintDarkGreen = Paint()
      ..color = AppColors.primaryGreen.withValues(alpha: 0.35)
      ..style = PaintingStyle.fill
      ..isAntiAlias = true;

    final pathDark = Path();
    pathDark.moveTo(0, h * 0.82);
    pathDark.quadraticBezierTo(w * 0.30, h * 0.68, w * 0.65, h * 0.85);
    pathDark.quadraticBezierTo(w * 0.85, h * 0.95, w, h * 0.78);
    pathDark.lineTo(w, h);
    pathDark.lineTo(0, h);
    pathDark.close();
    canvas.drawPath(pathDark, paintDarkGreen);

    // --- BOTTOM-LEFT FOLIAGE / LEAF ACCENTS ---
    _drawFoliageLeaf(
      canvas,
      origin: Offset(w * 0.05, h * 0.65),
      size: Size(38, 55),
      angle: -0.4,
      color: AppColors.secondaryGreen.withValues(alpha: 0.85),
    );

    _drawFoliageLeaf(
      canvas,
      origin: Offset(w * 0.12, h * 0.75),
      size: Size(32, 48),
      angle: 0.1,
      color: AppColors.primaryGreen.withValues(alpha: 0.8),
    );

    _drawFoliageLeaf(
      canvas,
      origin: Offset(w * 0.02, h * 0.45),
      size: Size(28, 42),
      angle: -0.7,
      color: const Color(0xFF6BB599).withValues(alpha: 0.8),
    );
  }

  void _drawFoliageLeaf(
    Canvas canvas, {
    required Offset origin,
    required Size size,
    required double angle,
    required Color color,
  }) {
    canvas.save();
    canvas.translate(origin.dx, origin.dy);
    canvas.rotate(angle);

    final leafPaint = Paint()
      ..color = color
      ..style = PaintingStyle.fill
      ..isAntiAlias = true;

    final path = Path();
    path.moveTo(0, 0);
    path.cubicTo(
      -size.width * 0.8,
      -size.height * 0.4,
      -size.width * 0.6,
      -size.height * 0.9,
      0,
      -size.height,
    );
    path.cubicTo(
      size.width * 0.6,
      -size.height * 0.9,
      size.width * 0.8,
      -size.height * 0.4,
      0,
      0,
    );
    path.close();

    canvas.drawPath(path, leafPaint);
    canvas.restore();
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
