import 'dart:convert';
import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../models/patient.dart';
import '../../models/prediction.dart';
import '../../models/screening.dart';
import '../../providers/session.dart';
import '../../widgets/clinical_widgets.dart';
import '../reports/ai_report_screen.dart';

/// Real prediction, class probabilities and model attention visualization.
class ResultScreen extends StatelessWidget {
  final Session session;
  final Patient patient;
  final Screening screening;
  final RetinalUpload image;
  final Prediction prediction;
  const ResultScreen({
    super.key,
    required this.session,
    required this.patient,
    required this.screening,
    required this.image,
    required this.prediction,
  });
  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Screening result')),
    body: SafeArea(
      child: PageBody(
        children: [
          SectionHeading(
            'A view into the result.',
            subtitle: '${patient.name} • ${screening.eye}',
          ),
          ClinicalCard(
            color: prediction.referral
                ? AppColors.referralBackground
                : AppColors.featureIconBg,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Grade ${prediction.grade} · ${prediction.label}',
                  style: Theme.of(context).textTheme.headlineSmall,
                ),
                const SizedBox(height: 12),
                Text(
                  'Confidence ${(prediction.confidence * 100).toStringAsFixed(1)}%',
                ),
                const SizedBox(height: 10),
                LinearProgressIndicator(value: prediction.confidence),
                const SizedBox(height: 16),
                Text(
                  prediction.referral
                      ? 'Ophthalmologist referral recommended'
                      : 'No AI referral recommendation',
                ),
              ],
            ),
          ),
          const SectionHeading('Retinal image'),
          ClipRRect(
            borderRadius: BorderRadius.circular(20),
            child: Image.memory(image.bytes, height: 260, fit: BoxFit.contain),
          ),
          const SizedBox(height: 24),
          const SectionHeading(
            'Why this prediction?',
            subtitle:
                'Highlighted regions contributed to the model’s prediction. This visualization is not lesion segmentation.',
          ),
          ClinicalCard(child: _heatmap()),
          const SectionHeading('Five-class probabilities'),
          ClinicalCard(
            child: Column(
              children: [
                for (final p in prediction.probabilities)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 16),
                    child: Column(
                      children: [
                        Row(
                          children: [
                            Expanded(
                              child: Text('${p['grade']} · ${p['class_name']}'),
                            ),
                            Text(
                              '${((p['probability'] as num) * 100).toStringAsFixed(1)}%',
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        LinearProgressIndicator(
                          value: (p['probability'] as num).toDouble(),
                        ),
                      ],
                    ),
                  ),
              ],
            ),
          ),
          ClinicalDataRow('Screening ID', screening.id),
          ClinicalDataRow('Prediction ID', prediction.json['prediction_id']),
          ClinicalDataRow(
            'Model processing time',
            '${prediction.json['inference_time_ms']} ms',
          ),
          if (prediction.json['persistence_status'] != 'persisted')
            const ErrorNotice(
              'This prediction has not been saved. A persisted prediction is required to generate an AI screening report.',
            ),
          const SizedBox(height: 16),
          PrimaryAction(
            'Generate AI Screening Report',
            icon: Icons.picture_as_pdf_outlined,
            onPressed:
                prediction.json['persistence_status'] != 'persisted' ||
                    prediction.json['prediction_id'] == null
                ? null
                : () => Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (_) => AiReportScreen(
                        session: session,
                        screeningId: screening.id,
                        generateOnOpen: true,
                        predictionId:
                            prediction.json['prediction_id'] as String,
                      ),
                    ),
                  ),
          ),
          const SizedBox(height: 20),
          const Text(clinicalDisclaimer),
        ],
      ),
    ),
  );
  Widget _heatmap() {
    final encoded = prediction.heatmapBase64;
    if (encoded != null) {
      try {
        return Image.memory(
          base64Decode(encoded),
          height: 280,
          fit: BoxFit.contain,
          errorBuilder: (_, _, _) =>
              const Text('The explanation image could not be displayed.'),
        );
      } catch (_) {
        /* Fall back to the server-provided signed URL. */
      }
    }
    final url = prediction.heatmapUrl;
    if (url == null) return const Text('No explanation image was returned.');
    return Image.network(
      url,
      height: 280,
      fit: BoxFit.contain,
      errorBuilder: (_, _, _) => const Text(
        'The image link may have expired. Explanation links last 30 minutes.',
      ),
    );
  }
}
