boolean mousePressing = false;
boolean click = false;
void oneClick() {
  if (!mousePressing && mousePressed)click = true;
  else click = false;
  if (mousePressed)mousePressing = true;
  else mousePressing = false;
}
