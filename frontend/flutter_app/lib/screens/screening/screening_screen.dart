import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../../core/network/api_client.dart';
import '../../models/patient.dart';
import '../../models/screening.dart';
import '../../models/prediction.dart';
import '../../providers/session.dart';
import '../../widgets/clinical_widgets.dart';
import '../results/result_screen.dart';

/// Retinal capture, real quality control, then inference using identical bytes.
class ScreeningScreen extends StatefulWidget {
  final Session session;
  final Patient patient;
  const ScreeningScreen({
    super.key,
    required this.session,
    required this.patient,
  });
  @override
  State<ScreeningScreen> createState() => _ScreeningScreenState();
}

class _ScreeningScreenState extends State<ScreeningScreen> {
  RetinalUpload? _image;
  Screening? _screening;
  Prediction? _prediction;
  Map<String, dynamic>? _rejectedQc;
  String _eye = 'OD';
  String? _error;
  bool _busy = false, _analyzing = false;
  double? _uploadProgress;
  Future<void> _pick(ImageSource source) async {
    if (_busy) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final file = await ImagePicker().pickImage(source: source);
      if (file == null) return;
      if (await file.length() > 15 * 1024 * 1024) {
        throw const ApiFailure('Choose an image no larger than 15 MiB.');
      }
      final image = RetinalUpload(
        bytes: await file.readAsBytes(),
        filename: file.name,
      );
      final failure = image.validate();
      if (failure != null) throw ApiFailure(failure);
      if (mounted) {
        setState(() {
          _image = image;
          _screening = null;
          _prediction = null;
          _rejectedQc = null;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(
          () => _error = e is ApiFailure
              ? e.message
              : 'Unable to access the image. Check camera or photo permissions.',
        );
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _upload() async {
    if (_busy || _image == null || _screening != null) return;
    setState(() {
      _busy = true;
      _error = null;
      _rejectedQc = null;
      _uploadProgress = 0;
    });
    try {
      final screening = await widget.session.screenings.create(
        widget.patient.id,
        _eye,
        _image!,
        onSendProgress: (sent, total) {
          if (mounted && total > 0) {
            setState(() => _uploadProgress = (sent / total).clamp(0.0, 1.0));
          }
        },
      );
      if (!mounted) return;
      setState(() => _screening = screening);
      widget.session.remember(screening.id);
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = e.toString();
          if (e is ApiFailure && e.extra?['qc'] is Map) {
            _rejectedQc = Map<String, dynamic>.from(e.extra!['qc']);
          }
        });
      }
    } finally {
      if (mounted) {
        setState(() {
          _busy = false;
          _uploadProgress = null;
        });
      }
    }
  }

  Future<void> _analyze() async {
    if (_busy || _screening == null || _image == null) return;
    if (_prediction != null) {
      _showResult();
      return;
    }
    setState(() {
      _busy = true;
      _analyzing = true;
      _error = null;
    });
    try {
      final result = await widget.session.predictions.predict(
        _screening!.imageId,
        _image!,
      );
      if (!mounted) return;
      setState(() => _prediction = result);
      final predictionId = result.json['prediction_id'];
      if (result.json['persistence_status'] == 'persisted' &&
          predictionId is String) {
        widget.session.rememberAiReport(
          AiReportEntry(
            screeningId: _screening!.id,
            predictionId: predictionId,
            patientName: widget.patient.name,
            patientCode: widget.patient.code,
            grade: result.grade,
            gradeName: result.label,
            confidence: result.confidence,
            screeningDate: _screening!.createdAt,
          ),
        );
      }
    } catch (e) {
      if (mounted) setState(() => _error = e.toString());
    } finally {
      if (mounted) {
        setState(() {
          _busy = false;
          _analyzing = false;
        });
      }
    }
    if (mounted && _prediction != null) _showResult();
  }

  void _showResult() => Navigator.of(context).push(
    MaterialPageRoute(
      builder: (_) => ResultScreen(
        session: widget.session,
        patient: widget.patient,
        screening: _screening!,
        image: _image!,
        prediction: _prediction!,
      ),
    ),
  );
  @override
  Widget build(BuildContext context) => PopScope(
    canPop: !_busy,
    child: Scaffold(
      appBar: AppBar(
        title: Text(
          _analyzing
              ? 'AI analysis'
              : _screening == null
              ? 'Retinal screening'
              : 'Image quality check',
        ),
      ),
      body: SafeArea(
        child: _analyzing
            ? _analysis()
            : PageBody(
                children: [
                  SectionHeading(
                    _screening == null
                        ? 'Capture a clearer view.'
                        : 'Ready for analysis.',
                    subtitle: '${widget.patient.name} • ${widget.patient.code}',
                  ),
                  SegmentedButton<String>(
                    segments: const [
                      ButtonSegment(
                        value: 'OD',
                        label: Text('Right eye · OD'),
                        icon: Icon(Icons.visibility_outlined),
                      ),
                      ButtonSegment(
                        value: 'OS',
                        label: Text('Left eye · OS'),
                        icon: Icon(Icons.visibility_outlined),
                      ),
                    ],
                    selected: {_eye},
                    onSelectionChanged: _busy || _screening != null
                        ? null
                        : (v) => setState(() => _eye = v.first),
                  ),
                  const SizedBox(height: 24),
                  if (_image != null)
                    ClipRRect(
                      borderRadius: BorderRadius.circular(24),
                      child: Image.memory(
                        _image!.bytes,
                        height: 260,
                        fit: BoxFit.contain,
                        errorBuilder: (_, _, _) => const ClinicalCard(
                          child: Text(
                            'Image preview unavailable. Choose another image.',
                          ),
                        ),
                      ),
                    )
                  else
                    const ClinicalCard(
                      child: Column(
                        children: [
                          Icon(Icons.add_a_photo_outlined, size: 72),
                          SizedBox(height: 20),
                          Text(
                            'Choose a retinal fundus image',
                            textAlign: TextAlign.center,
                          ),
                          SizedBox(height: 8),
                          Text('JPEG or PNG · up to 15 MiB'),
                        ],
                      ),
                    ),
                  const SizedBox(height: 16),
                  if (_screening == null) ...[
                    OutlinedButton.icon(
                      onPressed: _busy
                          ? null
                          : () => _pick(ImageSource.gallery),
                      icon: const Icon(Icons.photo_library_outlined),
                      label: const Text('Import from gallery'),
                    ),
                    OutlinedButton.icon(
                      onPressed: _busy ? null : () => _pick(ImageSource.camera),
                      icon: const Icon(Icons.camera_alt_outlined),
                      label: const Text('Capture image'),
                    ),
                    const SizedBox(height: 12),
                    const Text(
                      'Use a suitable fundus camera or retinal imaging attachment. A standard phone camera alone does not capture diagnostic fundus images.',
                    ),
                  ],
                  const SizedBox(height: 16),
                  ErrorNotice(_error),
                  if (_uploadProgress != null) ...[
                    LinearProgressIndicator(value: _uploadProgress),
                    const SizedBox(height: 8),
                    Text(
                      _uploadProgress! < 1
                          ? 'Uploading image: ${(_uploadProgress! * 100).round()}%'
                          : 'Upload sent. Checking image quality and saving screening...',
                    ),
                    const SizedBox(height: 16),
                  ],
                  if (_rejectedQc != null) _quality(_rejectedQc!, false),
                  if (_screening != null) ...[
                    _quality(_screening!.qc, true),
                    ClinicalDataRow(
                      'Screening ID — retain for clinical review',
                      _screening!.id,
                    ),
                    const SizedBox(height: 16),
                    PrimaryAction(
                      _prediction == null
                          ? 'Continue to AI analysis'
                          : 'View AI result',
                      busy: _busy,
                      onPressed: _analyze,
                    ),
                  ] else
                    PrimaryAction(
                      'Upload & check quality',
                      busy: _busy,
                      onPressed: _image == null ? null : _upload,
                    ),
                ],
              ),
      ),
    ),
  );
  Widget _quality(Map<String, dynamic> qc, bool passed) => ClinicalCard(
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        ListTile(
          contentPadding: EdgeInsets.zero,
          leading: Icon(
            passed ? Icons.check_circle : Icons.warning_amber_rounded,
          ),
          title: Text(
            passed ? 'Image quality passed' : 'Please recapture the image',
          ),
        ),
        ClinicalDataRow('Sharpness score', qc['blur_score']),
        ClinicalDataRow('Illumination', qc['illumination']),
        ClinicalDataRow(
          'QC confidence',
          '${((qc['confidence'] as num) * 100).toStringAsFixed(1)}%',
        ),
      ],
    ),
  );
  Widget _analysis() => const PageBody(
    children: [
      SizedBox(height: 64),
      Center(child: Icon(Icons.biotech_outlined, size: 90)),
      SizedBox(height: 32),
      SectionHeading(
        'Looking a little closer.',
        subtitle:
            'NETRAVA is analyzing retinal features and generating an explanation of the AI result.',
      ),
      LinearProgressIndicator(),
      SizedBox(height: 32),
      ClinicalCard(
        child: Text(
          'Analysis is in progress. Please keep this screen open. Processing time depends on server availability.',
        ),
      ),
      Text(clinicalDisclaimer),
    ],
  );
}
