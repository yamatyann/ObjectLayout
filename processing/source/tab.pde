boolean standing=true, objecting=false, dmxing=false, fileing=false;
void tabs() {
  standTab();
  objectTab();
  dmxTab();
  fileTab();
}

void standTab() {
  if (mousePressed && !standing && 2*width/13-width/10<=mouseX && mouseX<=2*width/13+width/10 && 550-35<=mouseY && mouseY<=550+35) {
    standing=true;
    objecting=false;
    dmxing=false;

    par = false;
    deco = false;
    bar = false;
    desk = false;
    denkei = false;
    other = false;

    lineType = false;
    connect = false;
  }
  if (standing) {

    stroke(0);
    fill(200);
    rect(width/10, height/2-50, width/5, height-100);

    table();
    stand();
    truss();
  }
}

void table() {
  stroke(0);
  fill(200);
  rect(width/10, height/4-50, width/6, height/10);
  fill(0);
  textSize(30);
  text("table", width/10, height/4-50);
}

void stand() {
  stroke(0);
  fill(200);
  rect(width/10, height/2-50, width/6, height/10);
  fill(0);
  textSize(30);
  text("stand", width/10, height/2-50);
}

void truss() {
  stroke(0);
  fill(200);
  rect(width/10, 3*height/4-50, width/6, height/10);
  fill(0);
  textSize(30);
  text("truss", width/10, 3*height/4-50);
}

void objectTab() {
  if (mousePressed && !objecting && 5*width/13-width/10<=mouseX && mouseX<=5*width/13+width/10 && 550-35<=mouseY && mouseY<=550+35) {
    standing=false;
    objecting=true;
    dmxing=false;

    table = false;
    stand = false;
    truss = false;

    lineType = false;
    connect = false;
  }
  if (objecting) {

    stroke(0);
    fill(200);
    rect(width/10, height/2-50, width/5, height-100);

    par();
    decoration();
    colorBar();
    desk();
    denkei();
    other();
  }
}

void par() {
  stroke(0);
  fill(200);
  rect(width/10, height/7-50, width/6, height/10);
  fill(0);
  textSize(30);
  text("Par", width/10, height/7-50);
}

void decoration() {
  stroke(0);
  fill(200);
  rect(width/10, 2*height/7-50, width/6, height/10);
  fill(0);
  textSize(30);
  text("decoration", width/10, 2*height/7-50);
}

void colorBar() {
  stroke(0);
  fill(200);
  rect(width/10, 3*height/7-50, width/6, height/10);
  fill(0);
  textSize(30);
  text("colorBar", width/10, 3*height/7-50);
}

void desk() {
  stroke(0);
  fill(200);
  rect(width/10, 4*height/7-50, width/6, height/10);
  fill(0);
  textSize(30);
  text("desk", width/10, 4*height/7-50);
}

void denkei() {
  stroke(0);
  fill(200);
  rect(width/10, 5*height/7-50, width/6, height/10);
  fill(0);
  textSize(30);
  text("denkei", width/10, 5*height/7-50);
}

void other() {
  stroke(0);
  fill(200);
  rect(width/10, 6*height/7-50, width/6, height/10);
  fill(0);
  textSize(30);
  text("other", width/10, 6*height/7-50);
}

void dmxTab() {
  if (mousePressed && !dmxing && 8*width/13-width/10<=mouseX && mouseX<=8*width/13+width/10 && 550-35<=mouseY && mouseY<=550+35) {
    standing=false;
    objecting=false;
    dmxing=true;

    par = false;
    deco = false;
    bar = false;
    desk = false;
    denkei = false;
    other = false;

    table = false;
    stand = false;
    truss = false;
  }
  if (dmxing) {

    stroke(0);
    fill(200);
    rect(width/10, height/2-50, width/5, height-100);

    connect();
    lineType();
  }
}

void connect() {
  stroke(0);
  fill(200);
  rect(width/10, height/3-50, width/6, height/10);
  fill(0);
  textSize(30);
  text("connect", width/10, height/3-50);
}

void lineType() {
  stroke(0);
  fill(200);
  rect(width/10, 2*height/3-50, width/6, height/10);
  fill(0);
  textSize(30);
  text("line type", width/10, 2*height/3-50);
}

void fileTab() {
  if (mousePressed && !fileing && 11*width/13-width/10<=mouseX && mouseX<=11*width/13+width/10 && 550-35<=mouseY && mouseY<=550+35) {
    standing=false;
    objecting=false;
    dmxing=false;
    fileing=true;

    par = false;
    deco = false;
    bar = false;
    desk = false;
    denkei = false;
    other = false;

    table = false;
    stand = false;
    truss = false;

    lineType = false;
    connect = false;
  }
  if (fileing) {

    stroke(0);
    fill(200);
    rect(width/10, height/2-50, width/5, height-100);
    
    choseOperation();
  }
}
