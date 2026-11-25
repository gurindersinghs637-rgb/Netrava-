import 'dart:io';
import 'dart:typed_data';
import 'package:flutter_test/flutter_test.dart';
import 'package:netrava/services/pdf_files.dart';
import 'package:open_filex/open_filex.dart';

void main() {
  test(
    'saves exact PDF privately, hands file to viewer and clears on logout',
    () async {
      final dir = await Directory(
        'build/report-file-tests',
      ).create(recursive: true);
      String? opened;
      final files = PdfFiles(
        directory: () async => dir,
        open: (path) async {
          opened = path;
          return OpenResult(type: ResultType.done, message: 'done');
        },
      );
      final bytes = Uint8List.fromList('%PDF-1.4\nfixture'.codeUnits);
      expect(await files.saveAndOpen('ai-test', bytes), contains('opened'));
      expect(await File(opened!).readAsBytes(), bytes);
      expect(File(opened!).parent.path, dir.path);
      await files.clear();
      expect(await dir.exists(), false);
    },
  );
  test('invalid PDF is rejected before saving or opening', () async {
    final files = PdfFiles(
      open: (_) async => throw StateError('must not open'),
    );
    await expectLater(
      files.saveAndOpen('test', Uint8List(2)),
      throwsFormatException,
    );
  });
  test(
    'missing viewer gives a useful message while preserving the PDF',
    () async {
      final dir = await Directory(
        'build/report-no-viewer-test',
      ).create(recursive: true);
      final files = PdfFiles(
        directory: () async => dir,
        open: (_) async =>
            OpenResult(type: ResultType.noAppToOpen, message: 'No app'),
      );
      try {
        expect(
          await files.saveAndOpen(
            'test',
            Uint8List.fromList('%PDF-1.4'.codeUnits),
          ),
          contains('No PDF viewer is installed'),
        );
        expect(await File('${dir.path}/netrava-test.pdf').exists(), isTrue);
      } finally {
        await files.clear();
      }
    },
  );
  test('viewer error is not reported as success', () async {
    final dir = await Directory(
      'build/report-viewer-error-test',
    ).create(recursive: true);
    final files = PdfFiles(
      directory: () async => dir,
      open: (_) async =>
          OpenResult(type: ResultType.error, message: 'Device failure'),
    );
    try {
      await expectLater(
        files.saveAndOpen('test', Uint8List.fromList('%PDF-1.4'.codeUnits)),
        throwsA(isA<FileSystemException>()),
      );
    } finally {
      await files.clear();
    }
  });
}
