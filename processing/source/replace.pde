Equipment repObj;
boolean repObjced = false;
boolean kp = false;
void replaceObject(ArrayList<Equipment> objects) {

  boolean replaced = false;


  println(keyPressing);

  if (repObjced) {
    rotate = repObj.r;
    if (!kp && keyPressed && (key == 'r' || key == 'R')) {
      if (rotate != 11)rotate++;
      else rotate = 0;
    }

    if (keyPressed)kp = true;
    else kp=false;

    if (width/10 + width/5/2 < mouseX && mouseX < width && 50+50 < mouseY && mouseY < 550 - 50) {

      stroke(255, 0, 0);
      if ((width/10+width/5/2+width)/2 - 10 < mouseX && mouseX < (width/10+width/5/2+width)/2 + 10) {
        ox = (width/10+width/5/2+width)/2;
        line((width/10+width/5/2+width)/2, 50+50, (width/10+width/5/2+width)/2, 550-50);
      } else {
        ox = mouseX;
      }

      oy = mouseY;

      if (objects != leds)drawVerticalLines(leds);
      if (objects != mega64s)drawVerticalLines(mega64s);
      if (objects != movings)drawVerticalLines(movings);
      if (objects != par12s)drawVerticalLines(par12s);
      if (objects != strobes)drawVerticalLines(strobes);
      if (objects != dekkers)drawVerticalLines(dekkers);
      if (objects != oldColorbars)drawVerticalLines(oldColorbars);
      if (objects != newColorbars)drawVerticalLines(newColorbars);
      if (objects != phantoms)drawVerticalLines(phantoms);
      if (objects != sceneSetters)drawVerticalLines(sceneSetters);
      if (objects != miniDesks)drawVerticalLines(miniDesks);
      if (objects != ePar38s)drawVerticalLines(ePar38s);
      if (objects != led38Bs)drawVerticalLines(led38Bs);
      if (objects != flatPars)drawVerticalLines(flatPars);
      if (objects != bk75s)drawVerticalLines(bk75s);
      if (objects != par20s)drawVerticalLines(par20s);
      if (objects != par30s)drawVerticalLines(par30s);
      if (objects != par46s)drawVerticalLines(par46s);
      if (objects != bolds)drawVerticalLines(bolds);
      if (objects != dimmerPacks)drawVerticalLines(dimmerPacks);
      if (objects != tables)drawVerticalLines(tables);
      if (objects != stands)drawVerticalLines(stands);
      if (objects != trusses)drawVerticalLines(trusses);

      smartGuides(stands);
      smartGuides(trusses);

      stroke(0);

      x = ox*cos(-rotate * 2*PI/12) - oy*sin(-rotate * 2*PI/12);
      y = ox*sin(-rotate * 2*PI/12) + oy*cos(-rotate * 2*PI/12);

      repObj.x = x;
      repObj.y = y;
      repObj.r = rotate;
    }
  }
  for (int i = objects.size()-1; i > 0; i--) {
    Equipment obj = objects.get(i);
    if (onObject(obj) && mousePressed && !repObjced) {
      repObj = obj;
      replaced = true;
      repObjced = true;
    }
    if (replaced) break;
  }
}

void replaces() {
  if (Replace) {
    if (!cTable && !cStand && !cTruss && !cLed && !cMega64 && !cMoving && !cPar12 && !cStrobe && !cDekker && !cOld && !cNew && !cPhantom && !cSceneSetter && !cMini && !cEPar38 && !cLED38B && !cFlatPar && !cBk75 && !cPar20 && !cPar30 && !cPar46 && !cBold && !cDimmerPack) {
      replaceObject(leds);
      replaceObject(mega64s);
      replaceObject(movings);
      replaceObject(par12s);
      replaceObject(strobes);
      replaceObject(dekkers);
      replaceObject(oldColorbars);
      replaceObject(newColorbars);
      replaceObject(phantoms);
      replaceObject(sceneSetters);
      replaceObject(miniDesks);
      replaceObject(ePar38s);
      replaceObject(led38Bs);
      replaceObject(flatPars);
      replaceObject(bk75s);
      replaceObject(par20s);
      replaceObject(par30s);
      replaceObject(par46s);
      replaceObject(bolds);
      replaceObject(dimmerPacks);
      replaceObject(tables);
      replaceObject(stands);
      replaceObject(trusses);
    }
  }
}

void mouseReleased() {
  if (repObjced)repObjced = false;
}
