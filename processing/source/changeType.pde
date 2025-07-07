void changeLineType() {
  if (mousePressed) {
    if (c1m) {
      changeLineColor(justLines, color(255, 0, 0));
      changeLineColor(lLines, color(255, 0, 0));
      changeLineColor(bracketLines, color(255, 0, 0));
    }
    if (c2m) {
      changeLineColor(justLines, color(200, 0, 255));
      changeLineColor(lLines, color(200, 0, 255));
      changeLineColor(bracketLines, color(200, 0, 255));
    }
    if (c3m) {
      changeLineColor(justLines, color(0, 255, 255));
      changeLineColor(lLines, color(0, 255, 255));
      changeLineColor(bracketLines, color(0, 255, 255));
    }
    if (c5m) {
      changeLineColor(justLines, color(255, 130, 0));
      changeLineColor(lLines, color(255, 130, 0));
      changeLineColor(bracketLines, color(255, 130, 0));
    }
    if (c10m) {
      changeLineColor(justLines, color(0, 255, 0));
      changeLineColor(lLines, color(0, 255, 0));
      changeLineColor(bracketLines, color(0, 255, 0));
    }
    if (c15m) {
      changeLineColor(justLines, color(0, 0, 255));
      changeLineColor(lLines, color(0, 0, 255));
      changeLineColor(bracketLines, color(0, 0, 255));
    }
    if (cpower) {
      changeLineColor(justLines, color(0));
      changeLineColor(lLines, color(0));
      changeLineColor(bracketLines, color(0));
    }
  }
  stroke(0);
}

void changeLineColor(ArrayList<Line> Lines, color c) {
  if (touchLine(Lines) != -1)Lines.get(touchLine(Lines)).c = c;
}
