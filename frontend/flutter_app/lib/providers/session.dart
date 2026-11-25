import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../core/network/api_client.dart';
import '../models/user.dart';
import '../models/screening.dart';
import '../services/auth_service.dart';
import '../services/patient_service.dart';
import '../services/prediction_service.dart';
import '../services/report_service.dart';
import '../services/screening_service.dart';
import '../services/pdf_files.dart';

/// Session lifecycle and dependency container; no clinical data is persisted locally.
class Session extends ChangeNotifier {
  final ApiClient api;
  final FlutterSecureStorage storage;
  final Future<void> Function() clearFiles;
  late final auth = AuthService(api);
  late final patients = PatientService(api);
  late final screenings = ScreeningService(api);
  late final predictions = PredictionService(api);
  late final reports = ReportService(api);
  UserProfile? user;
  bool initializing = true;
  String? startupError;
  final List<String> recentScreenings = [];
  final List<AiReportEntry> recentAiReports = [];
  int _generation = 0;
  static const _key = 'netrava_access_token';
  Session({
    ApiClient? client,
    FlutterSecureStorage? secureStorage,
    Future<void> Function()? clearFiles,
  }) : api = client ?? ApiClient(),
       clearFiles = clearFiles ?? PdfFiles.instance.clear,
       storage = secureStorage ?? const FlutterSecureStorage() {
    api.onUnauthorized = () {
      logout();
    };
  }
  Future<void> restore() async {
    initializing = true;
    startupError = null;
    notifyListeners();
    try {
      await clearFiles();
      api.token = await storage.read(key: _key);
      if (api.token != null) user = await auth.me();
    } catch (e) {
      if (e is ApiFailure && (e.status == 401 || e.status == 403)) {
        await logout();
      } else {
        startupError = e is ApiFailure
            ? e.message
            : 'Secure session storage is unavailable. Please retry.';
      }
    } finally {
      initializing = false;
      notifyListeners();
    }
  }

  Future<void> login(String email, String password) async {
    final generation = ++_generation;
    final result = await auth.login(email, password);
    if (generation != _generation) return;
    await storage.write(key: _key, value: result['access_token']);
    if (generation != _generation) {
      await storage.delete(key: _key);
      return;
    }
    api.token = result['access_token'];
    user = UserProfile.fromJson(result['user']);
    startupError = null;
    notifyListeners();
  }

  Future<void> refreshProfile() async {
    final generation = _generation;
    final profile = await auth.me();
    if (generation == _generation) {
      user = profile;
      notifyListeners();
    }
  }

  Future<void> logout() async {
    ++_generation;
    api.token = null;
    user = null;
    recentScreenings.clear();
    recentAiReports.clear();
    startupError = null;
    notifyListeners();
    try {
      await storage.delete(key: _key);
    } catch (_) {
      startupError =
          'Could not clear secure storage. Retry signing out before closing the app.';
      notifyListeners();
    }
    try {
      await clearFiles();
    } catch (_) {
      /* OS also evicts temporary files. */
    }
  }

  void remember(String id) {
    if (user == null) return;
    recentScreenings.remove(id);
    recentScreenings.insert(0, id);
    notifyListeners();
  }

  void rememberAiReport(AiReportEntry entry) {
    if (user == null) return;
    recentAiReports.removeWhere(
      (row) => row.predictionId == entry.predictionId,
    );
    recentAiReports.insert(0, entry);
    notifyListeners();
  }
}
