import 'package:flutter_test/flutter_test.dart';
import 'package:auto/main.dart';
import 'package:auto/services/notification_service.dart';

void main() {
  testWidgets('App renders', (WidgetTester tester) async {
    await tester.pumpWidget(LotApp(notificationService: NotificationService()));
    expect(find.text('LOT'), findsWidgets);
  });
}
