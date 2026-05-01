import 'package:flutter/material.dart';

class AppColors {
  static const bg = Color(0xFF0A0E14);
  static const surface = Color(0xFF111822);
  static const border = Color(0xFF1E2A3A);
  static const cyan = Color(0xFF00E5FF);
  static const cyanDim = Color(0xFF005F6B);
  static const green = Color(0xFF00E676);
  static const red = Color(0xFFFF1744);
  static const amber = Color(0xFFFFD740);
  static const dimText = Color(0xFF5C7A99);
  static const text = Color(0xFFB0BEC5);
}

const kMono = TextStyle(fontFamily: 'monospace');

TextStyle monoStyle({
  double fontSize = 11,
  Color color = AppColors.text,
  FontWeight fontWeight = FontWeight.normal,
  double letterSpacing = 0,
}) {
  return TextStyle(
    fontFamily: 'monospace',
    fontSize: fontSize,
    color: color,
    fontWeight: fontWeight,
    letterSpacing: letterSpacing,
  );
}
