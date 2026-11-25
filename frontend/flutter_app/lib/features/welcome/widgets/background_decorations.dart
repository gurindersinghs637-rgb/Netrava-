import 'package:flutter/material.dart';
import '../../../core/theme/app_colors.dart';

/// Reusable BackgroundDecorations Widget.
/// Renders subtle organic light green curved shapes in top-left and top-right edges
/// to replicate the reference design's calm medical-tech ambiance.
class BackgroundDecorations extends StatelessWidget {
  const BackgroundDecorations({super.key});

  @override
  Widget build(BuildContext context) {
    return Positioned.fill(
      child: IgnorePointer(
        child: CustomPaint(painter: _BackgroundDecorationsPainter()),
      ),
    );
  }
}

class _BackgroundDecorationsPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final w = size.width;
    final h = size.height;

    // --- TOP-LEFT Organic Light Green Curve ---
    final topLeftPaint = Paint()
      ..color = AppColors.lightGreen.withValues(alpha: 0.7)
      ..style = PaintingStyle.fill
      ..isAntiAlias = true;

    final topLeftPath = Path();
    topLeftPath.moveTo(0, 0);
    topLeftPath.lineTo(w * 0.42, 0);
    topLeftPath.cubicTo(w * 0.35, h * 0.12, w * 0.15, h * 0.18, 0, h * 0.22);
    topLeftPath.close();
    canvas.drawPath(topLeftPath, topLeftPaint);

    // --- TOP-LEFT Secondary Subtle Outer Wave ---
    final topLeftOuterPaint = Paint()
      ..color = const Color(0xFFD5F0E4).withValues(alpha: 0.35)
      ..style = PaintingStyle.fill
      ..isAntiAlias = true;

    final topLeftOuterPath = Path();
    topLeftOuterPath.moveTo(0, 0);
    topLeftOuterPath.lineTo(w * 0.58, 0);
    topLeftOuterPath.cubicTo(
      w * 0.45,
      h * 0.18,
      w * 0.20,
      h * 0.26,
      0,
      h * 0.30,
    );
    topLeftOuterPath.close();
    canvas.drawPath(topLeftOuterPath, topLeftOuterPaint);

    // --- TOP-RIGHT Soft Tint Corner ---
    final topRightPaint = Paint()
      ..color = AppColors.lightGreen.withValues(alpha: 0.4)
      ..style = PaintingStyle.fill
      ..isAntiAlias = true;

    final topRightPath = Path();
    topRightPath.moveTo(w * 0.75, 0);
    topRightPath.lineTo(w, 0);
    topRightPath.lineTo(w, h * 0.12);
    topRightPath.quadraticBezierTo(w * 0.85, h * 0.08, w * 0.75, 0);
    topRightPath.close();
    canvas.drawPath(topRightPath, topRightPaint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
