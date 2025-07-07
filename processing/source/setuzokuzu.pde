import javax.swing.JFileChooser;
import java.io.File;
// 機材クラス定義
float size = 10; // サイズを小さくするためのスケール

abstract class Equipment {
  float x, y;
  color c;
  int r;

  Equipment(float x, float y, color c, int r) {
    this.x = x;
    this.y = y;
    this.c = c;
    this.r = r;
  }

  abstract void display();
}

class CircleEquipment extends Equipment {
  float radius;

  CircleEquipment(float x, float y, float radius, color c, int r) {
    super(x, y, c, r);
    this.radius = radius;
  }

  void display() {
    pushMatrix();
    rotate(r * 2*PI/12);
    fill(c);
    ellipse(x, y, radius * 2, radius * 2);
    popMatrix();
  }
}

class RectEquipment extends Equipment {
  float w, h;

  RectEquipment(float x, float y, float w, float h, color c, int r) {
    super(x, y, c, r);
    this.w = w;
    this.h = h;
  }

  void display() {
    pushMatrix();
    rotate(r * 2*PI/12);
    fill(c);
    rect(x, y, w, h);
    popMatrix();
  }
}

class PolygonEquipment extends Equipment {
  float[] xPoints;
  float[] yPoints;

  PolygonEquipment(float x, float y, float[] xPoints, float[] yPoints, color c, int r) {
    super(x, y, c, r);
    this.xPoints = xPoints;
    this.yPoints = yPoints;
  }

  void display() {
    pushMatrix();
    rotate(r * 2*PI/12);
    fill(c);
    beginShape();
    for (int i = 0; i < xPoints.length; i++) {
      vertex(x + xPoints[i], y + yPoints[i]);
    }
    endShape(CLOSE);
    popMatrix();
  }
}

abstract class Line {
  float sx, sy, ex, ey;
  color c;

  Line(float sx, float sy, float ex, float ey, color c) {
    this.sx = sx;
    this.sy = sy;
    this.ex = ex;
    this.ey = ey;
    this.c = c;
  }

  abstract void display();
}

class JustLine extends Line {

  JustLine(float sx, float sy, float ex, float ey, color c) {
    super(sx, sy, ex, ey, c);
  }

  void display() {
    stroke(c);
    strokeWeight(3);
    line(sx, sy, ex, ey);
    strokeWeight(1);
    stroke(0);
  }
}

class LLine extends Line {
  float mx;
  float my;

  LLine(float sx, float sy, float ex, float ey, float mx, float my, color c) {
    super(sx, sy, ex, ey, c);
    this.mx = mx;
    this.my = my;
  }

  void display() {
    stroke(c);
    strokeWeight(3);
    line(sx, sy, mx, my);
    line(mx, my, ex, ey);
    strokeWeight(1);
    stroke(0);
  }
}

class BracketLine extends Line {
  float m1x;
  float m1y;
  float m2x;
  float m2y;

  BracketLine(float sx, float sy, float ex, float ey, float m1x, float m1y, float m2x, float m2y, color c) {
    super(sx, sy, ex, ey, c);
    this.m1x = m1x;
    this.m1y = m1y;
    this.m2x = m2x;
    this.m2y = m2y;
  }

  void display() {
    stroke(c);
    strokeWeight(3);
    line(sx, sy, m1x, m1y);
    line(m1x, m1y, m2x, m2y);
    line(m2x, m2y, ex, ey);
    strokeWeight(1);
    stroke(0);
  }
}

void drawVerticalLines(ArrayList<Equipment> objects) {
  for (int i = 1; i < objects.size(); i++) {
    Equipment obj = objects.get(i);
    float cosValue = cos(obj.r * 2 * PI / 12);
    float sinValue = sin(obj.r * 2 * PI / 12);
    float xValue = obj.x * cosValue - obj.y * sinValue;
    float yValue = obj.x * sinValue + obj.y * cosValue;

    if (xValue - 10 < mouseX && mouseX < xValue + 10) {
      ox = xValue;
      line(ox, 50 + 50, ox, 550 - 50);
    }
    if (yValue - 10 < mouseY && mouseY < yValue +10) {
      oy = yValue;
      line(80, oy, width-15+20, oy);
    }
  }
}

void smartGuides(ArrayList<Equipment> objects) {
  for (int i = 1; i < objects.size(); i++) {
    for (int j = 1; j < 5; j++) {
      Equipment obj = objects.get(i);
      float cosValue = cos(obj.r * 2 * PI / 12);
      float sinValue = sin(obj.r * 2 * PI / 12);
      float xValue = (obj.x+size*1.2*(6.0-12.0/5.0*j)) * cosValue - obj.y * sinValue;
      float yValue = (obj.x+size*1.2*(6.0-12.0/5.0*j)) * sinValue + obj.y * cosValue;

      if (xValue - 10 < mouseX && mouseX < xValue + 10 && yValue - 10 < mouseY && mouseY < yValue +10) {
        ox = xValue;
        line(ox, 50 + 50, ox, 550 - 50);
        oy = yValue;
        line(80, oy, width-15+20, oy);
      }
    }
  }
}

boolean onObject(Equipment obj) {
  float cosValue = cos(obj.r * 2 * PI / 12);
  float sinValue = sin(obj.r * 2 * PI / 12);
  float xValue = obj.x * cosValue - obj.y * sinValue;
  float yValue = obj.x * sinValue + obj.y * cosValue;

  if (obj instanceof CircleEquipment) {
    CircleEquipment circle = (CircleEquipment) obj;
    float r = circle.radius;
    if (pow((mouseX-xValue), 2) + pow((mouseY-yValue), 2) < pow(r, 2)) {
      return true;
    }
  } else if (obj instanceof PolygonEquipment) {
    PolygonEquipment polygon = (PolygonEquipment) obj;

    boolean judge = false;
    float pbx;
    float pby;
    float p0x;
    float p0y;
    float p1x;
    float p1y;
    float p2x;
    float p2y;
    float px = mouseX;
    float py = mouseY;

    pbx = obj.x + polygon.xPoints[0];
    pby = obj.y + polygon.yPoints[0];
    p0x = pbx * cosValue - pby * sinValue;
    p0y = pbx * sinValue + pby * cosValue;

    for (int k = 0; k < polygon.xPoints.length-2; k++) {
      pbx = obj.x + polygon.xPoints[k+1];
      pby = obj.y + polygon.yPoints[k+1];
      p1x = pbx * cosValue - pby * sinValue;
      p1y = pbx * sinValue + pby * cosValue;

      pbx = obj.x + polygon.xPoints[k+2];
      pby = obj.y + polygon.yPoints[k+2];
      p2x = pbx * cosValue - pby * sinValue;
      p2y = pbx * sinValue + pby * cosValue;

      //(p0x, p0y),(p1x, p1y),(p2x, p2y)の三角形
      //(px, py)が判定したい点
      float Area = 0.5 *(-p1y*p2x + p0y*(-p1x + p2x) + p0x*(p1y - p2y) + p1x*p2y);
      float s = 1/(2*Area)*(p0y*p2x - p0x*p2y + (p2y - p0y)*px + (p0x - p2x)*py);
      float t = 1/(2*Area)*(p0x*p1y - p0y*p1x + (p0y - p1y)*px + (p1x - p0x)*py);

      if ((0 <= s && s <= 1) && (0 <= t && t <= 1) && (0<=1-s-t && 1-s-t<=1)) {
        judge = true; //Inside Triangle
      }
    }

    if (judge) {
      return true;
    }
  } else if (obj instanceof RectEquipment) {
    boolean judge1 = false, judge2 = false;
    RectEquipment rect = (RectEquipment) obj;
    float p0x = (obj.x-rect.w/2) * cosValue - (obj.y-rect.h/2) * sinValue;
    float p0y = (obj.x-rect.w/2) * sinValue + (obj.y-rect.h/2) * cosValue;
    float p1x = (obj.x+rect.w/2) * cosValue - (obj.y-rect.h/2) * sinValue;
    float p1y = (obj.x+rect.w/2) * sinValue + (obj.y-rect.h/2) * cosValue;
    float p2x = (obj.x+rect.w/2) * cosValue - (obj.y+rect.h/2) * sinValue;
    float p2y = (obj.x+rect.w/2) * sinValue + (obj.y+rect.h/2) * cosValue;
    float p3x = (obj.x-rect.w/2) * cosValue - (obj.y+rect.h/2) * sinValue;
    float p3y = (obj.x-rect.w/2) * sinValue + (obj.y+rect.h/2) * cosValue;
    float px = mouseX;
    float py = mouseY;

    //(p0x, p0y),(p1x, p1y),(p2x, p2y)の三角形
    //(px, py)が判定したい点
    float Area = 0.5 *(-p1y*p2x + p0y*(-p1x + p2x) + p0x*(p1y - p2y) + p1x*p2y);
    float s = 1/(2*Area)*(p0y*p2x - p0x*p2y + (p2y - p0y)*px + (p0x - p2x)*py);
    float t = 1/(2*Area)*(p0x*p1y - p0y*p1x + (p0y - p1y)*px + (p1x - p0x)*py);

    float Area1 = 0.5 *(-p2y*p3x + p0y*(-p2x + p3x) + p0x*(p2y - p3y) + p2x*p3y);
    float s1 = 1/(2*Area1)*(p0y*p3x - p0x*p3y + (p3y - p0y)*px + (p0x - p3x)*py);
    float t1 = 1/(2*Area1)*(p0x*p2y - p0y*p2x + (p0y - p2y)*px + (p2x - p0x)*py);

    if ((0 < s && s < 1) && (0 < t && t < 1) && (0<1-s-t && 1-s-t<1)) {
      judge1 = true; //Inside Triangle
    }

    if ((0 < s1 && s1 < 1) && (0 < t1 && t1 < 1) && (0<1-s1-t1 && 1-s1-t1<1)) {
      judge2 = true; //Inside Triangle
    }

    if (judge1 || judge2) {
      return true;
    }
  }
  return false;
}

void removeObject(ArrayList<Equipment> objects) {
  boolean removed = false;
  for (int i = objects.size()-1; i > 0; i--) {
    Equipment obj = objects.get(i);
    if (onObject(obj)) {
      objects.remove(i);
      removed = true;
    }
    if (removed) break;
  }
}



void removeLine(ArrayList<Line> Lines) {
  if (touchLine(Lines) != -1)Lines.remove(touchLine(Lines));
}

// 各機材ごとに配列を用意
ArrayList<Equipment> leds;
ArrayList<Equipment> mega64s;
ArrayList<Equipment> movings;
ArrayList<Equipment> par12s;
ArrayList<Equipment> strobes;
ArrayList<Equipment> dekkers;
ArrayList<Equipment> oldColorbars;
ArrayList<Equipment> newColorbars;
ArrayList<Equipment> phantoms;
ArrayList<Equipment> sceneSetters;
ArrayList<Equipment> miniDesks;
ArrayList<Equipment> ePar38s;
ArrayList<Equipment> led38Bs;
ArrayList<Equipment> flatPars;
ArrayList<Equipment> bk75s;
ArrayList<Equipment> par20s;
ArrayList<Equipment> par30s;
ArrayList<Equipment> par46s;
ArrayList<Equipment> bolds;
ArrayList<Equipment> dimmerPacks;
ArrayList<Equipment> tables;
ArrayList<Equipment> stands;
ArrayList<Equipment> trusses;
ArrayList<Line> justLines;
ArrayList<Line> lLines;
ArrayList<Line> bracketLines;

// 各機材を追加する関数
void addLeds(float x, float y, int r) {
  leds.add(new CircleEquipment(x, y, size, color(255, 165, 0), r)); // LED
}

void addMega64s(float x, float y, int r) {
  mega64s.add(new CircleEquipment(x, y, size, color(255, 69, 0), r)); // MEGA64
}

void addMovings(float x, float y, int r) {
  movings.add(new CircleEquipment(x, y, size, color(0, 191, 255), r)); // Moving
}

void addPar12s(float x, float y, int r) {
  par12s.add(new CircleEquipment(x, y, size, color(50, 205, 50), r)); // Par12
}

void addStrobes(float x, float y, int r) {
  strobes.add(new RectEquipment(x, y, size * 2.67, size * 1.33, color(135, 206, 235), r)); // Strobe
}

void addDekkers(float x, float y, int r) {
  dekkers.add(new PolygonEquipment(x, y,
    new float[]{-size, -size, size, size, size * 0.5, -size * 0.5},
    new float[]{-size * 0.5, size * 0.5, size * 0.5, -size * 0.5, -size, -size},
    color(255, 105, 180), r)); // Dekker
}

void addOldColorbars(float x, float y, int r) {
  oldColorbars.add(new RectEquipment(x, y, size * 2.67, size * 0.67, color(240, 255, 255), r)); // 旧colorbar
}

void addNewColorbars(float x, float y, int r) {
  newColorbars.add(new RectEquipment(x, y, size * 2.67, size * 0.67, color(255, 165, 0), r)); // 新colorbar
}

void addPhantoms(float x, float y, int r) {
  phantoms.add(new RectEquipment(x, y, size * 4, size * 2, color(255, 20, 147), r)); // Phantom
}

void addSceneSetters(float x, float y, int r) {
  sceneSetters.add(new RectEquipment(x, y, size * 4, size * 2, color(0, 0, 255), r)); // SceneSetter
}

void addMiniDesks(float x, float y, int r) {
  miniDesks.add(new RectEquipment(x, y, size * 4, size * 2, color(255, 69, 0), r)); // mini卓
}

void addEPar38s(float x, float y, int r) {
  ePar38s.add(new CircleEquipment(x, y, size, color(0, 255, 255), r)); // ePar38
}

void addLed38Bs(float x, float y, int r) {
  led38Bs.add(new CircleEquipment(x, y, size, color(255, 255, 0), r)); // 38B LED
}

void addFlatPars(float x, float y, int r) {
  flatPars.add(new CircleEquipment(x, y, size, color(65, 105, 225), r)); // Flat Par
}

void addBk75s(float x, float y, int r) {
  bk75s.add(new CircleEquipment(x, y, size, color(255, 192, 203), r)); // 75BK
}

void addPar20s(float x, float y, int r) {
  par20s.add(new RectEquipment(x, y, 2*size, 2*size, color(255, 165, 0), r)); // Par20
}

void addPar30s(float x, float y, int r) {
  par30s.add(new RectEquipment(x, y, 2*size, 2*size, color(255, 69, 0), r));  // Par30
}

void addPar46s(float x, float y, int r) {
  par46s.add(new RectEquipment(x, y, 2*size, 2*size, color(0, 191, 255), r)); // Par46
}

void addBolds(float x, float y, int r) {
  bolds.add(new RectEquipment(x, y, size * 4, size * 2, color(138, 43, 226), r)); // Bold
}

void addDimmerPacks(float x, float y, int r) {
  dimmerPacks.add(new RectEquipment(x, y, size * 2, size * 2.5, color(215, 215, 215), r)); // DimmerPack
}

void addTables(float x, float y, int r) {
  tables.add(new RectEquipment(x, y, size * 5.33, size * 2.67, color(255, 255, 255), r)); // Table
}

void addStands(float x, float y, int r) {
  stands.add(new RectEquipment(x, y, size * 12, size * 1.33, color(0, 0, 0), r)); // Stand
}

void addTrusses(float x, float y, int r) {
  trusses.add(new RectEquipment(x, y, size * 12, size * 1.33, color(100, 100, 100), r)); // Truss
}

void addJustLines(float sx, float sy, float ex, float ey, color c) {
  justLines.add(new JustLine(sx, sy, ex, ey, c));
}

void addLLines(float sx, float sy, float ex, float ey, float mx, float my, color c) {
  lLines.add(new LLine(sx, sy, ex, ey, mx, my, c));
}

void addBracketLines(float sx, float sy, float ex, float ey, float m1x, float m1y, float m2x, float m2y, color c) {
  bracketLines.add(new BracketLine(sx, sy, ex, ey, m1x, m1y, m2x, m2y, c));
}

//PFont font;
// メインプログラム
void setup() {
  makeTable = false;
  saving = false;
  /*
  font = loadFont("All.vlw");
   textFont(font, 20);
   */

  size(800, 600);

  // 配列の初期化
  leds = new ArrayList<Equipment>();
  mega64s = new ArrayList<Equipment>();
  movings = new ArrayList<Equipment>();
  par12s = new ArrayList<Equipment>();
  strobes = new ArrayList<Equipment>();
  dekkers = new ArrayList<Equipment>();
  oldColorbars = new ArrayList<Equipment>();
  newColorbars = new ArrayList<Equipment>();
  phantoms = new ArrayList<Equipment>();
  sceneSetters = new ArrayList<Equipment>();
  miniDesks = new ArrayList<Equipment>();
  ePar38s = new ArrayList<Equipment>();
  led38Bs = new ArrayList<Equipment>();
  flatPars = new ArrayList<Equipment>();
  bk75s = new ArrayList<Equipment>();
  par20s = new ArrayList<Equipment>();
  par30s = new ArrayList<Equipment>();
  par46s = new ArrayList<Equipment>();
  bolds = new ArrayList<Equipment>();
  dimmerPacks = new ArrayList<Equipment>();
  tables = new ArrayList<Equipment>();
  stands = new ArrayList<Equipment>();
  trusses = new ArrayList<Equipment>();
  justLines = new ArrayList<Line>();
  lLines = new ArrayList<Line>();
  bracketLines = new ArrayList<Line>();

  // 機材の追加
  addLeds(width/10+width/5, 60, 0);//par
  addMega64s(width/10+2*width/5, 60, 0);
  addMovings(width/10+3*width/5, 60, 0);
  addPar12s(width/10+4*width/5, 60, 0);
  addStrobes(width/10+width/3, 60, 0);//装飾
  addDekkers(width/10+2*width/3, 60, 0);
  addOldColorbars(width/10+width/3, 60, 0);//カラーバー
  addNewColorbars(width/10+2*width/3, 60, 0);
  addPhantoms(width/10+width/4, 60, 0);//卓
  addSceneSetters(width/10+2*width/4, 60, 0);
  addMiniDesks(width/10+3*width/4, 60, 0);
  addEPar38s(width/10+3*width/18, 60, 0);//電軽
  addLed38Bs(width/10+5*width/18, 60, 0);
  addFlatPars(width/10+7*width/18, 60, 0);
  addBk75s(width/10+9*width/18, 60, 0);
  addPar20s(width/10+11*width/18, 60, 0);
  addPar30s(width/10+13*width/18, 60, 0);
  addPar46s(width/10+15*width/18, 60, 0);
  addBolds(width/10+width/3, 60, 0);//その他
  addDimmerPacks(width/10+2*width/3, 60, 0);

  addTables(width/10+width/2, 60, 0);//スタンド類
  addStands(width/10+width/2, 60, 0);
  addTrusses(width/10+width/2, 60, 0);

  addJustLines(width/10+width/5, 50, width/10+width/5, 70, color(0));
  addLLines(width/10+2*width/5-15, 50, width/10+2*width/5+15, 70, width/10+2*width/5-15, 70, color(0));
  addBracketLines(width/10+3*width/5-15, 50, width/10+3*width/5+15, 70, width/10+3*width/5-15, 60, width/10+3*width/5+15, 60, color(0));
  addBracketLines(width/10+4*width/5-15, 50, width/10+4*width/5+15, 70, width/10+4*width/5, 50, width/10+4*width/5, 70, color(0));
}

void draw() {
  oneClick();
  background(240);  // 特定の機材オブジェクトを描画
  rectMode(CENTER);
  textAlign(CENTER, CENTER);
  drawObject();
  if (saving)saveLocation();

  if (!fileing) {
    AddObjects();
    AddLines();
    changeLineType();
  }
  menus();
  tabs();
  if (!fileing) {
    lists();
    removes();
    replaces();
  }
}

void drawObject() {
  for (int i = 1; i <  tables.size(); i++) {
    tables.get(i).display();
  }
  for (int i = 1; i <  stands.size(); i++) {
    stands.get(i).display();
  }
  for (int i = 1; i <  trusses.size(); i++) {
    trusses.get(i).display();
  }
  for (int i = 1; i <  justLines.size(); i++) {
    justLines.get(i).display();
  }
  for (int i = 1; i <  lLines.size(); i++) {
    lLines.get(i).display();
  }
  for (int i = 2; i <  bracketLines.size(); i++) {
    bracketLines.get(i).display();
  }
  for (int i = 1; i < leds.size(); i++) {
    leds.get(i).display();
  }
  for (int i = 1; i < mega64s.size(); i++) {
    mega64s.get(i).display();
  }
  for (int i = 1; i < movings.size(); i++) {
    movings.get(i).display();
  }
  for (int i = 1; i < par12s.size(); i++) {
    par12s.get(i).display();
  }
  for (int i = 1; i < strobes.size(); i++) {
    strobes.get(i).display();
  }
  for (int i = 1; i < dekkers.size(); i++) {
    dekkers.get(i).display();
  }
  for (int i = 1; i < oldColorbars.size(); i++) {
    oldColorbars.get(i).display();
  }
  for (int i = 1; i < newColorbars.size(); i++) {
    newColorbars.get(i).display();
  }
  for (int i = 1; i < phantoms.size(); i++) {
    phantoms.get(i).display();
  }
  for (int i = 1; i < sceneSetters.size(); i++) {
    sceneSetters.get(i).display();
  }
  for (int i = 1; i < miniDesks.size(); i++) {
    miniDesks.get(i).display();
  }
  for (int i = 1; i < ePar38s.size(); i++) {
    ePar38s.get(i).display();
  }
  for (int i = 1; i < led38Bs.size(); i++) {
    led38Bs.get(i).display();
  }
  for (int i = 1; i < flatPars.size(); i++) {
    flatPars.get(i).display();
  }
  for (int i = 1; i < bk75s.size(); i++) {
    bk75s.get(i).display();
  }
  for (int i = 1; i < par20s.size(); i++) {
    par20s.get(i).display();
  }
  for (int i = 1; i < par30s.size(); i++) {
    par30s.get(i).display();
  }
  for (int i = 1; i <  par46s.size(); i++) {
    par46s.get(i).display();
  }
  for (int i = 1; i <  bolds.size(); i++) {
    bolds.get(i).display();
  }
  for (int i = 1; i <  dimmerPacks.size(); i++) {
    dimmerPacks.get(i).display();
  }
}
