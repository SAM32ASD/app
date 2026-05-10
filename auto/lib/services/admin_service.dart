import 'api_client.dart';

class AdminService {
  static final AdminService _instance = AdminService._internal();
  factory AdminService() => _instance;
  AdminService._internal();

  final _api = ApiClient();

  Future<List<Map<String, dynamic>>> getUsers() async {
    final response = await _api.get('/admin/users');
    final data = response.data as Map<String, dynamic>;
    final list = data['users'] as List<dynamic>;
    return list.map((e) => Map<String, dynamic>.from(e as Map)).toList();
  }

  Future<void> updateUserRole(String userId, String newRole) async {
    await _api.put('/admin/users/$userId/role', queryParameters: {'role': newRole});
  }

  Future<Map<String, dynamic>> getAuditLogs({int page = 1, int limit = 50}) async {
    final response = await _api.get(
      '/admin/audit',
      queryParameters: {'page': page, 'per_page': limit},
    );
    return response.data as Map<String, dynamic>;
  }
}
