import 'package:dio/dio.dart';
import '../core/network/api_client.dart';
import '../models/prediction.dart';
import '../models/screening.dart';

/// Prediction requires an image ID in the query and identical original bytes.
class PredictionService {
  final ApiClient api;
  PredictionService(this.api);
  Future<Prediction> predict(String imageId, RetinalUpload image) =>
      api.execute(
        () async => Prediction.fromJson(
          (await api.dio.post(
            '/predict',
            queryParameters: {'retinal_image_id': imageId},
            data: FormData.fromMap({'image': image.toMultipart()}),
          )).data,
        ),
      );
}
