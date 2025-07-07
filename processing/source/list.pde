boolean table = false, stand = false, truss = false;
boolean par = false, deco = false, bar = false, desk = false, denkei = false, other = false;
boolean lineType = false, connect = false;

boolean cTable = false;
boolean cStand = false;
boolean cTruss = false;
boolean cLed = false, cMega64 = false, cMoving = false, cPar12 = false;
boolean cStrobe = false, cDekker = false;
boolean cOld = false, cNew = false;
boolean cPhantom = false, cSceneSetter = false, cMini = false;
boolean cEPar38 = false, cLED38B = false, cFlatPar = false, cBk75 = false, cPar20 = false, cPar30 = false, cPar46 = false;
boolean cBold = false, cDimmerPack = false;
boolean cSingleLine = false, cLshaped = false, cHorizontal = false, cVertical = false;
boolean keepSingleLine = false, keepLshaped = false, keepHorizontal = false, keepVertical = false;
boolean c1m = false, c2m = false, c3m = false, c5m = false, c10m = false, c15m = false, cpower = false;

void lists() {
  tableList();
  standList();
  trussList();

  parList();
  decorationList();
  colorBarList();
  deskList();
  denkeiiList();
  otherList();

  lineTypeList();
  connectList();
}

void parList() {
  if (mousePressed && !par && objecting && width/10-width/12<=mouseX && mouseX<=width/10+width/12 && height/7-50-height/20<=mouseY && mouseY<=height/7-50+height/20) {
    par = true;
    deco = false;
    bar = false;
    desk = false;
    denkei = false;
    other = false;
  }
  if (par) {
    stroke(0);
    fill(200);
    rect(width/2+width/10, 50, 4*width/5, 100);
    fill(0);
    textSize(20);
    text("LED", width/10+width/5, 25);
    text("MEGA64", width/10+2*width/5, 25);
    text("Moving", width/10+3*width/5, 25);
    text("Par12", width/10+4*width/5, 25);
    leds.get(0).display();
    mega64s.get(0).display();
    movings.get(0).display();
    par12s.get(0).display();
  }

  if (par && width/10+width/5-25<=mouseX && mouseX<=width/10+width/5+25 && 60-20<=mouseY && mouseY<=60+20) {
    if (mousePressed) {
      cLed = true;
    } else if (!cLed) {
      fill(0, 0, 0, 20);
      rect(width/10+width/5, 50, 70, 80);
    }
  } else if (mousePressed) {
    cLed = false;
  }
  if (cLed) {
    fill(0, 0, 0, 20);
    rect(width/10+width/5, 50, 70, 80);
  }

  if (par && width/10+2*width/5-25<=mouseX && mouseX<=width/10+2*width/5+25 && 60-20<=mouseY && mouseY<=60+20) {
    if (mousePressed) {
      cMega64 = true;
    } else if (!cMega64) {
      fill(0, 0, 0, 20);
      rect(width/10+2*width/5, 50, 70, 80);
    }
  } else if (mousePressed) {
    cMega64 = false;
  }
  if (cMega64) {
    fill(0, 0, 0, 20);
    rect(width/10+2*width/5, 50, 70, 80);
  }

  if (par && width/10+3*width/5-25<=mouseX && mouseX<=width/10+3*width/5+25 && 60-20<=mouseY && mouseY<=60+20) {
    if (mousePressed) {
      cMoving = true;
    } else if (!cMoving) {
      fill(0, 0, 0, 20);
      rect(width/10+3*width/5, 50, 70, 80);
    }
  } else if (mousePressed) {
    cMoving = false;
  }
  if (cMoving) {
    fill(0, 0, 0, 20);
    rect(width/10+3*width/5, 50, 70, 80);
  }

  if (par && width/10+4*width/5-25<=mouseX && mouseX<=width/10+4*width/5+25 && 60-20<=mouseY && mouseY<=60+20) {
    if (mousePressed) {
      cPar12 = true;
    } else if (!cPar12) {
      fill(0, 0, 0, 20);
      rect(width/10+4*width/5, 50, 70, 80);
    }
  } else if (mousePressed) {
    cPar12 = false;
  }
  if (cPar12) {
    fill(0, 0, 0, 20);
    rect(width/10+4*width/5, 50, 70, 80);
  }
}

void decorationList() {
  if (mousePressed && !deco && objecting && width/10-width/12<=mouseX && mouseX<=width/10+width/12 && 2*height/7-50-height/20<=mouseY && mouseY<=2*height/7-50+height/20) {
    par = false;
    deco = true;
    bar = false;
    desk = false;
    denkei = false;
    other = false;
  }
  if (deco) {
    stroke(0);
    fill(200);
    rect(width/2+width/10, 50, 4*width/5, 100);
    fill(0);
    textSize(20);
    text("Strobe", width/10+width/3, 25);
    text("Dekker", width/10+2*width/3, 25);
    strobes.get(0).display();
    dekkers.get(0).display();
  }

  if (deco && width/10+width/3-25<=mouseX && mouseX<=width/10+width/3+25 && 60-20<=mouseY && mouseY<=60+20) {
    if (mousePressed) {
      cStrobe = true;
    } else if (!cStrobe) {
      fill(0, 0, 0, 20);
      rect(width/10+width/3, 50, 70, 80);
    }
  } else if (mousePressed) {
    cStrobe = false;
  }
  if (cStrobe) {
    fill(0, 0, 0, 20);
    rect(width/10+width/3, 50, 70, 80);
  }

  if (deco && width/10+2*width/3-25<=mouseX && mouseX<=width/10+2*width/3+25 && 60-20<=mouseY && mouseY<=60+20) {
    if (mousePressed) {
      cDekker = true;
    } else if (!cDekker) {
      fill(0, 0, 0, 20);
      rect(width/10+2*width/3, 50, 70, 80);
    }
  } else if (mousePressed) {
    cDekker = false;
  }
  if (cDekker) {
    fill(0, 0, 0, 20);
    rect(width/10+2*width/3, 50, 70, 80);
  }
}

void colorBarList() {
  if (mousePressed && !bar && objecting && width/10-width/12<=mouseX && mouseX<=width/10+width/12 && 3*height/7-50-height/20<=mouseY && mouseY<=3*height/7-50+height/20) {
    par = false;
    deco = false;
    bar = true;
    desk = false;
    denkei = false;
    other = false;
  }
  if (bar) {
    stroke(0);
    fill(200);
    rect(width/2+width/10, 50, 4*width/5, 100);
    fill(0);
    textSize(20);
    text("Old", width/10+width/3, 25);
    text("New", width/10+2*width/3, 25);
    oldColorbars.get(0).display();
    newColorbars.get(0).display();
  }

  if (bar && width/10+width/3-25<=mouseX && mouseX<=width/10+width/3+25 && 60-20<=mouseY && mouseY<=60+20) {
    if (mousePressed) {
      cOld = true;
    } else if (!cOld) {
      fill(0, 0, 0, 20);
      rect(width/10+width/3, 50, 70, 80);
    }
  } else if (mousePressed) {
    cOld = false;
  }
  if (cOld) {
    fill(0, 0, 0, 20);
    rect(width/10+width/3, 50, 70, 80);
  }

  if (bar && width/10+2*width/3-25<=mouseX && mouseX<=width/10+2*width/3+25 && 60-20<=mouseY && mouseY<=60+20) {
    if (mousePressed) {
      cNew = true;
    } else if (!cNew) {
      fill(0, 0, 0, 20);
      rect(width/10+2*width/3, 50, 70, 80);
    }
  } else if (mousePressed) {
    cNew = false;
  }
  if (cNew) {
    fill(0, 0, 0, 20);
    rect(width/10+2*width/3, 50, 70, 80);
  }
}

void deskList() {
  if (mousePressed && !desk && objecting && width/10-width/12<=mouseX && mouseX<=width/10+width/12 && 4*height/7-50-height/20<=mouseY && mouseY<=4*height/7-50+height/20) {
    par = false;
    deco = false;
    bar = false;
    desk = true;
    denkei = false;
    other = false;
  }
  if (desk) {
    stroke(0);
    fill(200);
    rect(width/2+width/10, 50, 4*width/5, 100);
    fill(0);
    textSize(20);
    text("Phantom", width/10+width/4, 25);
    text("SceneSetter", width/10+2*width/4, 25);
    text("Mini", width/10+3*width/4, 25);
    phantoms.get(0).display();
    sceneSetters.get(0).display();
    miniDesks.get(0).display();
  }

  if (desk && width/10+width/4-25<=mouseX && mouseX<=width/10+width/4+25 && 60-20<=mouseY && mouseY<=60+20) {
    if (mousePressed) {
      cPhantom = true;
    } else if (!cPhantom) {
      fill(0, 0, 0, 20);
      rect(width/10+width/4, 50, 90, 80);
    }
  } else if (mousePressed) {
    cPhantom = false;
  }
  if (cPhantom) {
    fill(0, 0, 0, 20);
    rect(width/10+width/4, 50, 90, 80);
  }

  if (desk && width/10+2*width/4-25<=mouseX && mouseX<=width/10+2*width/4+25 && 60-20<=mouseY && mouseY<=60+20) {
    if (mousePressed) {
      cSceneSetter = true;
    } else if (!cSceneSetter) {
      fill(0, 0, 0, 20);
      rect(width/10+2*width/4, 50, 120, 80);
    }
  } else if (mousePressed) {
    cSceneSetter = false;
  }
  if (cSceneSetter) {
    fill(0, 0, 0, 20);
    rect(width/10+2*width/4, 50, 120, 80);
  }

  if (desk && width/10+3*width/4-25<=mouseX && mouseX<=width/10+3*width/4+25 && 60-20<=mouseY && mouseY<=60+20) {
    if (mousePressed) {
      cMini = true;
    } else if (!cMini) {
      fill(0, 0, 0, 20);
      rect(width/10+3*width/4, 50, 70, 80);
    }
  } else if (mousePressed) {
    cMini = false;
  }
  if (cMini) {
    fill(0, 0, 0, 20);
    rect(width/10+3*width/4, 50, 70, 80);
  }
}

void denkeiiList() {
  if (mousePressed && !denkei && objecting && width/10-width/12<=mouseX && mouseX<=width/10+width/12 && 5*height/7-50-height/20<=mouseY && mouseY<=5*height/7-50+height/20) {
    par = false;
    deco = false;
    bar = false;
    desk = false;
    denkei = true;
    other = false;
  }
  if (denkei) {
    stroke(0);
    fill(200);
    rect(width/2+width/10, 50, 4*width/5, 100);
    fill(0);
    textSize(20);
    text("EPar38", width/10+3*width/18, 25);
    text("LED38B", width/10+5*width/18, 25);
    text("FlatPar", width/10+7*width/18, 25);
    text("Bk75", width/10+9*width/18, 25);
    text("Par20", width/10+11*width/18, 25);
    text("Par30", width/10+13*width/18, 25);
    text("Par46", width/10+15*width/18, 25);
    ePar38s.get(0).display();
    led38Bs.get(0).display();
    flatPars.get(0).display();
    bk75s.get(0).display();
    par20s.get(0).display();
    par30s.get(0).display();
    par46s.get(0).display();
  }

  if (denkei && width/10+3*width/18-25<=mouseX && mouseX<=width/10+3*width/18+25 && 60-20<=mouseY && mouseY<=60+20) {
    if (mousePressed) {
      cEPar38 = true;
    } else if (!cEPar38) {
      fill(0, 0, 0, 20);
      rect(width/10+3*width/18, 50, 70, 80);
    }
  } else if (mousePressed) {
    cEPar38 = false;
  }
  if (cEPar38) {
    fill(0, 0, 0, 20);
    rect(width/10+3*width/18, 50, 70, 80);
  }

  if (denkei && width/10+5*width/18-25<=mouseX && mouseX<=width/10+5*width/18+25 && 60-20<=mouseY && mouseY<=60+20) {
    if (mousePressed) {
      cLED38B = true;
    } else if (!cLED38B) {
      fill(0, 0, 0, 20);
      rect(width/10+5*width/18, 50, 70, 80);
    }
  } else if (mousePressed) {
    cLED38B = false;
  }
  if (cLED38B) {
    fill(0, 0, 0, 20);
    rect(width/10+5*width/18, 50, 70, 80);
  }

  if (denkei && width/10+7*width/18-25<=mouseX && mouseX<=width/10+7*width/18+25 && 60-20<=mouseY && mouseY<=60+20) {
    if (mousePressed) {
      cFlatPar = true;
    } else if (!cFlatPar) {
      fill(0, 0, 0, 20);
      rect(width/10+7*width/18, 50, 70, 80);
    }
  } else if (mousePressed) {
    cFlatPar = false;
  }
  if (cFlatPar) {
    fill(0, 0, 0, 20);
    rect(width/10+7*width/18, 50, 70, 80);
  }

  if (denkei && width/10+9*width/18-25<=mouseX && mouseX<=width/10+9*width/18+25 && 60-20<=mouseY && mouseY<=60+20) {
    if (mousePressed) {
      cBk75 = true;
    } else if (!cBk75) {
      fill(0, 0, 0, 20);
      rect(width/10+9*width/18, 50, 70, 80);
    }
  } else if (mousePressed) {
    cBk75 = false;
  }
  if (cBk75) {
    fill(0, 0, 0, 20);
    rect(width/10+9*width/18, 50, 70, 80);
  }

  if (denkei && width/10+11*width/18-25<=mouseX && mouseX<=width/10+11*width/18+25 && 60-20<=mouseY && mouseY<=60+20) {
    if (mousePressed) {
      cPar20 = true;
    } else if (!cPar20) {
      fill(0, 0, 0, 20);
      rect(width/10+11*width/18, 50, 70, 80);
    }
  } else if (mousePressed) {
    cPar20 = false;
  }
  if (cPar20) {
    fill(0, 0, 0, 20);
    rect(width/10+11*width/18, 50, 70, 80);
  }

  if (denkei && width/10+13*width/18-25<=mouseX && mouseX<=width/10+13*width/18+25 && 60-20<=mouseY && mouseY<=60+20) {
    if (mousePressed) {
      cPar30 = true;
    } else if (!cPar30) {
      fill(0, 0, 0, 20);
      rect(width/10+13*width/18, 50, 70, 80);
    }
  } else if (mousePressed) {
    cPar30 = false;
  }
  if (cPar30) {
    fill(0, 0, 0, 20);
    rect(width/10+13*width/18, 50, 70, 80);
  }

  if (denkei && width/10+15*width/18-25<=mouseX && mouseX<=width/10+15*width/18+25 && 60-20<=mouseY && mouseY<=60+20) {
    if (mousePressed) {
      cPar46 = true;
    } else if (!cPar46) {
      fill(0, 0, 0, 20);
      rect(width/10+15*width/18, 50, 70, 80);
    }
  } else if (mousePressed) {
    cPar46 = false;
  }
  if (cPar46) {
    fill(0, 0, 0, 20);
    rect(width/10+15*width/18, 50, 70, 80);
  }
}


void otherList() {
  if (mousePressed && !bar && objecting && width/10-width/12<=mouseX && mouseX<=width/10+width/12 && 6*height/7-50-height/20<=mouseY && mouseY<=6*height/7-50+height/20) {
    par = false;
    deco = false;
    bar = false;
    desk = false;
    denkei = false;
    other = true;
  }
  if (other) {
    stroke(0);
    fill(200);
    rect(width/2+width/10, 50, 4*width/5, 100);
    fill(0);
    textSize(20);
    text("Bold", width/10+width/3, 25);
    text("DimmerPack", width/10+2*width/3, 25);
    bolds.get(0).display();
    dimmerPacks.get(0).display();
  }

  if (other && width/10+width/3-25<=mouseX && mouseX<=width/10+width/3+25 && 60-20<=mouseY && mouseY<=60+20) {
    if (mousePressed) {
      cBold = true;
    } else if (!cBold) {
      fill(0, 0, 0, 20);
      rect(width/10+width/3, 50, 70, 80);
    }
  } else if (mousePressed) {
    cBold = false;
  }
  if (cBold) {
    fill(0, 0, 0, 20);
    rect(width/10+width/3, 50, 70, 80);
  }

  if (other && width/10+2*width/3-25<=mouseX && mouseX<=width/10+2*width/3+25 && 60-20<=mouseY && mouseY<=60+20) {
    if (mousePressed) {
      cDimmerPack = true;
    } else if (!cDimmerPack) {
      fill(0, 0, 0, 20);
      rect(width/10+2*width/3, 50, 120, 80);
    }
  } else if (mousePressed) {
    cDimmerPack = false;
  }
  if (cDimmerPack) {
    fill(0, 0, 0, 20);
    rect(width/10+2*width/3, 50, 120, 80);
  }
}


void tableList() {
  if (mousePressed && !table && standing && width/10-width/12<=mouseX && mouseX<=width/10+width/12 && height/4-50-height/20<=mouseY && mouseY<=height/4-50+height/20) {
    table = true;
    stand = false;
    truss = false;
  }
  if (table) {
    stroke(0);
    fill(200);
    rect(width/2+width/10, 50, 4*width/5, 100);
    fill(0);
    textSize(20);
    text("Table", width/10+width/2, 25);

    tables.get(0).display();
  }

  if (table && width/2+width/10-40<=mouseX && mouseX<=width/2+width/10+40 && 60-20<=mouseY && mouseY<=60+20) {
    if (mousePressed) {
      cTable = true;
    } else if (!cTable) {
      fill(0, 0, 0, 20);
      rect(width/2+width/10, 50, 90, 80);
    }
  } else if (mousePressed) {
    cTable = false;
  }
  if (cTable) {
    fill(0, 0, 0, 20);
    rect(width/2+width/10, 50, 90, 80);
  }
}


void standList() {
  if (mousePressed && !stand && standing && width/10-width/12<=mouseX && mouseX<=width/10+width/12 && 2*height/4-50-height/20<=mouseY && mouseY<=2*height/4-50+height/20) {
    table = false;
    stand = true;
    truss = false;
  }
  if (stand) {
    stroke(0);
    fill(200);
    rect(width/2+width/10, 50, 4*width/5, 100);
    fill(0);
    textSize(20);
    text("Stand", width/10+width/2, 25);

    stands.get(0).display();
  }

  if (stand && width/2+width/10-90<=mouseX && mouseX<=width/2+width/10+90 && 60-20<=mouseY && mouseY<=60+20) {
    if (mousePressed) {
      cStand = true;
    } else if (!cStand) {
      fill(0, 0, 0, 20);
      rect(width/2+width/10, 50, 200, 80);
    }
  } else if (mousePressed) {
    cStand = false;
  }
  if (cStand) {
    fill(0, 0, 0, 20);
    rect(width/2+width/10, 50, 200, 80);
  }
}


void trussList() {
  if (mousePressed && !truss && standing && width/10-width/12<=mouseX && mouseX<=width/10+width/12 && 3*height/4-50-height/20<=mouseY && mouseY<=3*height/4-50+height/20) {
    table = false;
    stand = false;
    truss = true;
  }
  if (truss) {
    stroke(0);
    fill(200);
    rect(width/2+width/10, 50, 4*width/5, 100);
    fill(0);
    textSize(20);
    text("Truss", width/10+width/2, 25);

    trusses.get(0).display();
  }

  if (truss && width/2+width/10-90<=mouseX && mouseX<=width/2+width/10+90 && 60-20<=mouseY && mouseY<=60+20) {
    if (mousePressed) {
      cTruss = true;
    } else if (!cTruss) {
      fill(0, 0, 0, 20);
      rect(width/2+width/10, 50, 200, 80);
    }
  } else if (mousePressed) {
    cTruss = false;
  }
  if (cTruss) {
    fill(0, 0, 0, 20);
    rect(width/2+width/10, 50, 200, 80);
  }
}


void connectList() {
  if (mousePressed && !connect && dmxing && width/10-width/12<=mouseX && mouseX<=width/10+width/12 && height/3-50-height/20<=mouseY && mouseY<=height/3-50+height/20) {
    lineType = false;
    connect = true;
  }
  if (connect) {
    stroke(0);
    fill(200);
    rect(width/2+width/10, 50, 4*width/5, 100);
    fill(0);
    textSize(20);

    text("SingleLine", width/10+width/5, 25);
    text("L-shaped", width/10+2*width/5, 25);
    text("Horizontal '['", width/10+3*width/5, 25);
    text("Vertical '['", width/10+4*width/5, 25);

    justLines.get(0).display();
    lLines.get(0).display();
    bracketLines.get(0).display();
    bracketLines.get(1).display();
  }


  if (connect && width/10+width/5-75<=mouseX && mouseX<=width/10+width/5+75 && 60-20<=mouseY && mouseY<=60+20) {
    if (mousePressed) {
      cSingleLine = true;
    } else if (!cSingleLine) {
      fill(0, 0, 0, 20);
      rect(width/10+width/5, 50, 150, 80);
    }
  } else if (mousePressed) {
    cSingleLine = false;
  }
  if (cSingleLine) {
    fill(0, 0, 0, 20);
    rect(width/10+width/5, 50, 150, 80);
  }

  if (connect && width/10+2*width/5-75<=mouseX && mouseX<=width/10+2*width/5+75 && 60-20<=mouseY && mouseY<=60+20) {
    if (mousePressed) {
      cLshaped = true;
    } else if (!cLshaped) {
      fill(0, 0, 0, 20);
      rect(width/10+2*width/5, 50, 150, 80);
    }
  } else if (mousePressed) {
    cLshaped = false;
  }
  if (cLshaped) {
    fill(0, 0, 0, 20);
    rect(width/10+2*width/5, 50, 150, 80);
  }

  if (connect && width/10+3*width/5-75<=mouseX && mouseX<=width/10+3*width/5+75 && 60-20<=mouseY && mouseY<=60+20) {
    if (mousePressed) {
      cHorizontal = true;
    } else if (!cHorizontal) {
      fill(0, 0, 0, 20);
      rect(width/10+3*width/5, 50, 150, 80);
    }
  } else if (mousePressed) {
    cHorizontal = false;
  }
  if (cHorizontal) {
    fill(0, 0, 0, 20);
    rect(width/10+3*width/5, 50, 150, 80);
  }

  if (connect && width/10+4*width/5-75<=mouseX && mouseX<=width/10+4*width/5+75 && 60-20<=mouseY && mouseY<=60+20) {
    if (mousePressed) {
      cVertical = true;
    } else if (!cVertical) {
      fill(0, 0, 0, 20);
      rect(width/10+4*width/5, 50, 150, 80);
    }
  } else if (mousePressed) {
    cVertical = false;
  }
  if (cVertical) {
    fill(0, 0, 0, 20);
    rect(width/10+4*width/5, 50, 150, 80);
  }

  if (keepSingleLine)cSingleLine = true;
  if (keepLshaped) cLshaped = true;
  if (keepHorizontal) cHorizontal = true;
  if (keepVertical) cVertical = true;
}



void lineTypeList() {
  if (mousePressed && !lineType && dmxing && width/10-width/12<=mouseX && mouseX<=width/10+width/12 && 2*height/3-50-height/20<=mouseY && mouseY<=2*height/3-50+height/20) {
    lineType = true;
    connect = false;
  }
  if (lineType) {
    stroke(0);
    fill(200);
    rect(width/2+width/10, 50, 4*width/5, 100);
    fill(0);
    textSize(20);
    
    text("1m", width/10+3*width/18, 25);
    text("2m", width/10+5*width/18, 25);
    text("3m", width/10+7*width/18, 25);
    text("5m", width/10+9*width/18, 25);
    text("10m", width/10+11*width/18, 25);
    text("15m", width/10+13*width/18, 25);
    text("power", width/10+15*width/18, 25);
    
    strokeWeight(3);
    stroke(255, 0, 0);
    line(width/10+3*width/18, 45, width/10+3*width/18, 70);
    stroke(200, 0, 255);
    line(width/10+5*width/18, 45, width/10+5*width/18, 70);
    stroke(0, 255, 255);
    line(width/10+7*width/18, 45, width/10+7*width/18, 70);
    stroke(255, 130, 0);
    line(width/10+9*width/18, 45, width/10+9*width/18, 70);
    stroke(0, 255, 0);
    line(width/10+11*width/18, 45, width/10+11*width/18, 70);
    stroke(0, 0, 255);
    line(width/10+13*width/18, 45, width/10+13*width/18, 70);
    stroke(0);
    line(width/10+15*width/18, 45, width/10+15*width/18, 70);
    strokeWeight(1);
  }

  if (lineType && width/10+3*width/18-40<=mouseX && mouseX<=width/10+3*width/18+40 && 60-20<=mouseY && mouseY<=60+20) {
    if (mousePressed) {
      c1m = true;
    } else if (!c1m) {
      fill(0, 0, 0, 20);
      rect(width/10+3*width/18, 50, 75, 80);
    }
  } else if (mousePressed && (mouseY >= 500 || 100 >= mouseY || mouseX <= width/10+width/10)) {
    c1m = false;
  }
  if (c1m) {
    fill(0, 0, 0, 20);
    rect(width/10+3*width/18, 50, 75, 80);
  }

  if (lineType && width/10+5*width/18-40<=mouseX && mouseX<=width/10+5*width/18+40 && 60-20<=mouseY && mouseY<=60+20) {
    if (mousePressed) {
      c2m = true;
    } else if (!c2m) {
      fill(0, 0, 0, 20);
      rect(width/10+5*width/18, 50, 75, 80);
    }
  } else if (mousePressed && (mouseY >= 500 || 100 >= mouseY || mouseX <= width/10+width/10)) {
    c2m = false;
  }
  if (c2m) {
    fill(0, 0, 0, 20);
    rect(width/10+5*width/18, 50, 75, 80);
  }

  if (lineType && width/10+7*width/18-40<=mouseX && mouseX<=width/10+7*width/18+40 && 60-20<=mouseY && mouseY<=60+20) {
    if (mousePressed) {
      c3m = true;
    } else if (!c3m) {
      fill(0, 0, 0, 20);
      rect(width/10+7*width/18, 50, 75, 80);
    }
  } else if (mousePressed && (mouseY >= 500 || 100 >= mouseY || mouseX <= width/10+width/10)) {
    c3m = false;
  }
  if (c3m) {
    fill(0, 0, 0, 20);
    rect(width/10+7*width/18, 50, 75, 80);
  }

  if (lineType && width/10+9*width/18-40<=mouseX && mouseX<=width/10+9*width/18+40 && 60-20<=mouseY && mouseY<=60+20) {
    if (mousePressed) {
      c5m = true;
    } else if (!c5m) {
      fill(0, 0, 0, 20);
      rect(width/10+9*width/18, 50, 75, 80);
    }
  } else if (mousePressed && (mouseY >= 500 || 100 >= mouseY || mouseX <= width/10+width/10)) {
    c5m = false;
  }
  if (c5m) {
    fill(0, 0, 0, 20);
    rect(width/10+9*width/18, 50, 75, 80);
  }

  if (lineType && width/10+11*width/18-40<=mouseX && mouseX<=width/10+11*width/18+40 && 60-20<=mouseY && mouseY<=60+20) {
    if (mousePressed) {
      c10m = true;
    } else if (!c10m) {
      fill(0, 0, 0, 20);
      rect(width/10+11*width/18, 50, 75, 80);
    }
  } else if (mousePressed && (mouseY >= 500 || 100 >= mouseY || mouseX <= width/10+width/10)) {
    c10m = false;
  }
  if (c10m) {
    fill(0, 0, 0, 20);
    rect(width/10+11*width/18, 50, 75, 80);
  }

  if (lineType && width/10+13*width/18-40<=mouseX && mouseX<=width/10+13*width/18+40 && 60-20<=mouseY && mouseY<=60+20) {
    if (mousePressed) {
      c15m = true;
    } else if (!c15m) {
      fill(0, 0, 0, 20);
      rect(width/10+13*width/18, 50, 75, 80);
    }
  } else if (mousePressed && (mouseY >= 500 || 100 >= mouseY || mouseX <= width/10+width/10)) {
    c15m = false;
  }
  if (c15m) {
    fill(0, 0, 0, 20);
    rect(width/10+13*width/18, 50, 75, 80);
  }

  if (lineType && width/10+15*width/18-40<=mouseX && mouseX<=width/10+15*width/18+40 && 60-20<=mouseY && mouseY<=60+20) {
    if (mousePressed) {
      cpower = true;
    } else if (!cpower) {
      fill(0, 0, 0, 20);
      rect(width/10+15*width/18, 50, 75, 80);
    }
  } else if (mousePressed && (mouseY >= 500 || 100 >= mouseY || mouseX <= width/10+width/10)) {
    cpower = false;
  }
  if (cpower) {
    fill(0, 0, 0, 20);
    rect(width/10+15*width/18, 50, 75, 80);
  }
}
