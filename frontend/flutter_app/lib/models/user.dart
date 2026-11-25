/// Trusted identity returned by the backend; the client never selects a role.
class UserProfile {
  final String id, email, fullName, role;
  final String? clinicName;
  const UserProfile({
    required this.id,
    required this.email,
    required this.fullName,
    required this.role,
    this.clinicName,
  });
  factory UserProfile.fromJson(Map<String, dynamic> j) => UserProfile(
    id: j['id'],
    email: j['email'],
    fullName: j['full_name'],
    role: j['role'],
    clinicName: j['clinic_name'],
  );
  bool get canReview => role == 'ophthalmologist' || role == 'administrator';
  String get roleLabel => switch (role) {
    'technician' => 'Field technician',
    'ophthalmologist' => 'Ophthalmologist',
    'administrator' => 'Administrator',
    _ => role,
  };
}
