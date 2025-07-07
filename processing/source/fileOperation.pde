void openProject() {
  String filePath = selectFile();  // ファイル選択ダイアログを開く
  if (filePath != null) {
    JSONObject projectData = loadJSONObject(filePath);  // JSONファイルを読み込む
    for (int i = 1; i < projectData.getInt("led"); i++) {
      addLeds(projectData.getFloat("ledX"+i), projectData.getFloat("ledY"+i), projectData.getInt("ledR"+i));
    }
    for (int i = 1; i < projectData.getInt("mega64"); i++) {
      addMega64s(projectData.getFloat("mega64X"+i), projectData.getFloat("mega64Y"+i), projectData.getInt("mega64R"+i));
    }
    for (int i = 1; i < projectData.getInt("moving"); i++) {
      addMovings(projectData.getFloat("movingX"+i), projectData.getFloat("movingY"+i), projectData.getInt("movingR"+i));
    }
    for (int i = 1; i < projectData.getInt("par12"); i++) {
      addPar12s(projectData.getFloat("par12X"+i), projectData.getFloat("par12Y"+i), projectData.getInt("par12R"+i));
    }
    for (int i = 1; i < projectData.getInt("strobe"); i++) {
      addStrobes(projectData.getFloat("strobeX"+i), projectData.getFloat("strobeY"+i), projectData.getInt("strobeR"+i));
    }
    for (int i = 1; i < projectData.getInt("dekker"); i++) {
      addDekkers(projectData.getFloat("dekkerX"+i), projectData.getFloat("dekkerY"+i), projectData.getInt("dekkerR"+i));
    }
    for (int i = 1; i < projectData.getInt("oldColorbar"); i++) {
      addOldColorbars(projectData.getFloat("oldColorbarX"+i), projectData.getFloat("oldColorbarY"+i), projectData.getInt("oldColorbarR"+i));
    }
    for (int i = 1; i < projectData.getInt("newColorbar"); i++) {
      addNewColorbars(projectData.getFloat("newColorbarX"+i), projectData.getFloat("newColorbarY"+i), projectData.getInt("newColorbarR"+i));
    }
    for (int i = 1; i < projectData.getInt("phantom"); i++) {
      addPhantoms(projectData.getFloat("phantomX"+i), projectData.getFloat("phantomY"+i), projectData.getInt("phantomR"+i));
    }
    for (int i = 1; i < projectData.getInt("sceneSetter"); i++) {
      addSceneSetters(projectData.getFloat("sceneSetterX"+i), projectData.getFloat("sceneSetterY"+i), projectData.getInt("sceneSetterR"+i));
    }
    for (int i = 1; i < projectData.getInt("miniDesk"); i++) {
      addMiniDesks(projectData.getFloat("miniDeskX"+i), projectData.getFloat("miniDeskY"+i), projectData.getInt("miniDeskR"+i));
    }
    for (int i = 1; i < projectData.getInt("ePar38"); i++) {
      addEPar38s(projectData.getFloat("ePar38X"+i), projectData.getFloat("ePar38Y"+i), projectData.getInt("ePar38R"+i));
    }
    for (int i = 1; i < projectData.getInt("led38B"); i++) {
      addLed38Bs(projectData.getFloat("led38BX"+i), projectData.getFloat("led38BY"+i), projectData.getInt("led38BR"+i));
    }
    for (int i = 1; i < projectData.getInt("flatPar"); i++) {
      addFlatPars(projectData.getFloat("flatParX"+i), projectData.getFloat("flatParY"+i), projectData.getInt("flatParR"+i));
    }
    for (int i = 1; i < projectData.getInt("bk75"); i++) {
      addBk75s(projectData.getFloat("bk75X"+i), projectData.getFloat("bk75Y"+i), projectData.getInt("bk75R"+i));
    }
    for (int i = 1; i < projectData.getInt("par20"); i++) {
      addPar20s(projectData.getFloat("par20X"+i), projectData.getFloat("par20Y"+i), projectData.getInt("par20R"+i));
    }
    for (int i = 1; i < projectData.getInt("par30"); i++) {
      addPar30s(projectData.getFloat("par30X"+i), projectData.getFloat("par30Y"+i), projectData.getInt("par30R"+i));
    }
    for (int i = 1; i < projectData.getInt("par46"); i++) {
      addPar46s(projectData.getFloat("par46X"+i), projectData.getFloat("par46Y"+i), projectData.getInt("par46R"+i));
    }
    for (int i = 1; i < projectData.getInt("bold"); i++) {
      addBolds(projectData.getFloat("boldX"+i), projectData.getFloat("boldY"+i), projectData.getInt("boldR"+i));
    }
    for (int i = 1; i < projectData.getInt("dimmerPack"); i++) {
      addDimmerPacks(projectData.getFloat("dimmerpackX"+i), projectData.getFloat("dimmerpackY"+i), projectData.getInt("dimmerpackR"+i));
    }
    for (int i = 1; i < projectData.getInt("table"); i++) {
      addTables(projectData.getFloat("tableX"+i), projectData.getFloat("tableY"+i), projectData.getInt("tableR"+i));
    }
    for (int i = 1; i < projectData.getInt("stand"); i++) {
      addStands(projectData.getFloat("standX"+i), projectData.getFloat("standY"+i), projectData.getInt("standR"+i));
    }
    for (int i = 1; i < projectData.getInt("truss"); i++) {
      addTrusses(projectData.getFloat("trussX"+i), projectData.getFloat("trussY"+i), projectData.getInt("trussR"+i));
    }
    for (int i = 1; i < projectData.getInt("justLine"); i++) {
      addJustLines(projectData.getFloat("justLineSX"+i), projectData.getFloat("justLineSY"+i), projectData.getFloat("justLineEX"+i), projectData.getFloat("justLineEY"+i), projectData.getInt("justLineC"+i));
    }
    for (int i = 1; i < projectData.getInt("lLine"); i++) {
      addLLines(projectData.getFloat("lLineSX"+i), projectData.getFloat("lLineSY"+i), projectData.getFloat("lLineEX"+i), projectData.getFloat("lLineEY"+i), projectData.getFloat("lLineMX"+i), projectData.getFloat("lLineMY"+i), projectData.getInt("lLineC"+i));
    }
    for (int i = 2; i < projectData.getInt("bracketLine"); i++) {
      addBracketLines(projectData.getFloat("bracketLineSX"+i), projectData.getFloat("bracketLineSY"+i), projectData.getFloat("bracketLineEX"+i), projectData.getFloat("bracketLineEY"+i), projectData.getFloat("bracketLineM1X"+i), projectData.getFloat("bracketLineM1Y"+i), projectData.getFloat("bracketLineM2X"+i), projectData.getFloat("bracketLineM2Y"+i), projectData.getInt("bracketLineC"+i));
    }
  }
  fileing = false;
  standing = true;
}

String selectFile() {
  JFileChooser fileChooser = new JFileChooser();
  int returnValue = fileChooser.showOpenDialog(null);
  if (returnValue == JFileChooser.APPROVE_OPTION) {
    return fileChooser.getSelectedFile().getPath();  // ファイルのパスを返す
  } else {
    //println("No file selected");
    return null;
  }
}

void saveProject() {
  // JFileChooserを使って保存ダイアログを表示
  JFileChooser fileChooser = new JFileChooser();
  fileChooser.setDialogTitle("保存場所とファイル名を指定してください");

  // デフォルトの保存形式はPNGとする
  fileChooser.setSelectedFile(new File("project.json"));

  // ダイアログを表示して、ユーザーの選択を待つ
  int userSelection = fileChooser.showSaveDialog(null);

  if (userSelection == JFileChooser.APPROVE_OPTION) {
    // ユーザーが保存場所と名前を選んだ場合、そのパスを取得
    File fileToSave = fileChooser.getSelectedFile();

    JSONObject projectData = new JSONObject();

    saveJson(projectData);

    saveJSONObject(projectData, fileToSave.getAbsolutePath());

    //println("プロジェクトが保存されました: " + fileToSave.getAbsolutePath());
  } else {
    //println("保存がキャンセルされました");
  }

  fileing = false;
  standing = true;
}

void saveJson(JSONObject projectData) {    // プロジェクトを指定されたファイル名で保存
  projectData.setInt("led", leds.size());
  for (int i = 1; i < leds.size(); i++) {
    projectData.setFloat("ledX"+i, leds.get(i).x);
    projectData.setFloat("ledY"+i, leds.get(i).y);
    projectData.setInt("ledR"+i, leds.get(i).r);
  }
  projectData.setInt("mega64", mega64s.size());
  for (int i = 1; i < mega64s.size(); i++) {
    projectData.setFloat("mega64X"+i, mega64s.get(i).x);
    projectData.setFloat("mega64Y"+i, mega64s.get(i).y);
    projectData.setInt("mega64R"+i, mega64s.get(i).r);
  }
  projectData.setInt("moving", movings.size());
  for (int i = 1; i < movings.size(); i++) {
    projectData.setFloat("movingX"+i, movings.get(i).x);
    projectData.setFloat("movingY"+i, movings.get(i).y);
    projectData.setInt("movingR"+i, movings.get(i).r);
  }
  projectData.setInt("par12", par12s.size());
  for (int i = 1; i < par12s.size(); i++) {
    projectData.setFloat("par12X"+i, par12s.get(i).x);
    projectData.setFloat("par12Y"+i, par12s.get(i).y);
    projectData.setInt("par12R"+i, par12s.get(i).r);
  }
  projectData.setInt("strobe", strobes.size());
  for (int i = 1; i < strobes.size(); i++) {
    projectData.setFloat("strobeX"+i, strobes.get(i).x);
    projectData.setFloat("strobeY"+i, strobes.get(i).y);
    projectData.setInt("strobeR"+i, strobes.get(i).r);
  }
  projectData.setInt("dekker", dekkers.size());
  for (int i = 1; i < dekkers.size(); i++) {
    projectData.setFloat("dekkerX"+i, dekkers.get(i).x);
    projectData.setFloat("dekkerY"+i, dekkers.get(i).y);
    projectData.setInt("dekkerR"+i, dekkers.get(i).r);
  }
  projectData.setInt("oldColorbar", oldColorbars.size());
  for (int i = 1; i < oldColorbars.size(); i++) {
    projectData.setFloat("oldColorbarX"+i, oldColorbars.get(i).x);
    projectData.setFloat("oldColorbarY"+i, oldColorbars.get(i).y);
    projectData.setInt("oldColorbarR"+i, oldColorbars.get(i).r);
  }
  projectData.setInt("newColorbar", newColorbars.size());
  for (int i = 1; i < newColorbars.size(); i++) {
    projectData.setFloat("newColorbarX"+i, newColorbars.get(i).x);
    projectData.setFloat("newColorbarY"+i, newColorbars.get(i).y);
    projectData.setInt("newColorbarR"+i, newColorbars.get(i).r);
  }
  projectData.setInt("phantom", phantoms.size());
  for (int i = 1; i < phantoms.size(); i++) {
    projectData.setFloat("phantomX"+i, phantoms.get(i).x);
    projectData.setFloat("phantomY"+i, phantoms.get(i).y);
    projectData.setInt("phantomR"+i, phantoms.get(i).r);
  }
  projectData.setInt("sceneSetter", sceneSetters.size());
  for (int i = 1; i < sceneSetters.size(); i++) {
    projectData.setFloat("sceneSetterX"+i, sceneSetters.get(i).x);
    projectData.setFloat("sceneSetterY"+i, sceneSetters.get(i).y);
    projectData.setInt("sceneSetterR"+i, sceneSetters.get(i).r);
  }
  projectData.setInt("miniDesk", miniDesks.size());
  for (int i = 1; i < miniDesks.size(); i++) {
    projectData.setFloat("miniDeskX"+i, miniDesks.get(i).x);
    projectData.setFloat("miniDeskY"+i, miniDesks.get(i).y);
    projectData.setInt("miniDeskR"+i, miniDesks.get(i).r);
  }
  projectData.setInt("ePar38", ePar38s.size());
  for (int i = 1; i < ePar38s.size(); i++) {
    projectData.setFloat("ePar38X"+i, ePar38s.get(i).x);
    projectData.setFloat("ePar38Y"+i, ePar38s.get(i).y);
    projectData.setInt("ePar38R"+i, ePar38s.get(i).r);
  }
  projectData.setInt("led38B", led38Bs.size());
  for (int i = 1; i < led38Bs.size(); i++) {
    projectData.setFloat("led38BX"+i, led38Bs.get(i).x);
    projectData.setFloat("led38BY"+i, led38Bs.get(i).y);
    projectData.setInt("led38BR"+i, led38Bs.get(i).r);
  }
  projectData.setInt("flatPar", flatPars.size());
  for (int i = 1; i < flatPars.size(); i++) {
    projectData.setFloat("flatParX"+i, flatPars.get(i).x);
    projectData.setFloat("flatParY"+i, flatPars.get(i).y);
    projectData.setInt("flatParR"+i, flatPars.get(i).r);
  }
  projectData.setInt("bk75", bk75s.size());
  for (int i = 1; i < bk75s.size(); i++) {
    projectData.setFloat("bk75X"+i, bk75s.get(i).x);
    projectData.setFloat("bk75Y"+i, bk75s.get(i).y);
    projectData.setInt("bk75R"+i, bk75s.get(i).r);
  }
  projectData.setInt("par20", par20s.size());
  for (int i = 1; i < par20s.size(); i++) {
    projectData.setFloat("par20X"+i, par20s.get(i).x);
    projectData.setFloat("par20Y"+i, par20s.get(i).y);
    projectData.setInt("par20R"+i, par20s.get(i).r);
  }
  projectData.setInt("par30", par30s.size());
  for (int i = 1; i < par30s.size(); i++) {
    projectData.setFloat("par30X"+i, par30s.get(i).x);
    projectData.setFloat("par30Y"+i, par30s.get(i).y);
    projectData.setInt("par30R"+i, par30s.get(i).r);
  }
  projectData.setInt("par46", par46s.size());
  for (int i = 1; i < par46s.size(); i++) {
    projectData.setFloat("par46X"+i, par46s.get(i).x);
    projectData.setFloat("par46Y"+i, par46s.get(i).y);
    projectData.setInt("par46R"+i, par46s.get(i).r);
  }
  projectData.setInt("bold", bolds.size());
  for (int i = 1; i < bolds.size(); i++) {
    projectData.setFloat("boldX"+i, bolds.get(i).x);
    projectData.setFloat("boldY"+i, bolds.get(i).y);
    projectData.setInt("boldR"+i, bolds.get(i).r);
  }
  projectData.setInt("dimmerPack", dimmerPacks.size());
  for (int i = 1; i < dimmerPacks.size(); i++) {
    projectData.setFloat("dimmerpackX"+i, dimmerPacks.get(i).x);
    projectData.setFloat("dimmerpackY"+i, dimmerPacks.get(i).y);
    projectData.setInt("dimmerpackR"+i, dimmerPacks.get(i).r);
  }
  projectData.setInt("table", tables.size());
  for (int i = 1; i < tables.size(); i++) {
    projectData.setFloat("tableX"+i, tables.get(i).x);
    projectData.setFloat("tableY"+i, tables.get(i).y);
    projectData.setInt("tableR"+i, tables.get(i).r);
  }
  projectData.setInt("stand", stands.size());
  for (int i = 1; i < stands.size(); i++) {
    projectData.setFloat("standX"+i, stands.get(i).x);
    projectData.setFloat("standY"+i, stands.get(i).y);
    projectData.setInt("standR"+i, stands.get(i).r);
  }
  projectData.setInt("truss", trusses.size());
  for (int i = 1; i < trusses.size(); i++) {
    projectData.setFloat("trussX"+i, trusses.get(i).x);
    projectData.setFloat("trussY"+i, trusses.get(i).y);
    projectData.setInt("trussR"+i, trusses.get(i).r);
  }
  projectData.setInt("justLine", justLines.size());
  for (int i = 1; i < justLines.size(); i++) {
    projectData.setFloat("justLineSX"+i, justLines.get(i).sx);
    projectData.setFloat("justLineSY"+i, justLines.get(i).sy);
    projectData.setFloat("justLineEX"+i, justLines.get(i).ex);
    projectData.setFloat("justLineEY"+i, justLines.get(i).ey);
    projectData.setInt("justLineC"+i, justLines.get(i).c);
  }
  projectData.setInt("lLine", lLines.size());
  for (int i = 1; i < lLines.size(); i++) {
    LLine Llines = (LLine) lLines.get(i);
    projectData.setFloat("lLineSX"+i, Llines.sx);
    projectData.setFloat("lLineSY"+i, Llines.sy);
    projectData.setFloat("lLineEX"+i, Llines.ex);
    projectData.setFloat("lLineEY"+i, Llines.ey);
    projectData.setFloat("lLineMX"+i, Llines.mx);
    projectData.setFloat("lLineMY"+i, Llines.my);
    projectData.setInt("lLineC"+i, Llines.c);
  }
  projectData.setInt("bracketLine", bracketLines.size());
  for (int i = 2; i < bracketLines.size(); i++) {
    BracketLine Bracketlines = (BracketLine) bracketLines.get(i);
    projectData.setFloat("bracketLineSX"+i, Bracketlines.sx);
    projectData.setFloat("bracketLineSY"+i, Bracketlines.sy);
    projectData.setFloat("bracketLineEX"+i, Bracketlines.ex);
    projectData.setFloat("bracketLineEY"+i, Bracketlines.ey);
    projectData.setFloat("bracketLineM1X"+i, Bracketlines.m1x);
    projectData.setFloat("bracketLineM1Y"+i, Bracketlines.m1y);
    projectData.setFloat("bracketLineM2X"+i, Bracketlines.m2x);
    projectData.setFloat("bracketLineM2Y"+i, Bracketlines.m2y);
    projectData.setInt("bracketLineC"+i, Bracketlines.c);
  }
}

void saveLocation() {
  JSONObject projectData = new JSONObject();
  saveJson(projectData);
  saveJSONObject(projectData, "project_data.json");
  SaveImage();
  fill(255);
  rect(width/2, height/2, 600, 150);
  rect(width/2-250/2, height/2+40, 200, 50);
  rect(width/2+250/2, height/2+40, 200, 50);
  fill(0);
  text("LicationSaveComplete. SaveProjectAlso?", width/2, height/2-40);
  text("Yes", width/2-250/2, height/2+40);
  text("No", width/2+250/2, height/2+40);
  if (click) {
    if (width/2-250/2-100 <= mouseX && mouseX <= width/2-250/2+100 && height/2+40-25 <= mouseY && mouseY <= height/2+40+25) {
      saveProject();
      fileing = false;
      standing = true;
      saving = false;
      makeTable = true;
      exit();
    }
    if (width/2+250/2-100 <= mouseX && mouseX <= width/2+250/2+100 && height/2+40-25 <= mouseY && mouseY <= height/2+40+25) {
      fileing = false;
      standing = true;
      saving = false;
      makeTable = true;
      exit();
    }
  }
}

void SaveImage() {
  pushMatrix();
  background(255);
  translate(-width/5-1, -49);
  scale(1.17);
  drawObject();
  save("image.png");
  popMatrix();
}
