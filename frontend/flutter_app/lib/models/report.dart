/// Persisted clinical review, separate from the AI prediction.
class ClinicalReport {
  final Map<String, dynamic> json;
  ClinicalReport.fromJson(this.json);
  String get id => json['id'];
  bool get signed => json['is_signed_off'] == true;
  int get grade => json['overall_grade'];
  int? get override => json['grade_override'];
  String? get notes => json['ophthalmologist_notes'];
  bool get urgent => json['is_urgent_referral'] == true;
}
