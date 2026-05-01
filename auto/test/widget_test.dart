import 'package:flutter_test/flutter_test.dart';
import 'package:auto/main.dart';

void main() {
  testWidgets('App renders', (WidgetTester tester) async {
    await tester.pumpWidget(const LotApp());
    expect(find.text('LOT'), findsWidgets);
  });
}
