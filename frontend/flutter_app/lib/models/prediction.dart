/// AI classification and explainability returned by the prediction endpoint.
class Prediction {
  final Map<String, dynamic> json;
  Prediction.fromJson(this.json);
  int get grade => json['predicted_grade'];
  String get label => json['severity_label'];
  double get confidence => (json['confidence_score'] as num).toDouble();
  bool get referral => json['is_referral_recommended'] == true;
  List<dynamic> get probabilities => json['probabilities'];
  String? get heatmapUrl => json['explanation']?['heatmap_signed_url'];
  String? get heatmapBase64 => json['explanation']?['heatmap_base64'];
}
