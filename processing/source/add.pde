boolean Single = true, Double = false, Quattro = false, Remove = false, Replace = false;

int rotate = 0, orotate = 0;
boolean keyPressing = false;
int putsize = 1;
float ox, oy, m1x, m2x, m1y, m2y, x, y;
float x1, x2, x3, x4, y1, y2, y3, y4;
int linePhase = 0;

void SizeButton() {
  stroke(0);
  rectMode(CENTER);
  fill(255);
  if (standing || objecting)rect(width-15, 120, 20, 15);
  if (standing || objecting)rect(width-15, 140, 20, 15);
  if (standing || objecting)rect(width-15, 160, 20, 15);
  rect(width-15, 180, 20, 15);
  rect(width-15, 200, 20, 15);
  textSize(15);
  fill(0);
  if (standing || objecting)text("Single", width-50, 120);
  if (standing || objecting)text("Double", width-50, 140);
  if (standing || objecting)text("Quattro", width-50, 160);
  text("Remove", width-50, 180);
  text("Replace", width-50, 200);

  if (Single && (standing || objecting)) {
    fill(0, 100);
    rect(width-15, 120, 20, 15);
  }
  if (Double && (standing || objecting)) {
    fill(0, 100);
    rect(width-15, 140, 20, 15);
  }
  if (Quattro && (standing || objecting)) {
    fill(0, 100);
    rect(width-15, 160, 20, 15);
  }
  if (Remove) {
    fill(0, 100);
    rect(width-15, 180, 20, 15);
    cTable = false;
    cStand = false;
    cTruss = false;
    cLed = false;
    cMega64 = false;
    cMoving = false;
    cPar12 = false;
    cStrobe = false;
    cDekker = false;
    cOld = false;
    cNew = false;
    cPhantom = false;
    cSceneSetter = false;
    cMini = false;
    cEPar38 = false;
    cLED38B = false;
    cFlatPar = false;
    cBk75 = false;
    cPar20 = false;
    cPar30 = false;
    cPar46 = false;
    cBold = false;
    cDimmerPack = false;
  }
  if (Replace) {
    fill(0, 100);
    rect(width-15, 200, 20, 15);
    cTable = false;
    cStand = false;
    cTruss = false;
    cLed = false;
    cMega64 = false;
    cMoving = false;
    cPar12 = false;
    cStrobe = false;
    cDekker = false;
    cOld = false;
    cNew = false;
    cPhantom = false;
    cSceneSetter = false;
    cMini = false;
    cEPar38 = false;
    cLED38B = false;
    cFlatPar = false;
    cBk75 = false;
    cPar20 = false;
    cPar30 = false;
    cPar46 = false;
    cBold = false;
    cDimmerPack = false;
  }

  if (width-15-20 < mouseX && mouseX < width-15+20 && mousePressed) {
    if (120-15 < mouseY && mouseY < 120+15) {
      Single = true;
      Double = false;
      Quattro = false;
      putsize = 1;
    }
    if (140-15 < mouseY && mouseY < 140+15) {
      Single = false;
      Double = true;
      Quattro = false;
      putsize = 2;
    }
    if (160-15 < mouseY && mouseY < 160+15) {
      Single = false;
      Double = false;
      Quattro = true;
      putsize = 4;
    }
    if (180-15 < mouseY && mouseY < 180+15 && click) {
      Remove = !Remove;
      Replace = false;
    }
    if (200-15 < mouseY && mouseY < 200+15 && click) {
      Replace = !Replace;
      Remove = false;
    }
  }
}

void AddObjects() {
  if (!keyPressing && keyPressed && (key == 'r' || key == 'R')) {
    if (rotate != 11)rotate++;
    else rotate = 0;
  }
  if (keyPressed)keyPressing = true;
  else keyPressing=false;


  if (width/10 + width/5/2 < mouseX && mouseX < width && 50+50 < mouseY && mouseY < 550 - 50) {

    stroke(255, 0, 0);
    if ((width/10+width/5/2+width)/2 - 10 < mouseX && mouseX < (width/10+width/5/2+width)/2 + 10) {
      ox = (width/10+width/5/2+width)/2;
      line((width/10+width/5/2+width)/2, 50+50, (width/10+width/5/2+width)/2, 550-50);
    } else {
      ox = mouseX;
    }

    oy = mouseY;


    drawVerticalLines(leds);
    drawVerticalLines(mega64s);
    drawVerticalLines(movings);
    drawVerticalLines(par12s);
    drawVerticalLines(strobes);
    drawVerticalLines(dekkers);
    drawVerticalLines(oldColorbars);
    drawVerticalLines(newColorbars);
    drawVerticalLines(phantoms);
    drawVerticalLines(sceneSetters);
    drawVerticalLines(miniDesks);
    drawVerticalLines(ePar38s);
    drawVerticalLines(led38Bs);
    drawVerticalLines(flatPars);
    drawVerticalLines(bk75s);
    drawVerticalLines(par20s);
    drawVerticalLines(par30s);
    drawVerticalLines(par46s);
    drawVerticalLines(bolds);
    drawVerticalLines(dimmerPacks);
    drawVerticalLines(tables);
    drawVerticalLines(stands);
    drawVerticalLines(trusses);

    smartGuides(stands);
    smartGuides(trusses);

    stroke(0);


    x = ox*cos(-rotate * 2*PI/12) - oy*sin(-rotate * 2*PI/12);
    y = ox*sin(-rotate * 2*PI/12) + oy*cos(-rotate * 2*PI/12);

    orotate = rotate;


    for (int i = 0; i < putsize; i++) {
      if (putsize == 2) {
        if (i == 1) {
          rotate = 12 - rotate;
          x = ((width/10+width/5/2+width)/2 - (ox - (width/10+width/5/2+width)/2))*cos(-rotate * 2*PI/12) - oy*sin(-rotate * 2*PI/12);
          y = ((width/10+width/5/2+width)/2 - (ox - (width/10+width/5/2+width)/2))*sin(-rotate * 2*PI/12) + oy*cos(-rotate * 2*PI/12);
        }
      } else if (putsize == 4) {
        if (i == 1) {
          x = ((width/10+width/5/2+width)/2 + (ox - (width/10+width/5/2+width)/2)/3)*cos(-rotate * 2*PI/12) - oy*sin(-rotate * 2*PI/12);
          y = ((width/10+width/5/2+width)/2 + (ox - (width/10+width/5/2+width)/2)/3)*sin(-rotate * 2*PI/12) + oy*cos(-rotate * 2*PI/12);
        }
        if (i == 2) {
          rotate = 12 - rotate;
          x = ((width/10+width/5/2+width)/2 - (ox - (width/10+width/5/2+width)/2)/3)*cos(-rotate * 2*PI/12) - oy*sin(-rotate * 2*PI/12);
          y = ((width/10+width/5/2+width)/2 - (ox - (width/10+width/5/2+width)/2)/3)*sin(-rotate * 2*PI/12) + oy*cos(-rotate * 2*PI/12);
        }
        if (i == 3) {
          rotate = 12 - rotate;
          x = ((width/10+width/5/2+width)/2 - (ox - (width/10+width/5/2+width)/2))*cos(-rotate * 2*PI/12) - oy*sin(-rotate * 2*PI/12);
          y = ((width/10+width/5/2+width)/2 - (ox - (width/10+width/5/2+width)/2))*sin(-rotate * 2*PI/12) + oy*cos(-rotate * 2*PI/12);
        }
      }

      if (width - 15 - 20 > mouseX || mouseX > width - 15 + 20 || 120 - 15 > mouseY || mouseY > 160 + 15) {
        if (cTable) {
          new RectEquipment(x, y, size * 5.33, size * 2.67, color(255, 255, 255), rotate).display();
          if (mousePressed) addTables(x, y, rotate);
        }
        if (cStand) {
          new RectEquipment(x, y, size * 12, size * 1.33, color(0, 0, 0), rotate).display();
          if (mousePressed) addStands(x, y, rotate);
        }
        if (cTruss) {
          new RectEquipment(x, y, size * 12, size * 1.33, color(100, 100, 100), rotate).display();
          if (mousePressed) addTrusses(x, y, rotate);
        }
        if (cLed) {
          new CircleEquipment(x, y, size, color(255, 165, 0), rotate).display();
          if (mousePressed) addLeds(x, y, rotate);
        }
        if (cMega64) {
          new CircleEquipment(x, y, size, color(255, 69, 0), rotate).display();
          if (mousePressed) addMega64s(x, y, rotate);
        }
        if (cMoving) {
          new CircleEquipment(x, y, size, color(0, 191, 255), rotate).display();
          if (mousePressed) addMovings(x, y, rotate);
        }
        if (cPar12) {
          new CircleEquipment(x, y, size, color(50, 205, 50), rotate).display();
          if (mousePressed) addPar12s(x, y, rotate);
        }
        if (cStrobe) {
          new RectEquipment(x, y, size * 2.67, size * 1.33, color(135, 206, 235), rotate).display();
          if (mousePressed) addStrobes(x, y, rotate);
        }
        if (cDekker) {
          new PolygonEquipment(x, y,
            new float[]{-size, -size, size, size, size * 0.5, -size * 0.5},
            new float[]{-size * 0.5, size * 0.5, size * 0.5, -size * 0.5, -size, -size},
            color(255, 105, 180), rotate).display();
          if (mousePressed) addDekkers(x, y, rotate);
        }
        if (cOld) {
          new RectEquipment(x, y, size * 2.67, size * 0.67, color(240, 255, 255), rotate).display();
          if (mousePressed) addOldColorbars(x, y, rotate);
        }
        if (cNew) {
          new RectEquipment(x, y, size * 2.67, size * 0.67, color(255, 165, 0), rotate).display();
          if (mousePressed) addNewColorbars(x, y, rotate);
        }
        if (cPhantom) {
          new RectEquipment(x, y, size * 4, size * 2, color(255, 20, 147), rotate).display();
          if (mousePressed) addPhantoms(x, y, rotate);
        }
        if (cSceneSetter) {
          new RectEquipment(x, y, size * 4, size * 2, color(0, 0, 255), rotate).display();
          if (mousePressed) addSceneSetters(x, y, rotate);
        }
        if (cMini) {
          new RectEquipment(x, y, size * 4, size * 2, color(255, 69, 0), rotate).display();
          if (mousePressed) addMiniDesks(x, y, rotate);
        }
        if (cEPar38) {
          new CircleEquipment(x, y, size, color(0, 255, 255), rotate).display();
          if (mousePressed) addEPar38s(x, y, rotate);
        }
        if (cLED38B) {
          new CircleEquipment(x, y, size, color(255, 255, 0), rotate).display();
          if (mousePressed) addLed38Bs(x, y, rotate);
        }
        if (cFlatPar) {
          new CircleEquipment(x, y, size, color(65, 105, 225), rotate).display();
          if (mousePressed) addFlatPars(x, y, rotate);
        }
        if (cBk75) {
          new CircleEquipment(x, y, size, color(255, 192, 203), rotate).display();
          if (mousePressed) addBk75s(x, y, rotate);
        }
        if (cPar20) {
          new RectEquipment(x, y, size*2, size*2, color(255, 165, 0), rotate).display();
          if (mousePressed) addPar20s(x, y, rotate);
        }
        if (cPar30) {
          new RectEquipment(x, y, size*2, size*2, color(255, 69, 0), rotate).display();
          if (mousePressed) addPar30s(x, y, rotate);
        }
        if (cPar46) {
          new RectEquipment(x, y, size*2, size*2, color(0, 191, 255), rotate).display();
          if (mousePressed) addPar46s(x, y, rotate);
        }
        if (cBold) {
          new RectEquipment(x, y, size * 4, size * 2, color(138, 43, 226), rotate).display();
          if (mousePressed) addBolds(x, y, rotate);
        }
        if (cDimmerPack) {
          new RectEquipment(x, y, size * 2, size * 2.5, color(215, 215, 215), rotate).display();
          if (mousePressed) addDimmerPacks(x, y, rotate);
        }
      }
      if (orotate != rotate)rotate = orotate;
    }
  }
  SizeButton();
  if (mousePressed)rotate = 0;
}

void AddLines() {
  if (width/10 + width/5/2 < mouseX && mouseX < width && 50+50 < mouseY && mouseY < 550 - 50) {
    if (cSingleLine) {
      switch(linePhase) {
      case 0:
        x1 = ox;
        y1 = oy;
        ellipse(ox, oy, 3, 3);
        if (click) {
          linePhase = 1;
          keepSingleLine = true;
        }
        break;
      default:
        x2 = ox;
        y2 = oy;
        new JustLine(x1, y1, x2, y2, color(0, 0, 0)).display();
        if (click) {
          linePhase = 0;
          addJustLines(x1, y1, x2, y2, color(0, 0, 0));
          keepSingleLine = true;
        }
        break;
      }
    }

    if (cLshaped) {
      switch(linePhase) {
      case 0:
        x1 = ox;
        y1 = oy;
        ellipse(ox, oy, 3, 3);
        if (click) {
          linePhase = 1;
          keepLshaped = true;
        }
        break;
      case 1:
        x2 = ox;
        y2 = oy;
        m1x = x2;
        m1y = y1;
        new LLine(x1, y1, x2, y2, m1x, m1y, color(0, 0, 0)).display();
        if (click) linePhase = 2;
        break;
      default:
        if (y1 < y2) {
          float tmp;
          tmp = x1;
          x1 = x2;
          x2 = tmp;
          tmp = y1;
          y1 = y2;
          y2 = tmp;
        }
        if (oy <= ((y1 - y2)/(x1 - x2)) * (ox - x1) + y1) {
          m1x = x1;
          m1y = y2;
        } else {
          m1x = x2;
          m1y = y1;
        }
        new LLine(x1, y1, x2, y2, m1x, m1y, color(0, 0, 0)).display();
        if (click) {
          linePhase = 0;
          addLLines(x1, y1, x2, y2, m1x, m1y, color(0, 0, 0));
          keepLshaped = true;
        }
        break;
      }
    }

    if (cHorizontal) {
      switch(linePhase) {
      case 0:
        x1 = ox;
        y1 = oy;
        ellipse(ox, oy, 3, 3);
        if (click) {
          linePhase = 1;
          keepHorizontal = true;
        }
        break;
      case 1:
        x2 = ox;
        y2 = oy;
        m1x = x1;
        m1y = (y1 + y2)/2;
        m2x = x2;
        m2y = (y1 + y2)/2;
        new BracketLine(x1, y1, x2, y2, m1x, m1y, m2x, m2y, color(0, 0, 0)).display();
        if (click) linePhase = 2;
        break;
      default:
        m1y = oy;
        m2y = oy;
        new BracketLine(x1, y1, x2, y2, m1x, m1y, m2x, m2y, color(0, 0, 0)).display();
        if (click) {
          linePhase = 0;
          addBracketLines(x1, y1, x2, y2, m1x, m1y, m2x, m2y, color(0, 0, 0));
          keepHorizontal = true;
        }
        break;
      }
    }

    if (cVertical) {
      switch(linePhase) {
      case 0:
        x1 = ox;
        y1 = oy;
        ellipse(ox, oy, 3, 3);
        if (click) {
          linePhase = 1;
          keepVertical = true;
        }
        break;
      case 1:
        x2 = ox;
        y2 = oy;
        m1x = (x1 + x2)/2;
        m1y = y1;
        m2x = (x1 + x2)/2;
        m2y = y2;
        new BracketLine(x1, y1, x2, y2, m1x, m1y, m2x, m2y, color(0, 0, 0)).display();
        if (click) linePhase = 2;
        break;
      default:
        m1x = ox;
        m2x = ox;
        new BracketLine(x1, y1, x2, y2, m1x, m1y, m2x, m2y, color(0, 0, 0)).display();
        if (click) {
          linePhase = 0;
          addBracketLines(x1, y1, x2, y2, m1x, m1y, m2x, m2y, color(0, 0, 0));
          keepVertical = true;
        }
        break;
      }
    }
  } else if (mousePressed) {
    keepSingleLine = cSingleLine = false;
    keepLshaped = cLshaped = false;
    keepHorizontal = cHorizontal = false;
    keepVertical = cVertical = false;
    linePhase = 0;
  }
}
