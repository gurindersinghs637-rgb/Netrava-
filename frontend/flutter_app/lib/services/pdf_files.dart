import 'dart:io';
import 'dart:typed_data';
import 'package:open_filex/open_filex.dart';
import 'package:path_provider/path_provider.dart';

/// App-private PDF files. Downloaded clinical files are cleared on logout/startup.
class PdfFiles {
  static final PdfFiles instance = PdfFiles();
  final Future<Directory> Function()? directory;
  final Future<OpenResult> Function(String)? open;
  PdfFiles({this.directory, this.open});
  Future<Directory> _directory() async {
    if (directory != null) return directory!();
    final root = await getTemporaryDirectory();
    return Directory('${root.path}/netrava_reports');
  }

  Future<String> saveAndOpen(String id, Uint8List bytes) async {
    if (bytes.length < 5 || String.fromCharCodes(bytes.take(5)) != '%PDF-') {
      throw const FormatException('The server did not return a valid PDF.');
    }
    final dir = await _directory();
    await dir.create(recursive: true);
    final safeId = id.replaceAll(RegExp('[^a-zA-Z0-9-]'), '');
    final file = File('${dir.path}/netrava-$safeId.pdf');
    await file.writeAsBytes(bytes, flush: true);
    final result = open != null
        ? await open!(file.path)
        : await OpenFilex.open(file.path, type: 'application/pdf');
    if (result.type == ResultType.done) return 'Report downloaded and opened.';
    if (result.type == ResultType.noAppToOpen) {
      return 'Report saved in private app storage. No PDF viewer is installed. Install a PDF viewer, then tap View Report again.';
    }
    throw const FileSystemException(
      'The report was saved, but the device could not open it. Please retry.',
    );
  }

  Future<void> clear() async {
    final dir = await _directory();
    if (await dir.exists()) await dir.delete(recursive: true);
  }
}
