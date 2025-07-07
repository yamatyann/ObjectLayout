void menus() {
  stroke(0);
  fill(200);
  rect(width/2, 550, width, 100);

  standButton();
  objectButton();
  dmxButton();
  fileButton();
}

void standButton() {
  stroke(0);
  fill(200);
  rect(2*width/13, 550, width/5, 70);
  fill(0);
  textSize(30);
  text("stand", 2*width/13, 550);
}

void objectButton() {
  stroke(0);
  fill(200);
  rect(5*width/13, 550, width/5, 70);
  fill(0);
  textSize(30);
  text("object", 5*width/13, 550);
}

void dmxButton() {
  stroke(0);
  fill(200);
  rect(8*width/13, 550, width/5, 70);
  fill(0);
  textSize(30);
  text("DMX", 8*width/13, 550);
}

void fileButton() {
  stroke(0);
  fill(200);
  rect(11*width/13, 550, width/5, 70);
  fill(0);
  textSize(30);
  text("File", 11*width/13, 550);
}
