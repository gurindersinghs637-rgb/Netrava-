import 'dart:typed_data';
import 'package:dio/dio.dart';

/// Immutable original bytes shared by upload and prediction; never re-encode.
class RetinalUpload {
  final Uint8List bytes;
  final String filename;
  RetinalUpload({required this.bytes, required this.filename});
  bool get isPng =>
      bytes.length >= 8 &&
      List.generate(8, (i) => bytes[i]).join(',') == '137,80,78,71,13,10,26,10';
  String? validate() {
    if (bytes.length > 15 * 1024 * 1024) {
      return 'Choose an image no larger than 15 MiB.';
    }
    final jpeg =
        bytes.length >= 3 &&
        bytes[0] == 255 &&
        bytes[1] == 216 &&
        bytes[2] == 255;
    if (!isPng && !jpeg) return 'Choose a JPEG or PNG image.';
    return null;
  }

  MultipartFile toMultipart() => MultipartFile.fromBytes(
    bytes,
    filename: isPng ? 'fundus.png' : 'fundus.jpg',
    contentType: DioMediaType('image', isPng ? 'png' : 'jpeg'),
  );
}

/// Persisted upload and quality-control result.
class Screening {
  final String id, imageId, eye, imageUrl;
  final DateTime? createdAt;
  final Map<String, dynamic> qc;
  Screening.fromJson(Map<String, dynamic> j)
    : id = j['screening_id'],
      imageId = j['retinal_image_id'],
      eye = j['eye'],
      imageUrl = j['fundus_image_signed_url'],
      createdAt = DateTime.tryParse(j['created_at']?.toString() ?? ''),
      qc = j['qc_assessment'];
}

/// Saved prediction metadata retained only during the authenticated session.
class AiReportEntry {
  final String screeningId, predictionId, patientName, patientCode, gradeName;
  final int grade;
  final double confidence;
  final DateTime? screeningDate;
  const AiReportEntry({
    required this.screeningId,
    required this.predictionId,
    required this.patientName,
    required this.patientCode,
    required this.gradeName,
    required this.grade,
    required this.confidence,
    this.screeningDate,
  });
}
