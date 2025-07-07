int touchLine(ArrayList<Line> Lines) {
  boolean touched = false;
  for (int i = Lines.size()-1; i > 0; i--) {
    if (touched) break;
    Line lines = Lines.get(i);
    float sx = lines.sx;
    float sy = lines.sy;
    float ex = lines.ex;
    float ey = lines.ey;

    if (lines instanceof JustLine) {
      if(isPointOnLine(sx, sy, ex, ey))touched = true;
    } else if (lines instanceof LLine) {
      LLine Llines = (LLine) lines;
      float mx = Llines.mx;
      float my = Llines.my;
      if(isPointOnLine(sx, sy, mx, my) || isPointOnLine(mx, my, ex, ey))touched = true;
    } else if (lines instanceof BracketLine) {
      BracketLine Blines = (BracketLine) lines;
      float m1x = Blines.m1x;
      float m1y = Blines.m1y;
      float m2x = Blines.m2x;
      float m2y = Blines.m2y;
      if(isPointOnLine(sx, sy, m1x, m1y) || isPointOnLine(m1x, m1y, m2x, m2y) || isPointOnLine(m2x, m2y, ex, ey))touched = true;
    }
    if (touched) {
      return i;
    }
  }
  return -1;
}

boolean isPointOnLine(float startX, float startY, float endX, float endY) {
  // 垂直線の処理
  if (startX == endX) {
    if (mouseX == (int)startX && isBetween(startY, endY, mouseY)) {
      return true;
    }
  } else {
    // 傾きと切片の計算
    float slope = (endY - startY) / (endX - startX);
    float intercept = startY - slope * startX;
    
    // マウスのY座標が線の方程式に一致するか確認（四捨五入を使用）
    if (mouseY == (int)Math.round(slope * mouseX + intercept)) {
      if (isBetween(startX, endX, mouseX) && isBetween(startY, endY, mouseY)) {
        return true;
      }
    }
  }
  return false;
}

boolean isBetween(float start, float end, float value) {
  return (start < end) ? (start <= value && value <= end) : (end <= value && value <= start);
}
