boolean saving;
void choseOperation() {
  fill(255);
  rect(width/2, height/2, 600, 150);
  rect(width/2-200, height/2+40, 180, 50);
  rect(width/2, height/2+40, 180, 50);
  rect(width/2+200, height/2+40, 180, 50);
  fill(0);
  text("Chose Operation", width/2, height/2-40);
  text("Open Project", width/2-200, height/2+40);
  text("Save Project", width/2, height/2+40);
  text("Save Location", width/2+200, height/2+40);
  if(click){
    if(width/2-200-90 <= mouseX && mouseX <= width/2-200+90 && height/2+40-25 <= mouseY && mouseY <= height/2+40+25)openProject();
    if(width/2-90 <= mouseX && mouseX <= width/2+90 && height/2+40-25 <= mouseY && mouseY <= height/2+40+25)saveProject();
    if(width/2+200-90 <= mouseX && mouseX <= width/2+200+90 && height/2+40-25 <= mouseY && mouseY <= height/2+40+25){
      fileing = false;
      saving = true;
    }
  }
}
