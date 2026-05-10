class AppException implements Exception {
  final String message;
  final int? statusCode;
  final dynamic originalError;

  const AppException(
    this.message, {
    this.statusCode,
    this.originalError,
  });

  @override
  String toString() => 'AppException($statusCode): $message';
}
