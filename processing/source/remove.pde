void removes() {
  if (Remove) {
    if (click && !cTable && !cStand && !cTruss && !cLed && !cMega64 && !cMoving && !cPar12 && !cStrobe && !cDekker && !cOld && !cNew && !cPhantom && !cSceneSetter && !cMini && !cEPar38 && !cLED38B && !cFlatPar && !cBk75 && !cPar20 && !cPar30 && !cPar46 && !cBold && !cDimmerPack) {
      removeObject(leds);
      removeObject(mega64s);
      removeObject(movings);
      removeObject(par12s);
      removeObject(strobes);
      removeObject(dekkers);
      removeObject(oldColorbars);
      removeObject(newColorbars);
      removeObject(phantoms);
      removeObject(sceneSetters);
      removeObject(miniDesks);
      removeObject(ePar38s);
      removeObject(led38Bs);
      removeObject(flatPars);
      removeObject(bk75s);
      removeObject(par20s);
      removeObject(par30s);
      removeObject(par46s);
      removeObject(bolds);
      removeObject(dimmerPacks);
      removeObject(tables);
      removeObject(stands);
      removeObject(trusses);
    }
    if (mousePressed && !cSingleLine && !cLshaped && !cHorizontal && !cVertical) {
      removeLine(justLines);
      removeLine(lLines);
      removeLine(bracketLines);
    }
  }
}
