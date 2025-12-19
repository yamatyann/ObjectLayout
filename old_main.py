# ==========================================
# 定数定義 (Constants)
# ==========================================

# --- Z値 (描画順序: 数値が大きいほど手前) ---
Z_VAL_PREVIEW         = 100.0  # プレビュー、ドラッグ中のアイテム
Z_VAL_EQUIPMENT_FRONT = 30.0   # 配線可能な機材 (最前面)
Z_VAL_EQUIPMENT_STD   = 25.0   # 一般機材
Z_VAL_EQUIPMENT_BACK  = 20.0   # トラス・構造物 (背面)
Z_VAL_OUTLET          = 15.0   # コンセント
Z_VAL_WIRE            = 10.0   # 配線 (機材より下)
Z_VAL_VENUE           = -10.0  # 会場の壁 (最背面)

# --- グリッド・スナップ設定 ---
DEFAULT_GRID_SIZE     = 50.0   # 標準グリッドサイズ
SNAP_DISTANCE_MOUSE   = 15.0   # マウス操作時のスナップ判定距離
SNAP_THRESHOLD_ITEM   = 20.0   # アイテム同士の吸着距離

# ==========================================

import sys
import json
import copy
import os
import uuid
import shutil
import glob
from PySide6.QtWidgets import QApplication, QMainWindow, QDockWidget, QWidget, QListWidget, QLabel, QGraphicsView, QGraphicsScene, QVBoxLayout, QFileDialog, QMessageBox, QGraphicsItem, QLineEdit, QFormLayout, QGraphicsPixmapItem, QGraphicsSimpleTextItem, QListWidgetItem, QGraphicsObject, QCheckBox, QStyle, QStyleOptionGraphicsItem, QDialog, QPushButton, QHBoxLayout, QComboBox, QTreeWidget, QStackedWidget, QTreeWidgetItem, QToolBar, QGraphicsPathItem, QProgressDialog, QTabWidget, QSpinBox, QDoubleSpinBox, QTableWidget, QHeaderView, QTableWidgetItem, QColorDialog, QGraphicsRectItem, QMenu, QAbstractItemView, QRadioButton, QButtonGroup, QGraphicsSceneMouseEvent
from PySide6.QtCore import Qt, Signal, QRect, QSize, QTimer, QPointF, QLineF, QEvent, QRectF, QPoint
from PySide6.QtGui import QPixmap, QColor, QPen, QPainterPath, QAction, QActionGroup, QCursor, QMouseEvent, QPainterPathStroker, QUndoStack, QUndoCommand, QKeySequence, QPainter, QFontMetrics, QPageSize, QPageLayout, QTextDocument, QImage, QFont, QKeyEvent, QPaintEvent, QCloseEvent, QWheelEvent
from PySide6.QtPrintSupport import QPrinter

# ==========================================
# データディレクトリ設定
# ==========================================
if getattr(sys, 'frozen', False): # 実行ファイルのディレクトリ
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
IMAGES_DIR = os.path.join(DATA_DIR, "images")
VENUES_DIR = os.path.join(DATA_DIR, "venues")
LIBRARY_FILE = os.path.join(DATA_DIR, "equipment_library.json")


def ensure_data_directories():
    """必要なフォルダが存在しない場合は作成する"""
    if not os.path.exists(DATA_DIR):
        """データディレクトリの作成"""
        os.makedirs(DATA_DIR)
        print(f"Created data directory: {DATA_DIR}")
    if not os.path.exists(IMAGES_DIR):
        """画像ディレクトリの作成"""
        os.makedirs(IMAGES_DIR)
        print(f"Created images directory: {IMAGES_DIR}")
    if not os.path.exists(VENUES_DIR):
        """会場データディレクトリの作成"""
        os.makedirs(VENUES_DIR)
        print(f"Created venues directory: {VENUES_DIR}")

# アプリ起動時にチェックを実行
ensure_data_directories()

class CustomGraphicsView(QGraphicsView):
    """カスタムグラフィックスビュー（配線・機材配置用）"""
    sceneChanged = Signal()
    
    def __init__(self, scene: QGraphicsScene) -> None:
        """初期化処理"""
        super().__init__(scene)
        self.setAcceptDrops(True)
        self.setMouseTracking(True)
        # ビューポート全体を常に再描画する設定
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        
        # 内部状態の初期化
        self._is_panning = False  # パン操作中かどうか
        self._last_pan_pos = None
        self._r_key_is_pressed = False  # Rキー押下状態
        self._interaction_mode = "cursor"  # 現在の操作モード
        self.show_grid = False  # グリッド表示フラグ
        self.grid_size = int(DEFAULT_GRID_SIZE)  # グリッド間隔
        self._wiring_start_item = None  # 配線開始アイテム
        self._wiring_preview_path = None  # 配線プレビュー用パス
        self._snap_targets = []  # スナップ対象リスト
        self._snap_radius = SNAP_DISTANCE_MOUSE  # スナップ判定半径
        self._current_wiring_points = []  # 現在の配線経路
        self._current_preview_points = []  # プレビュー用経路
        self._wiring_direction_priority = "horizontal"  # 配線の優先方向
        
        self.setDragMode(QGraphicsView.RubberBandDrag)  # デフォルトは範囲選択
    
    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:
        """グリッド背景の描画"""
        super().drawBackground(painter, rect)
        # グリッド表示が有効な場合のみ描画
        if not self.show_grid:
            return
        
        # 現在のズーム倍率を取得
        scale = self.transform().m11()
        if scale == 0:
            scale = 1.0
        
        # グリッド間隔をズームに応じて調整（50px～100pxの範囲に収める）
        base_step = DEFAULT_GRID_SIZE
        step = base_step
        while (step * scale) < 50:
            step *= 2
        while (step * scale) > 100:
            step /= 2
        self.grid_size = step  # スナップ用グリッドサイズも更新
        
        # ペンとフォントの設定
        grid_pen = QPen(QColor(220, 220, 220))  # グリッド線
        grid_pen.setWidth(0)
        text_pen = QPen(QColor(150, 150, 150))  # 座標テキスト
        font = painter.font()
        font.setPointSizeF(10 / scale)  # フォントサイズをズームに合わせて逆補正
        painter.setFont(font)
        
        # 現在画面に見えている範囲（シーン座標）を取得
        viewport_rect = self.viewport().rect()
        visible_scene_rect = self.mapToScene(viewport_rect).boundingRect()
        view_left = visible_scene_rect.left()
        view_top = visible_scene_rect.top()
        offset_x = 5 / scale
        offset_y = 15 / scale
        
        # 縦線とX座標の描画
        left = int(rect.left()) - (int(rect.left()) % step)
        x = left
        while x < rect.right():
            painter.setPen(grid_pen)
            painter.drawLine(x, rect.top(), x, rect.bottom())
            painter.setPen(text_pen)
            painter.drawText(QPointF(x + offset_x, view_top + offset_y), str(int(x)))
            x += step
        
        # 横線とY座標の描画
        top = int(rect.top()) - (int(rect.top()) % step)
        y = top
        while y < rect.bottom():
            painter.setPen(grid_pen)
            painter.drawLine(rect.left(), y, rect.right(), y)
            painter.setPen(text_pen)
            painter.drawText(QPointF(view_left + offset_x, y - (2 / scale)), str(int(y)))
            y += step
    
    def set_interaction_mode(self, mode: str) -> None:
        """操作モードの切り替え"""
        self._cancel_wiring()
        self._interaction_mode = mode
        
        if self._interaction_mode == "cursor":
            self.setCursor(Qt.ArrowCursor)
            self.setDragMode(QGraphicsView.RubberBandDrag)
        else: 
            self.setCursor(Qt.CrossCursor)
            self.setDragMode(QGraphicsView.NoDrag)
            
        # 操作モード切替時にWiringItemのshapeキャッシュを破棄し、再計算させる（itemAtの判定精度維持のため）
        if self.scene():
            for item in self.scene().items():
                if isinstance(item, WiringItem):
                    # これにより、次に itemAt() が呼ばれた際に
                    # 新しいモードに基づいた shape() が呼び出される
                    item.prepareGeometryChange()
    
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """マウス押下イベント処理"""
        if event.button() == Qt.RightButton:
            is_wiring_mode = self._interaction_mode.startswith("wiring_") and self._interaction_mode != "wiring_delete"
            if is_wiring_mode and self._wiring_start_item: self._cancel_wiring()
            event.accept(); return
        if event.button() == Qt.LeftButton and event.modifiers() == Qt.ControlModifier:
            self._is_panning = True; self._last_pan_pos = event.position()
            self.setCursor(Qt.ClosedHandCursor); event.accept(); return
            
        click_pos = event.position().toPoint()
        item_at_click = self.itemAt(click_pos) 
        
        if self._interaction_mode == "cursor":
            if isinstance(item_at_click, WiringItem): event.accept(); return
            super().mousePressEvent(event); return
        
        elif self._interaction_mode == "wiring_delete":
            if isinstance(item_at_click, WiringItem):
                command = CommandRemoveItems([item_at_click], self.scene(), "配線の削除")
                self.mainWindow.undoStack.push(command)
                self.scene().update()
            event.accept(); return
        
        elif self._interaction_mode.startswith("wiring_") and self._interaction_mode != "wiring_delete" and event.button() == Qt.LeftButton:
            current_wire_type = "power" if self._interaction_mode == "wiring_power" else "dmx"
            if isinstance(item_at_click, WiringItem): event.accept(); return
            
            target_item = self._get_target_item_at(click_pos)
            
            if self._wiring_start_item is None:
                if target_item and target_item.can_be_wired:
                    self._wiring_start_item = target_item
                    self._wiring_start_item.setWiringHighlight(True)
                    self._wiring_preview_path = QGraphicsPathItem()
                    self._wiring_preview_path.setData(0, {"type": "preview"})
                    self._wiring_preview_path.setZValue(Z_VAL_PREVIEW)
                    pen = QPen(QColor("white"), 1, Qt.DotLine)
                    self._wiring_preview_path.setPen(pen)
                    self.scene().addItem(self._wiring_preview_path)
                    
                    self._snap_targets = []
                    for item in self.scene().items():
                        if isinstance(item, (EquipmentItem, OutletItem)) and item != self._wiring_start_item:
                            self._snap_targets.append(item)
            else:
                self._current_wiring_points.extend(self._current_preview_points)
                if len(self._current_wiring_points) >= 2:
                    p1 = self._current_wiring_points[-2]
                    p2 = self._current_wiring_points[-1]
                    if len(self._current_wiring_points) == 2:
                        # 配線開始アイテムの中心座標を取得（EquipmentItemの場合は画像中心、それ以外は位置）
                        if isinstance(self._wiring_start_item, EquipmentItem):
                            p0 = self._wiring_start_item.pos() + self._wiring_start_item.image.boundingRect().center()
                        else:
                            p0 = self._wiring_start_item.pos()
                    else:
                        p0 = self._current_wiring_points[-3]
                    if (p0.x() == p1.x() == p2.x()) or (p0.y() == p1.y() == p2.y()):
                        self._current_wiring_points.pop(-2)
                
                if target_item and target_item.can_be_wired and target_item != self._wiring_start_item:
                    start_item_copy = self._wiring_start_item
                    end_item_copy = target_item
                    points_copy = self._current_wiring_points.copy()
                    QTimer.singleShot(0, lambda: self._add_wire_async(start_item_copy, end_item_copy, points_copy, current_wire_type))
                    self._cancel_wiring() 
                elif not target_item:
                    pass
            event.accept(); return
        super().mousePressEvent(event)
    
    # 非同期スロット
    def _add_wire_async(self, start_item: 'EquipmentItem', end_item: 'EquipmentItem', points: list, wire_type: str = "dmx") -> None:
        """非同期で配線アイテムを追加"""
        print("タイマーで WiringItem を追加")
        # ここで wire_type を指定可能ですが、現状の配線モードはDMXと仮定
        wire = WiringItem(start_item, end_item, points, wire_type=wire_type) 
        wire.setData(0, {"type": "wire"}) 
        wire.setZValue(Z_VAL_WIRE)
        
        command = CommandAddItems(wire, self.scene(), "配線の追加")
        if self.mainWindow and self.mainWindow.undoStack:
             self.mainWindow.undoStack.push(command)
        else:
             print("エラー: undoStack が見つかりません。")
             self.scene().addItem(wire) # フォールバック
    
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """マウス移動イベント処理"""
        if self._is_panning:
            delta = event.position() - self._last_pan_pos
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - int(delta.x()))
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - int(delta.y()))
            self._last_pan_pos = event.position(); event.accept(); return 
        
        if self._interaction_mode.startswith("wiring_") and self._interaction_mode != "wiring_delete":
            if self._wiring_start_item and self._wiring_preview_path:
                current_pos_scene = self.mapToScene(event.position().toPoint())
                
                # 配線開始アイテムの中心座標を取得（EquipmentItemの場合は画像中心、それ以外は位置）
                if isinstance(self._wiring_start_item, EquipmentItem):
                    start_center = self._wiring_start_item.pos() + self._wiring_start_item.image.boundingRect().center()
                else:
                    start_center = self._wiring_start_item.pos()
                
                if not self._current_wiring_points:
                    last_pos = start_center
                else:
                    last_pos = self._current_wiring_points[-1]
                
                path = QPainterPath()
                path.moveTo(start_center)
                for point in self._current_wiring_points: path.lineTo(point)
                self._current_preview_points = []
                
                target_item = None
                for item in self._snap_targets:
                    # スナップ対象アイテムの中心座標を取得（EquipmentItemの場合は画像中心、それ以外は位置）
                    if isinstance(item, EquipmentItem):
                        item_center = item.pos() + item.image.boundingRect().center()
                    else:
                        item_center = item.pos()
                        
                    dx = abs(current_pos_scene.x() - item_center.x())
                    dy = abs(current_pos_scene.y() - item_center.y())
                    if dx < self._snap_radius and dy < self._snap_radius:
                        target_item = item
                        break
                
                if target_item:
                    # A: スナップする場合
                    if isinstance(target_item, EquipmentItem):
                        end_pos = target_item.pos() + target_item.image.boundingRect().center()
                    else:
                        end_pos = target_item.pos()
                        
                    if self._wiring_direction_priority == "horizontal":
                        first_corner = QPointF(end_pos.x(), last_pos.y())
                        second_corner = QPointF(end_pos.x(), end_pos.y())
                    else:
                        first_corner = QPointF(last_pos.x(), end_pos.y())
                        second_corner = QPointF(end_pos.x(), end_pos.y())
                    self._current_preview_points.append(first_corner)
                    path.lineTo(first_corner); path.lineTo(second_corner)
                else:
                    # B: スナップしない場合
                    dx = current_pos_scene.x() - last_pos.x()
                    dy = current_pos_scene.y() - last_pos.y()
                    if abs(dx) > abs(dy):
                        snapped_pos = QPointF(current_pos_scene.x(), last_pos.y())
                    else:
                        snapped_pos = QPointF(last_pos.x(), current_pos_scene.y())
                    self._current_preview_points.append(snapped_pos)
                    path.lineTo(snapped_pos)
                
                self._wiring_preview_path.setPath(path)
            event.accept(); return 
            
        elif self._interaction_mode == "wiring_delete":
            if event.buttons() & Qt.LeftButton:
                item_under_cursor = self.itemAt(event.position().toPoint())
                if isinstance(item_under_cursor, WiringItem):
                    command = CommandRemoveItems([item_under_cursor], self.scene(), "配線の削除")
                    self.mainWindow.undoStack.push(command)
                    self.scene().update()
            event.accept(); return
            
        elif self._interaction_mode == "cursor":
            super().mouseMoveEvent(event)
        else:
            event.accept(); return
    
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """マウスリリースイベント処理"""
        if self._is_panning and event.button() == Qt.LeftButton:
            self._is_panning = False
            self.setCursor(Qt.ArrowCursor) 
            event.accept()
            return
        super().mouseReleaseEvent(event)
    
    def dragEnterEvent(self, event: QEvent) -> None:
        """ドラッグ開始イベント処理"""
        if event.mimeData().hasFormat('application/x-qabstractitemmodeldatalist'): event.acceptProposedAction()
    
    def dragMoveEvent(self, event: QEvent) -> None:
        """ドラッグ移動イベント処理"""
        if event.mimeData().hasFormat('application/x-qabstractitemmodeldatalist'): event.acceptProposedAction()
    
    def dropEvent(self, event: QEvent) -> None:
        """ドロップイベント処理"""
        if self._interaction_mode != "cursor":
            event.ignore()
            return
        source = event.source()
        if not isinstance(source, QTreeWidget): return
        item_data = source.currentItem().data(0, Qt.UserRole)
        if not item_data or item_data.get("type") != "equipment": return
        equipment_item = EquipmentItem(item_data)
        scene_pos = self.mapToScene(event.position().toPoint())
        equipment_item.setPos(scene_pos)
        # self.scene().addItem(equipment_item)
        command = CommandAddItems(equipment_item, self.scene(), "機材の配置")
        if self.mainWindow and self.mainWindow.undoStack:
            self.mainWindow.undoStack.push(command)
        else:
            print("エラー: undoStack が見つかりません。")
            self.scene().addItem(equipment_item) # フォールバック
        event.acceptProposedAction()
        # self.sceneChanged.emit() # <- undoStack が管理するので削除
    
    def wheelEvent(self, event: QEvent) -> None:
        """マウスホイールイベント処理"""
        if self._r_key_is_pressed:
            selected_items = [item for item in self.scene().selectedItems() if isinstance(item, EquipmentItem)]
            if not selected_items: return
            
            delta = 1.5 if event.angleDelta().y() > 0 else -1.5
            
            # 回転操作は直接値を変更せず、変更前後の値をコマンドとしてまとめて管理（Undo/Redo対応のため）
            items_with_rot = []
            for item in selected_items:
                old_rot = item.rotation()
                new_rot = (old_rot + delta) % 360
                items_with_rot.append((item, old_rot, new_rot))
            
            if items_with_rot and self.mainWindow and self.mainWindow.undoStack:
                cmd = CommandRotateItems(items_with_rot, "アイテムの回転")
                self.mainWindow.undoStack.push(cmd)
            
            # self.sceneChanged.emit() # <- undoStackが管理するので削除
            
        elif event.modifiers() == Qt.ControlModifier:
            zoom_factor = 1.25 if event.angleDelta().y() > 0 else 1 / 1.25
            self.scale(zoom_factor, zoom_factor)
        else:
            super().wheelEvent(event)
    
    def _redraw_all_wires(self) -> None:
        """全WiringItemの再描画"""
        for item in self.scene().items():
            if isinstance(item, WiringItem):
                item.update_path()
    
    def keyPressEvent(self, event: QKeyEvent) -> None:
        """キーボード押下イベント処理"""
        if event.key() == Qt.Key_R:
            self._r_key_is_pressed = True
        elif event.key() == Qt.Key_Space:
            if self._wiring_direction_priority == "horizontal":
                self._wiring_direction_priority = "vertical"
            else:
                self._wiring_direction_priority = "horizontal"
            is_wiring_mode = self._interaction_mode.startswith("wiring_") and self._interaction_mode != "wiring_delete"
            
            if is_wiring_mode and self._wiring_start_item and self._wiring_preview_path:
                cursor_pos = self.mapFromGlobal(QCursor.pos())
                
                # (Deprecation Warning 対策済み)
                fake_event = QMouseEvent(QEvent.Type.MouseMove, cursor_pos, Qt.MouseButton.NoButton, Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier)
                
                self.mouseMoveEvent(fake_event)
        elif event.key() == Qt.Key_Delete:
            selected_items = self.scene().selectedItems()
            if selected_items:
                # (アイテム削除と関連配線削除のロジックは CommandRemoveItems に移譲)
                command = CommandRemoveItems(selected_items, self.scene(), "アイテムの削除")
                self.mainWindow.undoStack.push(command)
                # items_to_delete = set(selected_items)
                # wires_to_remove = []
                # all_wires = [item for item in self.scene().items() if isinstance(item, WiringItem)]
                # for item in selected_items:
                #     if isinstance(item, EquipmentItem):
                #         for wire in all_wires:
                #             if wire.start_item is item or wire.end_item is item:
                #                 wires_to_remove.append(wire)
                # items_to_delete.update(wires_to_remove)
                # for item in items_to_delete:
                #     if item.scene(): 
                #         self.scene().removeItem(item)
                # self.sceneChanged.emit()
                # self.scene().update()
        else:
            super().keyPressEvent(event)
    
    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        """キーボードリリースイベント処理"""
        if event.key() == Qt.Key_R:
            self._r_key_is_pressed = False
        else:
            super().keyReleaseEvent(event)
    
    def _cancel_wiring(self) -> None:
        """配線操作のキャンセル処理"""
        print("配線操作をキャンセルしました。")
        if self._wiring_start_item:
            self._wiring_start_item.setWiringHighlight(False)
        if self._wiring_preview_path:
            data = self._wiring_preview_path.data(0) if hasattr(self._wiring_preview_path, 'data') else None
            if data and isinstance(data, dict) and data.get("type") == "preview":
                self.scene().removeItem(self._wiring_preview_path)
        self._wiring_start_item = None
        self._wiring_preview_path = None
        self._current_wiring_points = []
        self._current_preview_points = []
        self._snap_targets = [] # スナップ対象リストをクリア（前回の状態を残さないため）
    
    def _get_target_item_at(self, pos: QPointF) -> object:
        """指定座標にある配線可能なアイテムを返す"""
        # クリック判定用の矩形作成
        rect = QRect(pos - QPointF(5, 5).toPoint(), QSize(10, 10))
        items = self.items(rect)
        
        for item in items:
            temp = item
            # 親を遡って対象クラスを探す
            while temp:
                if isinstance(temp, (EquipmentItem, OutletItem)):
                    return temp
                temp = temp.parentItem()
        return None

class SnapPreviewWidget(QWidget):
    """スナップ点プレビュー用ウィジェット"""
    def __init__(self, parent: QWidget = None) -> None:
        """初期化処理"""
        super().__init__(parent)
        self.setMinimumHeight(200) # 最低限の高さを確保
        self.image_path = None
        self.snap_points = []
        self._pixmap = None
    
    def set_data(self, image_path: str, points: list) -> None:
        """画像パスとスナップ点リストの設定"""
        self.image_path = image_path
        self.snap_points = points
        
        load_path = image_path
        if image_path and not os.path.exists(image_path):
            # DATA_DIR 基準で探す
            alt_path = os.path.join(DATA_DIR, image_path)
            if os.path.exists(alt_path):
                load_path = alt_path
        
        if load_path and os.path.exists(load_path):
            self._pixmap = QPixmap(load_path)
        else:
            self._pixmap = None
        self.update() # 再描画
    
    def paintEvent(self, event: QPaintEvent) -> None:
        """ウィジェット描画処理"""
        painter = QPainter(self)
        # 背景を薄いグレーに
        painter.fillRect(self.rect(), QColor(240, 240, 240))
        
        # 枠線
        painter.setPen(QColor("gray"))
        painter.drawRect(0, 0, self.width()-1, self.height()-1)
        
        if not self._pixmap or self._pixmap.isNull():
            painter.setPen(QColor("black"))
            painter.drawText(self.rect(), Qt.AlignCenter, "画像なし")
            return
        
        # --- 画像をウィジェットのサイズに合わせて縮小表示 ---
        w = self.width()
        h = self.height()
        img_w = self._pixmap.width()
        img_h = self._pixmap.height()
        
        if img_w == 0 or img_h == 0: return
        
        # アスペクト比を維持して収まる倍率を計算
        scale = min((w - 20) / img_w, (h - 20) / img_h, 1.0)
        
        # 描画位置（中央寄せ）
        scaled_w = img_w * scale
        scaled_h = img_h * scale
        offset_x = (w - scaled_w) / 2
        offset_y = (h - scaled_h) / 2
        
        painter.save()
        painter.translate(offset_x, offset_y)
        painter.scale(scale, scale)
        
        # 1. 画像を描画
        painter.drawPixmap(0, 0, self._pixmap)
        
        # 2. スナップ点を描画
        # スナップ点のデータは「画像の中心からの相対座標」
        center_x = img_w / 2
        center_y = img_h / 2
        
        # 見やすいように赤枠・黄色塗りつぶしの円にする
        pen = QPen(QColor("red"))
        pen.setWidthF(2.0 / scale) # 縮小されても線の太さを維持する工夫
        painter.setPen(pen)
        painter.setBrush(QColor("yellow"))
        
        for pt in self.snap_points:
            x = pt.get("x", 0)
            y = pt.get("y", 0)
            
            # 画像上の座標に変換
            pt_scene_x = center_x + x
            pt_scene_y = center_y + y
            
            # 円を描画 (半径5px程度の見た目になるように)
            radius = 5.0 / scale 
            painter.drawEllipse(QPointF(pt_scene_x, pt_scene_y), radius, radius)
        
        painter.restore()

class NumericTableWidgetItem(QTableWidgetItem):
    """数値としてソート可能なテーブルアイテム"""
    def __lt__(self, other: QTableWidgetItem) -> bool:
        """大小比較（数値優先）"""
        try:
            return float(self.text()) < float(other.text())
        except ValueError:
            return super().__lt__(other)

class FilterHeaderView(QHeaderView):
    """フィルタ機能付きヘッダー"""
    filterChanged = Signal()
    
    def __init__(self, parent: QWidget = None) -> None:
        """初期化処理"""
        super().__init__(Qt.Horizontal, parent)
        self._filters = {} # col: set(checked_values)
        self._button_padding = 20 # アイコンの幅
        self.setSectionsClickable(True)
        self.setHighlightSections(True)
        # フィルタ対象の列インデックス (1:機材名, 2:メーカー)
        self.filter_columns = [1, 2] 
    
    def paintSection(self, painter: QPainter, rect: QRect, logicalIndex: int) -> None:
        """ヘッダーセクション描画処理"""
        painter.save()
        super().paintSection(painter, rect, logicalIndex)
        painter.restore()
        
        # フィルタ対象列ならアイコンを描画
        if logicalIndex in self.filter_columns:
            icon_size = 12
            icon_x = rect.right() - icon_size - 5
            icon_y = rect.center().y() - icon_size / 2
            
            # フィルタ適用中なら色を変えるなどの処理も可能
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing)
            
            # 簡易的な「漏斗」アイコンを描画
            if logicalIndex in self._filters:
                painter.setBrush(QColor(255, 100, 100)) # フィルタ適用中は赤
            else:
                painter.setBrush(QColor(200, 200, 200)) # 通常はグレー
                
            path = QPainterPath()
            path.moveTo(icon_x, icon_y)
            path.lineTo(icon_x + icon_size, icon_y)
            path.lineTo(icon_x + icon_size / 2, icon_y + icon_size)
            path.closeSubpath()
            
            painter.setPen(Qt.NoPen)
            painter.drawPath(path)
            painter.restore()
    
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """ヘッダークリックイベント処理"""
        # フィルタアイコン付近のクリック判定
        logicalIndex = self.logicalIndexAt(event.position().toPoint())
        
        if logicalIndex in self.filter_columns:
            # セクションの右端付近をクリックしたかチェック
            rect = self.sectionViewportPosition(logicalIndex)
            section_width = self.sectionSize(logicalIndex)
            click_x_in_section = event.position().x() - rect
            
            # 右端の20px以内ならフィルタメニューを開く
            if click_x_in_section > section_width - self._button_padding:
                self.showFilterMenu(logicalIndex)
                return # ソート処理に行かないようにここで終了
    
        # それ以外は通常のクリック（ソートなど）
        super().mousePressEvent(event)
    
    def showFilterMenu(self, logicalIndex: int) -> None:
        """フィルタメニュー表示処理"""
        table = self.parent()
        if not table: return
        
        # カラム内のユニークな値を取得
        values = set()
        for row in range(table.rowCount()):
            item = table.item(row, logicalIndex)
            if item:
                values.add(item.text())
        
        sorted_values = sorted(list(values))
        
        menu = QMenu(self)
        
        # "すべて選択" アクション
        all_action = QAction("すべて選択", menu)
        all_action.triggered.connect(lambda: self.setFilter(logicalIndex, None))
        menu.addAction(all_action)
        menu.addSeparator()
        
        # 現在のフィルタ状態
        current_filter = self._filters.get(logicalIndex, None)
        
        # 各値のチェックボックス
        actions = []
        for val in sorted_values:
            action = QAction(val, menu)
            action.setCheckable(True)
            # フィルタがNone(全表示) または 値が含まれているならチェック
            if current_filter is None or val in current_filter:
                action.setChecked(True)
            actions.append(action)
            menu.addAction(action)
            
        # メニュー表示して実行
        menu.exec(QCursor.pos())
        
        # メニューが閉じたら状態を更新
        new_filter = set()
        for action in actions:
            if action.isChecked():
                new_filter.add(action.text())
        
        # 全選択されているかチェック
        if len(new_filter) == len(sorted_values):
            self.setFilter(logicalIndex, None) # 全選択扱い
        else:
            self.setFilter(logicalIndex, new_filter)
    
    def setFilter(self, logicalIndex: int, values: set | None) -> None:
        """フィルタ条件の設定"""
        if values is None:
            if logicalIndex in self._filters:
                del self._filters[logicalIndex]
        else:
            self._filters[logicalIndex] = values
        self.filterChanged.emit()
    
    def isRowVisible(self, row: int, table: QTableWidget) -> bool:
        """指定された行が現在のフィルタ条件を満たすか"""
        for col, allowed_values in self._filters.items():
            item = table.item(row, col)
            val = item.text() if item else ""
            if val not in allowed_values:
                return False
        return True

class EquipmentManagerDialog(QDialog):
    """機材ライブラリ管理ダイアログ"""
    def __init__(self, equipment_data: dict, parent: QWidget = None) -> None:
        """初期化処理"""
        super().__init__(parent)
        self.setWindowTitle("機材ライブラリ管理")
        self.setMinimumSize(1100, 750) # 詳細表示のため少し大きく
        self.tree_data = copy.deepcopy(equipment_data)
        
        # --- UI構築 ---
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("機材名、メーカー名で検索...")
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.setDragEnabled(True)
        self.tree_widget.setAcceptDrops(True)
        self.tree_widget.setDragDropMode(QAbstractItemView.InternalMove)
        self.tree_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        
        self.add_button = QPushButton("+ 追加")
        self.delete_button = QPushButton("- 削除")
        
        tree_button_layout = QHBoxLayout()
        tree_button_layout.addWidget(self.add_button)
        tree_button_layout.addWidget(self.delete_button)
        tree_button_layout.addStretch()
        
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.search_bar)
        left_layout.addWidget(self.tree_widget)
        left_layout.addLayout(tree_button_layout)
        
        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        
        # --- 右側：詳細編集 ---
        self.stacked_widget = QStackedWidget()
        
        # ページ0, 1
        self.placeholder_page = QWidget()
        
        folder_page = QWidget()
        folder_layout = QFormLayout()
        self.folder_name_edit = QLineEdit()
        folder_layout.addRow("フォルダ名:", self.folder_name_edit)
        folder_page.setLayout(folder_layout)
        
        # ページ2: 機材編集
        equipment_page = QWidget()
        equip_main_layout = QVBoxLayout()
        self.equip_tabs = QTabWidget()
        
        # -- タブ1: 基本情報 --
        basic_info_widget = QWidget()
        self.equip_name_edit = QLineEdit()
        self.manufacturer_edit = QLineEdit()
        self.image_path_edit = QLineEdit()
        self.browse_button = QPushButton("参照...")
        self.width_spin = QSpinBox()
        self.width_spin.setRange(10, 2000); self.width_spin.setValue(50); self.width_spin.setSuffix(" px")
        
        image_path_layout = QHBoxLayout()
        image_path_layout.addWidget(self.image_path_edit)
        image_path_layout.addWidget(self.browse_button)
        
        basic_form = QFormLayout()
        basic_form.addRow("機材名:", self.equip_name_edit)
        basic_form.addRow("メーカー:", self.manufacturer_edit)
        basic_form.addRow("画像パス:", image_path_layout)
        basic_form.addRow("基準サイズ(幅):", self.width_spin)
        basic_info_widget.setLayout(basic_form)
        self.equip_tabs.addTab(basic_info_widget, "基本情報")
        
        # -- タブ2: 接続・DMX設定 --
        connection_widget = QWidget()
        conn_layout = QVBoxLayout()
        
        # 電源
        power_group = QWidget()
        power_layout = QHBoxLayout(power_group)
        self.has_power_check = QCheckBox("電源を使用する")
        self.power_spin = QSpinBox()
        self.power_spin.setRange(0, 20000); self.power_spin.setSuffix(" W")
        power_layout.addWidget(self.has_power_check)
        power_layout.addWidget(QLabel("消費電力:"))
        power_layout.addWidget(self.power_spin)
        power_layout.addStretch()
        
        # DMX設定エリア
        dmx_group = QWidget()
        dmx_layout = QVBoxLayout(dmx_group)
        dmx_top_layout = QHBoxLayout()
        self.has_dmx_check = QCheckBox("DMXを使用する")
        self.is_controller_check = QCheckBox("コントローラー(卓)として使用")
        dmx_top_layout.addWidget(self.has_dmx_check)
        dmx_top_layout.addWidget(self.is_controller_check)
        dmx_top_layout.addStretch()
        
        # === モードエディタ (2段構成) ===
        self.mode_editor_widget = QWidget()
        mode_edit_layout = QVBoxLayout(self.mode_editor_widget)
        mode_edit_layout.setContentsMargins(0, 0, 0, 0)
        
        # 1. 上段: モード一覧テーブル
        mode_edit_layout.addWidget(QLabel("<b>1. DMXモード一覧</b>"))
        
        mode_input_layout = QHBoxLayout()
        self.new_mode_name = QLineEdit()
        self.new_mode_name.setPlaceholderText("モード名 (例: 4ch Mode)")
        self.new_mode_ch = QSpinBox()
        self.new_mode_ch.setRange(1, 512); self.new_mode_ch.setSuffix(" ch")
        btn_add_mode = QPushButton("追加")
        btn_add_mode.clicked.connect(self._add_dmx_mode)
        mode_input_layout.addWidget(self.new_mode_name, 2)
        mode_input_layout.addWidget(self.new_mode_ch, 1)
        mode_input_layout.addWidget(btn_add_mode)
        
        self.modes_table = QTableWidget(0, 2)
        self.modes_table.setHorizontalHeaderLabels(["モード名", "使用ch数"])
        self.modes_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.modes_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.modes_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.modes_table.setSortingEnabled(True) # モード一覧のソートを有効化（ユーザー利便性向上のため）
        self.modes_table.itemSelectionChanged.connect(self._on_mode_selection_changed)
        
        btn_del_mode = QPushButton("選択したモードを削除")
        btn_del_mode.clicked.connect(self._delete_dmx_mode)
        
        mode_edit_layout.addLayout(mode_input_layout)
        mode_edit_layout.addWidget(self.modes_table)
        mode_edit_layout.addWidget(btn_del_mode)
        
        # 2. 下段: チャンネル詳細テーブル
        self.ch_detail_label = QLabel("<b>2. チャンネル詳細設定 (モードを選択してください)</b>")
        mode_edit_layout.addSpacing(10)
        mode_edit_layout.addWidget(self.ch_detail_label)
        
        self.ch_detail_table = QTableWidget(0, 2)
        self.ch_detail_table.setHorizontalHeaderLabels(["Ch", "機能 / パラメータ"])
        self.ch_detail_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.ch_detail_table.verticalHeader().setVisible(False)
        self.ch_detail_table.itemChanged.connect(self._on_ch_detail_changed) # 編集検知
        
        mode_edit_layout.addWidget(self.ch_detail_table)
        
        dmx_layout.addLayout(dmx_top_layout)
        dmx_layout.addWidget(self.mode_editor_widget)
        
        conn_layout.addWidget(QLabel("<b>電源設定</b>"))
        conn_layout.addWidget(power_group)
        conn_layout.addWidget(QLabel("<b>DMX設定</b>"))
        conn_layout.addWidget(dmx_group)
        
        connection_widget.setLayout(conn_layout)
        self.equip_tabs.addTab(connection_widget, "接続・DMX")
        
        # -- タブ3: スナップ点 --
        snap_point_widget = QWidget()
        gen_group = QWidget(); gen_layout = QHBoxLayout(gen_group); gen_layout.setContentsMargins(0,0,0,0)
        self.snap_div_spin = QSpinBox(); self.snap_div_spin.setRange(1, 50); self.snap_div_spin.setValue(4); self.snap_div_spin.setSuffix(" 分割")
        self.snap_y_offset_spin = QDoubleSpinBox(); self.snap_y_offset_spin.setRange(-1000, 1000); self.snap_y_offset_spin.setSuffix(" px")
        btn_gen = QPushButton("追加生成"); btn_gen.clicked.connect(self._generate_snap_points)
        gen_layout.addWidget(QLabel("分割数:")); gen_layout.addWidget(self.snap_div_spin)
        gen_layout.addWidget(QLabel("Y位置:")); gen_layout.addWidget(self.snap_y_offset_spin)
        gen_layout.addWidget(btn_gen); gen_layout.addStretch()
        self.snap_table = QTableWidget(0, 2)
        self.snap_table.setHorizontalHeaderLabels(["X", "Y"]); self.snap_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        btn_add_pt = QPushButton("+"); btn_add_pt.clicked.connect(self._add_empty_snap_row)
        btn_del_pt = QPushButton("-"); btn_del_pt.clicked.connect(self._delete_selected_snap_row)
        btn_clear_pt = QPushButton("クリア"); btn_clear_pt.clicked.connect(self._clear_snap_points)
        btns_layout = QHBoxLayout(); btns_layout.addWidget(btn_add_pt); btns_layout.addWidget(btn_del_pt); btns_layout.addStretch(); btns_layout.addWidget(btn_clear_pt)
        self.preview_widget = SnapPreviewWidget()
        snap_layout = QVBoxLayout(); snap_layout.addWidget(gen_group)
        mid_layout = QHBoxLayout(); t_layout = QVBoxLayout(); t_layout.addWidget(self.snap_table); t_layout.addLayout(btns_layout)
        mid_layout.addLayout(t_layout, 1); mid_layout.addWidget(self.preview_widget, 1)
        snap_layout.addLayout(mid_layout); snap_point_widget.setLayout(snap_layout)
        self.equip_tabs.addTab(snap_point_widget, "スナップ点")
        
        # --- レイアウト組み立て ---
        equip_main_layout.addWidget(self.equip_tabs)
        equipment_page.setLayout(equip_main_layout)
        self.stacked_widget.addWidget(self.placeholder_page)
        self.stacked_widget.addWidget(folder_page)
        self.stacked_widget.addWidget(equipment_page)
        self.ok_button = QPushButton("OK"); self.cancel_button = QPushButton("キャンセル")
        main_layout = QHBoxLayout(); main_layout.addWidget(left_widget, 2); main_layout.addWidget(self.stacked_widget, 3)
        bottom_button_layout = QHBoxLayout(); bottom_button_layout.addStretch(); bottom_button_layout.addWidget(self.ok_button); bottom_button_layout.addWidget(self.cancel_button)
        dialog_layout = QVBoxLayout(); dialog_layout.addLayout(main_layout); dialog_layout.addLayout(bottom_button_layout)
        self.setLayout(dialog_layout)
        
        # --- シグナル接続 ---
        self._populate_tree()
        self.tree_widget.currentItemChanged.connect(self._on_selection_changed)
        
        self.folder_name_edit.textChanged.connect(self._on_form_edited)
        self.equip_name_edit.textChanged.connect(self._on_form_edited)
        self.manufacturer_edit.textChanged.connect(self._on_form_edited)
        self.image_path_edit.textChanged.connect(self._on_form_edited)
        self.width_spin.valueChanged.connect(self._on_form_edited)
        
        self.has_power_check.toggled.connect(self._on_connection_settings_changed)
        self.power_spin.valueChanged.connect(self._on_form_edited)
        self.has_dmx_check.toggled.connect(self._on_connection_settings_changed)
        self.is_controller_check.toggled.connect(self._on_form_edited)
        
        self.modes_table.itemChanged.connect(self._on_mode_table_changed) # モード名/ch数変更時
        
        self.snap_table.itemChanged.connect(self._on_snap_table_changed)
        self.browse_button.clicked.connect(self._browse_for_image)
        self.add_button.clicked.connect(self._add_item)
        self.delete_button.clicked.connect(self._delete_item)
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
    
    def _populate_tree(self) -> None:
        """ツリーウィジェットをデータから構築"""
        self.tree_widget.clear()
        self._add_items_recursively(self.tree_widget, self.tree_data)
        self.tree_widget.expandAll()
    
    def _add_items_recursively(self, parent_widget: QTreeWidgetItem, children_data: list[dict]) -> None:
        """ツリー項目を再帰的に追加"""
        for item_data in children_data:
            tree_item = QTreeWidgetItem(parent_widget)
            tree_item.setText(0, item_data["name"])
            tree_item.setData(0, Qt.UserRole, item_data)
            if item_data.get("type") == "folder":
                tree_item.setFlags(tree_item.flags() | Qt.ItemIsDropEnabled | Qt.ItemIsDragEnabled)
                if "children" in item_data: self._add_items_recursively(tree_item, item_data["children"])
            elif item_data.get("type") == "equipment":
                tree_item.setFlags((tree_item.flags() | Qt.ItemIsDragEnabled) & ~Qt.ItemIsDropEnabled)
    
    def _on_selection_changed(self) -> None:
        """ツリー選択変更時のUI更新"""
        selected_item = self.tree_widget.currentItem()
        if not selected_item: self.stacked_widget.setCurrentIndex(0); return
        item_data = selected_item.data(0, Qt.UserRole)
        
        if item_data["type"] == "folder":
            self.stacked_widget.setCurrentIndex(1)
            self.folder_name_edit.setText(item_data["name"])
        elif item_data["type"] == "equipment":
            self.stacked_widget.setCurrentIndex(2)
            self.equip_name_edit.setText(item_data["name"])
            self.manufacturer_edit.setText(item_data.get("manufacturer", ""))
            self.image_path_edit.setText(item_data.get("image_path", ""))
            self.width_spin.blockSignals(True); self.width_spin.setValue(item_data.get("default_width", 50)); self.width_spin.blockSignals(False)
            
            has_power = item_data.get("has_power", item_data.get("can_be_wired", False))
            has_dmx = item_data.get("has_dmx", item_data.get("can_be_wired", False))
            self.has_power_check.setChecked(has_power)
            self.power_spin.setValue(item_data.get("power_consumption", 0))
            self.has_dmx_check.setChecked(has_dmx)
            self.is_controller_check.setChecked(item_data.get("is_controller", False))
            
            # モードリスト読み込み
            modes = item_data.get("dmx_modes", [])
            self._load_modes_to_table(modes)
            
            self._update_ui_state()
            self._load_snap_points_to_table(item_data.get("snap_points", []))
            self._update_preview()
    
    def _load_snap_points_to_table(self, points: list[dict]) -> None:
        """スナップ点データをテーブルに表示"""
        self.snap_table.blockSignals(True)
        self.snap_table.setRowCount(0)
        for pt in points:
            row = self.snap_table.rowCount()
            self.snap_table.insertRow(row)
            # X
            item_x = QTableWidgetItem(str(pt.get("x", 0)))
            self.snap_table.setItem(row, 0, item_x)
            # Y
            item_y = QTableWidgetItem(str(pt.get("y", 0)))
            self.snap_table.setItem(row, 1, item_y)
        self.snap_table.blockSignals(False)
    
    def _on_snap_table_changed(self, item: QTableWidgetItem) -> None:
        """スナップ点テーブル編集時のデータ反映"""
        self._save_current_snap_points()
    
    def _save_current_snap_points(self) -> None:
        """スナップ点テーブル内容をデータに保存"""
        selected_item = self.tree_widget.currentItem()
        if not selected_item: return
        
        # ツリーアイテムが持つデータのコピーを取得
        item_data_copy = selected_item.data(0, Qt.UserRole)
        if item_data_copy["type"] != "equipment": return
        
        # 大元のデータを検索して更新対象にする
        target_id = item_data_copy["id"]
        real_item_data = self._find_data_by_id(self.tree_data, target_id)
        if not real_item_data: return
        
        real_item_data["default_width"] = self.width_spin.value()
        
        points = []
        for row in range(self.snap_table.rowCount()):
            try:
                x_item = self.snap_table.item(row, 0)
                y_item = self.snap_table.item(row, 1)
                x = float(x_item.text()) if x_item else 0.0
                y = float(y_item.text()) if y_item else 0.0
                points.append({"x": x, "y": y})
            except ValueError:
                print(f"数値エラー。入力された文字列: x='{x_item.text() if x_item else ''}', y='{y_item.text() if y_item else ''}'")
                continue # 数値変換できない行は無視
        
        # データを更新
        real_item_data["snap_points"] = points
        
        # ツリーアイテムのデータも更新（重要：次回選択時に古いデータが読まれないように）
        selected_item.setData(0, Qt.UserRole, real_item_data)
        
        self._update_preview()
    
    def _add_empty_snap_row(self) -> None:
        """スナップ点テーブルに空行追加"""
        self.snap_table.blockSignals(True)
        row = self.snap_table.rowCount()
        self.snap_table.insertRow(row)
        self.snap_table.setItem(row, 0, QTableWidgetItem("0"))
        self.snap_table.setItem(row, 1, QTableWidgetItem("0"))
        self.snap_table.blockSignals(False)
        self._save_current_snap_points()
    
    def _delete_selected_snap_row(self) -> None:
        """選択されたスナップ点行を削除"""
        rows = sorted(set(index.row() for index in self.snap_table.selectedIndexes()), reverse=True)
        if not rows: return
        
        self.snap_table.blockSignals(True)
        for row in rows:
            self.snap_table.removeRow(row)
        self.snap_table.blockSignals(False)
        self._save_current_snap_points()
    
    def _clear_snap_points(self) -> None:
        """スナップ点テーブルをクリア"""
        self.snap_table.setRowCount(0)
        self._save_current_snap_points()
    
    def _generate_snap_points(self) -> None:
        """画像幅・分割数・オフセットからスナップ点生成"""
        current_image_path = self.image_path_edit.text()
        
        load_path = current_image_path
        if current_image_path and not os.path.exists(current_image_path):
            alt_path = os.path.join(DATA_DIR, current_image_path)
            if os.path.exists(alt_path):
                load_path = alt_path
        
        if not os.path.exists(load_path):
            QMessageBox.warning(self, "エラー", "画像が見つからないためサイズを計算できません。\n先に有効な画像を設定してください。")
            return
        
        pixmap = QPixmap(load_path)
        if pixmap.isNull(): return
        
        width = pixmap.width()
        # height = pixmap.height() # 今回は幅基準
        
        divisions = self.snap_div_spin.value()
        y_offset = self.snap_y_offset_spin.value()
        
        # 横幅を等分割する点を計算 (中心基準)
        # 例: 幅100, 2分割 -> -25, 25 (端から端までの区間を2つ作る中心点)
        step = width / divisions
        start_x = -width / 2 + (step / 2)
        
        self.snap_table.blockSignals(True)
        for i in range(divisions):
            x = start_x + (i * step)
            
            # 行を追加
            row = self.snap_table.rowCount()
            self.snap_table.insertRow(row)
            self.snap_table.setItem(row, 0, QTableWidgetItem(str(round(x, 1))))
            self.snap_table.setItem(row, 1, QTableWidgetItem(str(round(y_offset, 1))))
            
        self.snap_table.blockSignals(False)
        self._save_current_snap_points()
        
        QMessageBox.information(self, "完了", f"Y={y_offset} の位置に {divisions} 個のポイントを追加しました。")
    
    def _update_ui_state(self) -> None:
        """UIの有効/無効状態を更新"""
        # 電源設定
        self.power_spin.setEnabled(self.has_power_check.isChecked())
        
        # DMX設定
        has_dmx = self.has_dmx_check.isChecked()
        self.is_controller_check.setEnabled(has_dmx)
        
        # 卓（コントローラー）の場合はモードエディタを「非表示」ではなく「無効化(グレーアウト)」する（UI一貫性のため）
        # DMXが無効ならエディタも無効。DMX有効でも卓ならエディタは無効。
        is_mode_editable = (has_dmx and not self.is_controller_check.isChecked())
        self.mode_editor_widget.setEnabled(is_mode_editable)
        
        # 注: setVisible(True) にして常に表示領域を確保しておくことでレイアウト崩れを防ぐ
        self.mode_editor_widget.setVisible(True)
    
    def _on_connection_settings_changed(self) -> None:
        """接続設定変更時のUI更新"""
        self._update_ui_state()
        self._on_form_edited()
    
    def _load_modes_to_table(self, modes: list[dict]) -> None:
        """DMXモード一覧をテーブルに表示"""
        self.modes_table.blockSignals(True)
        self.modes_table.setSortingEnabled(False) # ロード中はソート無効
        self.modes_table.setRowCount(0)
        self.ch_detail_table.setRowCount(0) # 詳細もクリア
        self.ch_detail_label.setText("<b>2. チャンネル詳細設定 (モードを選択してください)</b>")
        
        for m in modes:
            row = self.modes_table.rowCount()
            self.modes_table.insertRow(row)
            
            # モード名
            self.modes_table.setItem(row, 0, QTableWidgetItem(str(m.get("name", "Default"))))
            
            # ch数 (ソート用にNumericTableWidgetItemを使用)
            ch_count = m.get("channels", 1)
            self.modes_table.setItem(row, 1, NumericTableWidgetItem(str(ch_count)))
            
            # 非表示データとして詳細定義を持たせる
            # definitions = ["Dimmer", "Red", "Green"...]
            definitions = m.get("definitions", [])
            # データの不整合を防ぐため、ch数に合わせてリスト長を調整
            if len(definitions) < ch_count:
                definitions.extend([""] * (ch_count - len(definitions)))
            elif len(definitions) > ch_count:
                definitions = definitions[:ch_count]
            
            self.modes_table.item(row, 0).setData(Qt.UserRole, definitions)
        
        self.modes_table.setSortingEnabled(True) # ソート再有効化
        self.modes_table.blockSignals(False)
    
    def _add_dmx_mode(self) -> None:
        """DMXモードを追加"""
        name = self.new_mode_name.text().strip()
        ch = self.new_mode_ch.value()
        if not name: name = f"{ch}ch Mode"
        
        self.modes_table.blockSignals(True)
        self.modes_table.setSortingEnabled(False)
        row = self.modes_table.rowCount()
        self.modes_table.insertRow(row)
        
        name_item = QTableWidgetItem(name)
        # 新規作成時の空定義
        default_defs = [f"Ch {i+1}" for i in range(ch)] 
        name_item.setData(Qt.UserRole, default_defs)
        
        self.modes_table.setItem(row, 0, name_item)
        self.modes_table.setItem(row, 1, NumericTableWidgetItem(str(ch)))
        
        self.modes_table.setSortingEnabled(True)
        self.modes_table.blockSignals(False)
        self.new_mode_name.clear()
        self._save_current_modes()
    
    def _delete_dmx_mode(self) -> None:
        """選択したDMXモードを削除"""
        rows = sorted(set(index.row() for index in self.modes_table.selectedIndexes()), reverse=True)
        if not rows: return
        self.modes_table.blockSignals(True)
        for row in rows:
            self.modes_table.removeRow(row)
        self.modes_table.blockSignals(False)
        self.ch_detail_table.setRowCount(0) # 詳細表示も消す
        self._save_current_modes()
    
    def _on_mode_table_changed(self, item: QTableWidgetItem) -> None:
        """DMXモードテーブル編集時のデータ反映"""
        # ch数が変わったら、保持しているdefinitionsリストの長さも調整が必要
        if item.column() == 1: # ch数列
            row = item.row()
            try:
                new_ch = int(item.text())
                name_item = self.modes_table.item(row, 0)
                defs = name_item.data(Qt.UserRole) or []
                
                # リスト長調整
                if len(defs) < new_ch:
                    defs.extend([f"Ch {i+1}" for i in range(len(defs), new_ch)])
                elif len(defs) > new_ch:
                    defs = defs[:new_ch]
                
                name_item.setData(Qt.UserRole, defs)
                
                # もし現在この行を選択中なら、詳細テーブルも更新
                if self.modes_table.currentRow() == row:
                    self._load_detail_table(defs)
                    
            except ValueError: pass
            
        self._save_current_modes()
    
    def _on_mode_selection_changed(self) -> None:
        """DMXモード選択変更時の詳細テーブル更新"""
        selected_rows = self.modes_table.selectedItems()
        if not selected_rows:
            self.ch_detail_table.setRowCount(0)
            self.ch_detail_label.setText("<b>2. チャンネル詳細設定</b>")
            return
        
        row = self.modes_table.currentRow()
        if row < 0: return
        
        name_item = self.modes_table.item(row, 0)
        mode_name = name_item.text()
        definitions = name_item.data(Qt.UserRole) or []
        
        self.ch_detail_label.setText(f"<b>2. チャンネル詳細設定: {mode_name}</b>")
        self._load_detail_table(definitions)
    
    def _load_detail_table(self, definitions: list[str]) -> None:
        """詳細テーブルに定義データを展開"""
        self.ch_detail_table.blockSignals(True)
        self.ch_detail_table.setRowCount(len(definitions))
        for i, func_name in enumerate(definitions):
            # Ch番号 (編集不可)
            item_ch = QTableWidgetItem(str(i + 1))
            item_ch.setFlags(item_ch.flags() ^ Qt.ItemIsEditable)
            self.ch_detail_table.setItem(i, 0, item_ch)
            
            # 機能名 (編集可)
            item_def = QTableWidgetItem(str(func_name))
            self.ch_detail_table.setItem(i, 1, item_def)
        self.ch_detail_table.blockSignals(False)
    
    def _on_ch_detail_changed(self, item: QTableWidgetItem) -> None:
        """詳細テーブル編集時のデータ反映"""
        current_mode_row = self.modes_table.currentRow()
        if current_mode_row < 0: return
        
        # 現在のテーブル内容をリスト化
        new_defs = []
        for r in range(self.ch_detail_table.rowCount()):
            def_item = self.ch_detail_table.item(r, 1)
            new_defs.append(def_item.text() if def_item else "")
        
        # モード一覧の該当アイテムに保存
        name_item = self.modes_table.item(current_mode_row, 0)
        name_item.setData(Qt.UserRole, new_defs)
        
        self._save_current_modes()
    
    def _save_current_modes(self) -> None:
        """DMXモード情報をデータに保存"""
        selected_item = self.tree_widget.currentItem()
        if not selected_item: return
        item_data_copy = selected_item.data(0, Qt.UserRole)
        target_id = item_data_copy["id"]
        real_item_data = self._find_data_by_id(self.tree_data, target_id)
        if not real_item_data: return
        
        modes = []
        # ビジュアル上の順序ではなく、内部行順序で走査が必要だが
        # QTableWidgetはソートするとVisualな順序が変わる。
        # データの保存としては、見た目順でも問題ない。
        
        for row in range(self.modes_table.rowCount()):
            name_item = self.modes_table.item(row, 0)
            ch_item = self.modes_table.item(row, 1)
            if name_item and ch_item:
                try:
                    modes.append({
                        "name": name_item.text(),
                        "channels": int(ch_item.text()),
                        "definitions": name_item.data(Qt.UserRole) # 詳細データも保存
                    })
                except ValueError: pass
        
        real_item_data["dmx_modes"] = modes
        selected_item.setData(0, Qt.UserRole, real_item_data)
    
    def _on_form_edited(self) -> None:
        """フォーム編集時のデータ反映"""
        selected_item = self.tree_widget.currentItem()
        if not selected_item: return
        item_data_copy = selected_item.data(0, Qt.UserRole)
        target_id = item_data_copy["id"]
        real_item_data = self._find_data_by_id(self.tree_data, target_id)
        if not real_item_data: return
        
        if real_item_data["type"] == "folder":
            real_item_data["name"] = self.folder_name_edit.text()
            selected_item.setText(0, real_item_data["name"])
        elif real_item_data["type"] == "equipment":
            real_item_data["name"] = self.equip_name_edit.text()
            real_item_data["manufacturer"] = self.manufacturer_edit.text()
            real_item_data["image_path"] = self.image_path_edit.text()
            real_item_data["default_width"] = self.width_spin.value()
            real_item_data["has_power"] = self.has_power_check.isChecked()
            real_item_data["power_consumption"] = self.power_spin.value()
            real_item_data["has_dmx"] = self.has_dmx_check.isChecked()
            real_item_data["is_controller"] = self.is_controller_check.isChecked()
            real_item_data["can_be_wired"] = real_item_data["has_power"] or real_item_data["has_dmx"]
            selected_item.setText(0, real_item_data["name"])
        selected_item.setData(0, Qt.UserRole, real_item_data)
    
    def _browse_for_image(self) -> None:
        """画像ファイル選択・コピー処理"""
        start_dir = os.getcwd()
        file_path, _ = QFileDialog.getOpenFileName(self, "画像を選択", start_dir, "画像ファイル (*.png *.jpg)")
        
        if not file_path:
            return
        
        # パスの正規化
        abs_file_path = os.path.abspath(file_path)
        images_dir = IMAGES_DIR
        abs_images_dir = os.path.abspath(images_dir)
        
        # imagesフォルダ作成
        if not os.path.exists(images_dir):
            os.makedirs(images_dir)
        
        is_inside_images = abs_file_path.startswith(abs_images_dir)
        
        if is_inside_images:
            # imagesフォルダ内の場合、相対パスとして保存
            try:
                # dataフォルダを基準とした相対パスにするのが扱いやすい
                relative_path = os.path.relpath(file_path, DATA_DIR).replace("\\", "/")
                self.image_path_edit.setText(relative_path)
            except ValueError:
                self.image_path_edit.setText(file_path)
        else:
            # ■ ケース2: images 外にある場合 -> コピーの確認
            reply = QMessageBox.question(
                self,
                "画像の取り込み",
                "選択された画像は 'images' フォルダの外にあります。\n"
                "プロジェクトフォルダ内（images）にコピーしますか？\n\n"
                "「はい」: 画像をコピーして、そのパスを使用します（推奨）。\n"
                "「いいえ」: 元の場所のパスをそのまま使用します。",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                file_name = os.path.basename(file_path)
                dest_path = os.path.join(images_dir, file_name)
                
                # 画像コピー中は進捗ダイアログを表示し、操作をブロックする
                progress = QProgressDialog("画像をコピーしています...", None, 0, 0, self)
                progress.setWindowTitle("処理中")
                progress.setWindowModality(Qt.WindowModal) # ウィンドウ操作をブロック
                progress.setCancelButton(None) # キャンセル不可にする
                progress.show()
                QApplication.processEvents() # ダイアログを即座に描画
                
                try:
                    shutil.copy2(file_path, dest_path)
                    
                    # 処理完了後にダイアログを閉じる
                    progress.close()
                    
                    # コピー完了後にユーザーへ通知
                    QMessageBox.information(self, "完了", "画像のコピーが完了しました。")
                    
                    # パスの設定
                    try:
                        relative_path = os.path.relpath(dest_path, DATA_DIR).replace("\\", "/")
                        self.image_path_edit.setText(relative_path)
                    except ValueError:
                        self.image_path_edit.setText(dest_path)
                
                except Exception as e:
                    progress.close()
                    QMessageBox.critical(self, "エラー", f"画像のコピーに失敗しました:\n{e}")
            else:
                # 「いいえ」が選ばれた場合
                try:
                    relative_path = os.path.relpath(file_path, start_dir).replace("\\", "/")
                    self.image_path_edit.setText(relative_path)
                except ValueError:
                    # ドライブが異なる等で相対パスにできない場合は通知
                    QMessageBox.information(
                        self, 
                        "通知", 
                        "選択されたファイルは別のドライブにあるため、相対パスに変換できませんでした。\n"
                        "絶対パスとして設定します。"
                    )
                    self.image_path_edit.setText(file_path)
    
    def _add_item(self) -> None:
        """フォルダ・機材の追加"""
        from PySide6.QtWidgets import QMenu, QTreeWidgetItem
        menu = QMenu(self)
        add_folder_action = menu.addAction("フォルダを追加")
        add_equipment_action = menu.addAction("機材を追加")
        action = menu.exec(self.add_button.mapToGlobal(self.add_button.rect().bottomLeft()))
        if not action: return
        selected_item = self.tree_widget.currentItem()
        target_parent_data = None
        parent_widget = self.tree_widget
        if not selected_item:
            target_parent_data = {"children": self.tree_data}
        else:
            selected_data_copy = selected_item.data(0, Qt.UserRole)
            if selected_data_copy["type"] == "folder":
                target_parent_data = self._find_data_by_id(self.tree_data, selected_data_copy["id"])
                parent_widget = selected_item
            elif selected_data_copy["type"] == "equipment":
                parent_tree_item = selected_item.parent()
                if parent_tree_item:
                    parent_id = parent_tree_item.data(0, Qt.UserRole)["id"]
                    target_parent_data = self._find_data_by_id(self.tree_data, parent_id)
                    parent_widget = parent_tree_item
                else:
                    target_parent_data = {"children": self.tree_data}
                    parent_widget = self.tree_widget
        if not target_parent_data or "children" not in target_parent_data:
            return
        if action == add_folder_action:
            new_data = {"id": f"folder_{uuid.uuid4().hex[:8]}", "type": "folder", "name": "新しいフォルダ", "children": []}
        else:
            new_data = { 
                "id": f"equip_{uuid.uuid4().hex[:8]}", 
                "type": "equipment", 
                "name": "新しい機材", 
                "manufacturer": "", 
                "image_path": "images/placeholder.png", 
                "default_width": 50,
                "snap_points": [],
                # 新しい属性
                "has_power": True,
                "power_consumption": 0,
                "has_dmx": True,
                "is_controller": False,
                "dmx_modes": [{"name": "Default", "channels": 1}], # デフォルトモード
                "can_be_wired": True 
            }
        target_parent_data["children"].append(new_data)
        tree_item = QTreeWidgetItem(parent_widget)
        tree_item.setText(0, new_data["name"])
        tree_item.setData(0, Qt.UserRole, new_data)
        if new_data["type"] == "folder":
            tree_item.setFlags(tree_item.flags() | Qt.ItemIsDropEnabled | Qt.ItemIsDragEnabled)
        elif new_data["type"] == "equipment":
            tree_item.setFlags((tree_item.flags() | Qt.ItemIsDragEnabled) & ~Qt.ItemIsDropEnabled)
        self.tree_widget.setCurrentItem(tree_item)
    
    def _delete_item(self) -> None:
        """選択した項目（フォルダ・機材）を削除"""
        selected_item = self.tree_widget.currentItem()
        if not selected_item: return
        item_data_copy = selected_item.data(0, Qt.UserRole)
        warning_message = f"「{item_data_copy['name']}」を本当に削除しますか？"
        if item_data_copy["type"] == "folder" and item_data_copy.get("children"):
            warning_message += "\n\n注意: このフォルダ内にあるすべての項目も一緒に削除されます。"
        reply = QMessageBox.question(self, "削除の確認", warning_message, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            parent_tree_item = selected_item.parent()
            if parent_tree_item:
                parent_id = parent_tree_item.data(0, Qt.UserRole)["id"]
                parent_real_data = self._find_data_by_id(self.tree_data, parent_id)
                if parent_real_data and "children" in parent_real_data:
                    target_id_to_delete = item_data_copy["id"]
                    parent_real_data["children"] = [item for item in parent_real_data["children"] if item.get("id") != target_id_to_delete]
                    parent_tree_item.removeChild(selected_item)
            else:
                target_id_to_delete = item_data_copy["id"]
                self.tree_data = [item for item in self.tree_data if item.get("id") != target_id_to_delete]
                idx = self.tree_widget.indexOfTopLevelItem(selected_item)
                if idx != -1:
                    self.tree_widget.takeTopLevelItem(idx)
            QTimer.singleShot(0, self._reset_selection_state)
    
    def _reset_selection_state(self) -> None:
        """選択状態をリセット"""
        self.tree_widget.clearSelection()
        self.tree_widget.setCurrentItem(None)
        self._on_selection_changed()
    
    def _find_data_by_id(self, data_list: list[dict], target_id: str) -> dict | None:
        """IDでデータを再帰検索"""
        for item in data_list:
            if item.get("id") == target_id: return item
            if item.get("type") == "folder" and "children" in item:
                found = self._find_data_by_id(item["children"], target_id)
                if found: return found
        return None
    
    def _find_tree_item_by_id(self, data_list: list[dict], target_id: str) -> dict | None:
        """IDでツリー項目を再帰検索（未使用）"""
        for item in data_list:
            if item.get("id") == target_id: return item
            if item.get("type") == "folder" and "children" in item:
                found = self._find_data_by_id(item["children"], target_id)
                if found: return found
        return None
    
    def get_updated_data(self) -> dict:
        """現在のツリー構造からデータを取得"""
        return self._reconstruct_data_from_tree()
    
    def _reconstruct_data_from_tree(self) -> dict:
        """ツリーウィジェットからデータリストを再構築"""
        new_data = []
        root = self.tree_widget.invisibleRootItem()
        for i in range(root.childCount()):
            child = root.child(i)
            new_data.append(self._serialize_tree_item(child))
        return new_data
    
    def _serialize_tree_item(self, item: QTreeWidgetItem) -> dict:
        """ツリー項目を辞書データに変換"""
        original_data = item.data(0, Qt.UserRole)
        # データのコピーを作成
        data = original_data.copy()
        
        if data["type"] == "folder":
            new_children = []
            for i in range(item.childCount()):
                child = item.child(i)
                new_children.append(self._serialize_tree_item(child))
            data["children"] = new_children
        else:
            # 機材の場合、誤ってchildrenが含まれないように削除
            if "children" in data:
                del data["children"]
        return data
    
    def _update_preview(self) -> None:
        """プレビューウィジェットを更新"""
        current_image_path = self.image_path_edit.text()
        
        # テーブルから座標リストを作成
        points = []
        for row in range(self.snap_table.rowCount()):
            try:
                x_item = self.snap_table.item(row, 0)
                y_item = self.snap_table.item(row, 1)
                x = float(x_item.text()) if x_item else 0.0
                y = float(y_item.text()) if y_item else 0.0
                points.append({"x": x, "y": y})
            except ValueError:
                continue
        
        # プレビューウィジェットにデータを渡して再描画
        self.preview_widget.set_data(current_image_path, points)

class MainWindow(QMainWindow):
    """アプリケーションのメインウィンドウ"""
    def __init__(self) -> None:
        """初期化処理"""
        super().__init__()
        self.setWindowTitle("空のウィンドウ")
        self.resize(800, 600)
        
        self.undoStack = QUndoStack(self)
        self._load_equipment_data()
        self.is_modified = False
        self.undoStack.cleanChanged.connect(self.set_modified)
        self.current_file_path = None
        self.setWindowTitle("無題 - DMX Layout Tool")
        
        # --- 左ドック ---
        self.left_dock = QDockWidget("機材ライブラリ", self)
        self.main_tree_widget = QTreeWidget()
        self.main_tree_widget.setHeaderHidden(True)
        self.main_tree_widget.setDragEnabled(True)
        self.left_dock.setWidget(self.main_tree_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.left_dock)
        self.update_main_tree()
        
        # --- 右ドック (プロパティ) ---
        self.right_dock = QDockWidget("プロパティ", self)
        prop_widget = QWidget()
        prop_layout = QFormLayout()
        prop_widget.setLayout(prop_layout)
        
        # 共通項目
        self.name_edit = QLineEdit(); self.name_edit.setReadOnly(True)
        self.pos_x_edit = QLineEdit()
        self.pos_y_edit = QLineEdit()
        self.angle_edit = QLineEdit()
        
        self.pos_x_edit.editingFinished.connect(self.on_property_edited)
        self.pos_y_edit.editingFinished.connect(self.on_property_edited)
        self.angle_edit.editingFinished.connect(self.on_property_edited)
        
        # --- DMX用項目 ---
        self.lbl_dmx_mode = QLabel("DMXモード:")
        self.combo_dmx_mode = QComboBox()
        self.combo_dmx_mode.currentIndexChanged.connect(self.on_property_edited) 
        
        self.lbl_dmx_addr = QLabel("DMXアドレス:")
        dmx_addr_layout = QHBoxLayout()
        self.spin_universe = QSpinBox(); self.spin_universe.setRange(1, 100); self.spin_universe.setPrefix("U: ")
        self.spin_address = QSpinBox(); self.spin_address.setRange(1, 512); self.spin_address.setPrefix("Addr: ")
        dmx_addr_layout.addWidget(self.spin_universe)
        dmx_addr_layout.addWidget(self.spin_address)
        
        self.spin_universe.valueChanged.connect(self.on_property_edited)
        self.spin_address.valueChanged.connect(self.on_property_edited)
        
        # --- コンセント用項目 ---
        self.lbl_circuit = QLabel("回路番号/名:")
        self.circuit_group_edit = QLineEdit(); self.circuit_group_edit.setReadOnly(True)
        self.lbl_tap_lim = QLabel("タップ容量:")
        self.tap_limit_edit = QSpinBox(); self.tap_limit_edit.setRange(0, 5000); self.tap_limit_edit.setSuffix(" W"); self.tap_limit_edit.setReadOnly(True)
        self.lbl_circ_lim = QLabel("回路容量:")
        self.circuit_limit_edit = QSpinBox(); self.circuit_limit_edit.setRange(0, 20000); self.circuit_limit_edit.setSuffix(" W"); self.circuit_limit_edit.setReadOnly(True)
        
        # 表示切替
        self.text_visible_check = QCheckBox("灯体名を表示")
        self.text_visible_check.toggled.connect(self.on_visibility_changed)
        self.channel_visible_check = QCheckBox("チャンネルを表示")
        self.channel_visible_check.toggled.connect(self.on_visibility_changed)
        
        self.btn_text_color = QPushButton("文字色を変更...")
        self.btn_text_color.clicked.connect(self.change_text_color)
        
        # レイアウト配置
        prop_layout.addRow("名前:", self.name_edit)
        prop_layout.addRow("X座標:", self.pos_x_edit)
        prop_layout.addRow("Y座標:", self.pos_y_edit)
        prop_layout.addRow("角度:", self.angle_edit)
        
        # DMX項目 (デフォルトは隠しておく)
        prop_layout.addRow(self.lbl_dmx_mode, self.combo_dmx_mode)
        prop_layout.addRow(self.lbl_dmx_addr, dmx_addr_layout)
        # コンセント項目
        prop_layout.addRow(self.lbl_circuit, self.circuit_group_edit)
        prop_layout.addRow(self.lbl_tap_lim, self.tap_limit_edit)
        prop_layout.addRow(self.lbl_circ_lim, self.circuit_limit_edit)
        
        prop_layout.addRow(self.text_visible_check)
        prop_layout.addRow(self.channel_visible_check)
        prop_layout.addRow(self.btn_text_color)
        
        self.right_dock.setWidget(prop_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.right_dock)
        
        # 切り替え項目
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(-5000, -5000, 10000, 10000)
        self.scene.setBackgroundBrush(QColor(150, 150, 150))
        self.view = CustomGraphicsView(self.scene)
        self.view.mainWindow = self
        self.setCentralWidget(self.view)
        self.view.scene().changed.connect(self.update_properties_panel)
        
        # メニューバー設定
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("ファイル")
        new_action = file_menu.addAction("新規作成"); new_action.setShortcut("Ctrl+N"); new_action.triggered.connect(self.new_file)
        file_menu.addSeparator()
        save_action = file_menu.addAction("上書き保存"); save_action.setShortcut("Ctrl+S"); save_action.triggered.connect(self.save_file)
        save_as_action = file_menu.addAction("名前を付けて保存..."); save_as_action.setShortcut("Ctrl+Shift+S"); save_as_action.triggered.connect(self.save_file_as)
        load_action = file_menu.addAction("読み込み"); load_action.setShortcut("Ctrl+O"); load_action.triggered.connect(self.load_file)
        file_menu.addSeparator()
        export_action = file_menu.addAction("エクスポート (PDF/PNG)...")
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self.open_export_dialog)
        
        edit_menu = menu_bar.addMenu("編集")
        undo_action = self.undoStack.createUndoAction(self, "元に戻す"); undo_action.setShortcut(QKeySequence.Undo); edit_menu.addAction(undo_action)
        redo_action = self.undoStack.createRedoAction(self, "やり直す"); redo_action.setShortcut(QKeySequence.Redo); edit_menu.addAction(redo_action)
        edit_menu.addSeparator()
        manage_equipment_action = edit_menu.addAction("機材を管理..."); manage_equipment_action.triggered.connect(self.open_equipment_manager)
        
        bg_menu = menu_bar.addMenu("背景")
        select_venue_action = bg_menu.addAction("背景色を変更..."); select_venue_action.triggered.connect(self.change_background_color)
        bg_menu.addSeparator()
        change_bg_action = bg_menu.addAction("背景図面を選択/管理..."); change_bg_action.triggered.connect(self.open_venue_manager)
        
        tool_menu = menu_bar.addMenu("ツール")
        
        patch_action = tool_menu.addAction("DMXパッチ管理...")
        patch_action.triggered.connect(self.open_patch_window)
        
        calc_power_action = tool_menu.addAction("電力計算レポート表示")
        calc_power_action.setShortcut("F5")
        calc_power_action.triggered.connect(self.show_power_report)
        
        arrange_menu = menu_bar.addMenu("配置")
        # 変数に保存して、後で有効/無効を切り替えられるようにする
        self.front_action = arrange_menu.addAction("最前面へ移動")
        self.front_action.setShortcut("Ctrl+Shift+]")
        self.front_action.triggered.connect(lambda: self.change_z_order("front"))
        self.front_action.setEnabled(False)        
        self.forward_action = arrange_menu.addAction("前面へ移動")
        self.forward_action.setShortcut("Ctrl+]")
        self.forward_action.triggered.connect(lambda: self.change_z_order("up"))
        self.forward_action.setEnabled(False)        
        self.backward_action = arrange_menu.addAction("背面へ移動")
        self.backward_action.setShortcut("Ctrl+[")
        self.backward_action.triggered.connect(lambda: self.change_z_order("down"))
        self.backward_action.setEnabled(False)        
        self.back_action = arrange_menu.addAction("最背面へ移動")
        self.back_action.setShortcut("Ctrl+Shift+[")
        self.back_action.triggered.connect(lambda: self.change_z_order("back"))
        self.back_action.setEnabled(False)
        
        self.current_venue_item = None
        self.scene.selectionChanged.connect(self.update_arrange_actions_state)
        
        # ツールバー
        self.mode_toolbar = QToolBar("モード選択"); self.addToolBar(self.mode_toolbar)
        self.mode_action_group = QActionGroup(self); self.mode_action_group.setExclusive(True)
        
        self.cursor_mode_action = QAction("配置", self); self.cursor_mode_action.setCheckable(True); self.cursor_mode_action.setChecked(True); self.cursor_mode_action.triggered.connect(lambda: self._set_mode("cursor"))
        self.mode_toolbar.addAction(self.cursor_mode_action); self.mode_action_group.addAction(self.cursor_mode_action)
        
        self.dmx_mode_action = QAction("DMX配線", self); self.dmx_mode_action.setCheckable(True); self.dmx_mode_action.triggered.connect(lambda: self._set_mode("wiring_dmx"))
        self.mode_toolbar.addAction(self.dmx_mode_action); self.mode_action_group.addAction(self.dmx_mode_action)
        
        self.power_mode_action = QAction("電源配線", self); self.power_mode_action.setCheckable(True); self.power_mode_action.triggered.connect(lambda: self._set_mode("wiring_power"))
        self.mode_toolbar.addAction(self.power_mode_action); self.mode_action_group.addAction(self.power_mode_action)
        
        self.wiring_delete_mode_action = QAction("配線削除", self); self.wiring_delete_mode_action.setCheckable(True); self.wiring_delete_mode_action.triggered.connect(lambda: self._set_mode("wiring_delete"))
        self.mode_toolbar.addAction(self.wiring_delete_mode_action); self.mode_action_group.addAction(self.wiring_delete_mode_action)
        
        self.mode_toolbar.addSeparator()
        self.show_dmx_check = QCheckBox("DMX表示"); self.show_dmx_check.setChecked(True); self.show_dmx_check.toggled.connect(self.update_wire_visibility); self.mode_toolbar.addWidget(self.show_dmx_check)
        self.show_power_check = QCheckBox("電源表示"); self.show_power_check.setChecked(True); self.show_power_check.toggled.connect(self.update_wire_visibility); self.mode_toolbar.addWidget(self.show_power_check)
        self.mode_toolbar.addSeparator()
        self.grid_check = QCheckBox("グリッド吸着"); self.grid_check.setChecked(False); self.grid_check.toggled.connect(self.toggle_grid); self.mode_toolbar.addWidget(self.grid_check)
        
        self._current_mode = "cursor"
    
    # is_modified を設定するスロット
    def set_modified(self, is_clean: bool) -> None:
        """undoStackの状態に応じてウィンドウタイトルを変更"""
        self.is_modified = not is_clean
        title = self.windowTitle()
        # 末尾に '*' がない かつ クリーンでない場合
        if not title.endswith('*') and not is_clean:
            self.setWindowTitle(title + '*')
        # 末尾に '*' がある かつ クリーンな場合
        elif title.endswith('*') and is_clean:
            self.setWindowTitle(title[:-1]) # 末尾の '*' を削除
    
    def save_file(self) -> bool:
        """現在のファイルにレイアウトを保存"""
        if self.current_file_path is None:
            return self.save_file_as()
        else:
            return self._perform_save(self.current_file_path)
    
    def save_file_as(self) -> bool:
        """ファイル名を指定してレイアウトを保存"""
        file_path, _ = QFileDialog.getSaveFileName(self, "レイアウトを保存", "", "レイアウトファイル (*.json)")
        if not file_path:
            return False
        return self._perform_save(file_path)
    
    # ファイル操作時に undoStack の状態をリセット
    def _perform_save(self, file_path: str) -> bool:
        """指定パスにレイアウトデータを保存"""
        equipment_items_data = []
        venue_walls_data = []
        venue_outlets_data = []
        lines_to_process = []
        
        # 背景色の保存
        bg_brush = self.view.scene().backgroundBrush()
        bg_color_name = bg_brush.color().name() if bg_brush.style() != Qt.NoBrush else "#FFFFFF"
        
        # シーン内のアイテムを分類して保存
        for item in self.view.scene().items():
            if isinstance(item, EquipmentItem):
                item_data = {
                    # 既存データ...
                    "instance_id": item.instance_id,
                    "type_id": item.type_id,
                    "x": item.pos().x(),
                    "y": item.pos().y(),
                    "angle": item.rotation(),
                    
                    # 重なり順と表示設定の保存
                    "z_value": item.zValue(),
                    "text_visible": item.text.isVisible(),
                    "channel_visible": item.channel_text.isVisible(),
                    
                    "text_color": item.getTextColor().name(),
                    "channel_text_color": item.getChannelTextColor().name(),
                    
                    # DMXデータ
                    "dmx_data": {
                        "universe": item.dmx_universe,
                        "address": item.dmx_address,
                        "mode_name": item.dmx_mode_name
                    }
                }
                equipment_items_data.append(item_data)
            
            elif isinstance(item, WiringItem):
                lines_to_process.append(item)
            
            elif isinstance(item, VenueItem):
                # 会場の壁データの保存
                # QPointFのリストを辞書のリストに変換
                walls = []
                for points in item.points_list:
                    wall_pts = [{"x": p.x(), "y": p.y()} for p in points]
                    walls.append(wall_pts)
                venue_walls_data.extend(walls)
            
            elif isinstance(item, OutletItem):
                # コンセントデータの保存
                # OutletItemは info に色や容量を持っているのでそれを保存
                # 位置は pos() から取得して info を更新しておく
                info = item.info.copy()
                info["x"] = item.pos().x()
                info["y"] = item.pos().y()
                info["text_color"] = item.getTextColor().name()
                
                outlet_data = {
                    "instance_id": item.instance_id,
                    "info": info
                }
                venue_outlets_data.append(outlet_data)
        
        # 配線データの作成
        wires_data = []
        for line in lines_to_process:
            wire_info = getattr(line, "wire_info", None)
            if not wire_info: continue
            start_id = wire_info.get("start_id")
            end_id = wire_info.get("end_id")
            if not start_id or not end_id: continue
            points_list = []
            if wire_info.get("points"):
                points_list = [{"x": p.x(), "y": p.y()} for p in wire_info["points"]]
            wire_data = {
                "start_item_id": wire_info["start_id"],
                "end_item_id": wire_info["end_id"],
                "points": points_list,
                "wire_category": wire_info.get("wire_category", "dmx")
            }
            wires_data.append(wire_data)
            
        # 統合データ
        layout_data = {
            "version": 1.1, # バージョン管理用
            "background_color": bg_color_name,
            "venue": {
                "walls": venue_walls_data,
                "outlets": venue_outlets_data
            },
            "equipment_items": equipment_items_data, 
            "wires": wires_data
        }
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(layout_data, f, indent=4, ensure_ascii=False)
            self.current_file_path = file_path
            # self.is_modified = False
            self.undoStack.setClean() # 保存したのでクリーン状態にする
            file_name = os.path.basename(file_path)
            self.setWindowTitle(f"{file_name} - DMX Layout Tool")
            print(f"レイアウトが {file_path} に保存されました。")
            return True
        except Exception as e:
            print(f"保存中にエラーが発生しました: {e}"); return False
    
    def check_unsaved_changes(self) -> bool:
        """未保存変更がある場合の確認ダイアログ"""
        if not self.is_modified:
            return True 
        file_name = os.path.basename(self.current_file_path) if self.current_file_path else "無題"
        message_box = QMessageBox(self)
        message_box.setWindowTitle("変更の保存")
        message_box.setText(f"'{file_name}' への変更を保存しますか？")
        message_box.setInformativeText("未保存の変更は失われます。")
        message_box.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
        message_box.setDefaultButton(QMessageBox.Save)
        save_btn = message_box.button(QMessageBox.Save); save_btn.setText("保存する(&S)")
        discard_btn = message_box.button(QMessageBox.Discard); discard_btn.setText("保存しない(&N)")
        cancel_btn = message_box.button(QMessageBox.Cancel); cancel_btn.setText("キャンセル")
        ret = message_box.exec()
        if ret == QMessageBox.Save:
            return self.save_file()
        elif ret == QMessageBox.Discard:
            return True
        elif ret == QMessageBox.Cancel:
            return False
        return False
    
    def load_file(self) -> None:
        """レイアウトファイルを読み込む"""
        if not self.check_unsaved_changes(): return
        file_path, _ = QFileDialog.getOpenFileName(self, "レイアウトを読み込み", "", "レイアウトファイル (*.json)")
        if not file_path: return
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                layout_data = json.load(f)
        except Exception as e:
            print(f"読み込み中にエラーが発生しました: {e}"); return
        
        self.view._cancel_wiring()
        self.view.scene().clear()
        created_items_map = {}
        
        if not isinstance(layout_data, dict):
            return
        
        # 1. 背景色の復元
        bg_color = layout_data.get("background_color", "#969696") # デフォルトはグレー
        self.view.scene().setBackgroundBrush(QColor(bg_color))
        
        # 2. 会場 (壁) の復元
        venue_data = layout_data.get("venue", {})
        walls_data = venue_data.get("walls", [])
        
        # 互換性: 古い形式のファイルには venue キーがない場合がある
        if walls_data:
            points_list = []
            for wall_pts in walls_data:
                pts = [QPointF(p["x"], p["y"]) for p in wall_pts]
                points_list.append(pts)
            if points_list:
                self.current_venue_item = VenueItem(points_list)
                self.view.scene().addItem(self.current_venue_item)
        
        # 3. コンセントの復元 (IDをマップに登録することが重要)
        outlets_data = venue_data.get("outlets", [])
        for out_d in outlets_data:
            info = out_d.get("info", {})
            uid = out_d.get("instance_id")
            
            # 位置情報は info に入っているはずだが、念のため外側にあれば優先
            if "x" not in info and "x" in out_d: info["x"] = out_d["x"]
            if "y" not in info and "y" in out_d: info["y"] = out_d["y"]
            
            outlet_item = OutletItem(info, uid=uid)
            if "text_color" in info:
                outlet_item.setTextColor(QColor(info["text_color"]))
            if "channel_text_color" in item_data:
                item.setChannelTextColor(QColor(item_data["channel_text_color"]))
            self.view.scene().addItem(outlet_item)
            
            # 配線のためにマップに登録
            if outlet_item.instance_id:
                created_items_map[outlet_item.instance_id] = outlet_item
        
        # 4. 機材の復元
        equipment_items_data = layout_data.get("equipment_items", [])
        for item_data in equipment_items_data:
            type_id = item_data.get("type_id")
            type_info = self._find_data_by_id(self.equipment_data, type_id)
            if not type_info: continue
            
            # DMXデータの読み込み
            dmx_data = item_data.get("dmx_data", None)
            if dmx_data is None and "channel" in item_data:
                old_ch = item_data["channel"]
                if old_ch is not None:
                    dmx_data = {"universe": 1, "address": int(old_ch), "mode_name": ""}
            
            # Item 生成
            item = EquipmentItem(type_info, dmx_data=dmx_data)
            
            if "instance_id" in item_data:
                item.instance_id = item_data["instance_id"]
            
            item.setPos(item_data.get("x", 0), item_data.get("y", 0))
            item.setRotation(item_data.get("angle", 0))
            
            # Z値と表示設定の復元
            if "z_value" in item_data:
                item.setZValue(item_data["z_value"])
            if "text_visible" in item_data:
                item.setTextVisible(item_data["text_visible"])
            if "channel_visible" in item_data:
                item.setChannelVisible(item_data["channel_visible"])
            
            # 文字色の復元
            if "text_color" in item_data:
                item.setTextColor(QColor(item_data["text_color"]))
            
            self.view.scene().addItem(item)
            created_items_map[item.instance_id] = item
            
        # 5. 配線の復元
        wires_data = layout_data.get("wires", [])
        for wire_data in wires_data:
            start_id = wire_data.get("start_item_id")
            end_id = wire_data.get("end_item_id")
            
            # 機材だけでなくコンセントもマップに入っているので検索可能
            start_item = created_items_map.get(start_id)
            end_item = created_items_map.get(end_id)
            
            if start_item and end_item:
                middle_points_data = wire_data.get("points", [])
                middle_points = [QPointF(p['x'], p['y']) for p in middle_points_data]
                
                wire_category = wire_data.get("wire_category", "dmx")
                
                wire = WiringItem(start_item, end_item, middle_points, wire_type=wire_category)
                self.view.scene().addItem(wire)
                
        self.current_file_path = file_path
        self.undoStack.clear()
        self.undoStack.setClean()
        file_name = file_path.split('/')[-1]
        self.setWindowTitle(f"{file_name} - DMX Layout Tool")
    
    def new_file(self) -> None:
        """新規レイアウトを作成"""
        if not self.check_unsaved_changes():
            return
        self.view._cancel_wiring()
        self.view.scene().clear()
        self.current_file_path = None
        # self.is_modified = False
        self.undoStack.clear() # 新規作成時はUndoスタックをクリア
        self.undoStack.setClean() # 新規作成時はUndoスタックをクリーン状態に
        self.setWindowTitle("無題 - DMX Layout Tool")
    
    def change_background_color(self) -> None:
        """背景色を変更する"""
        # 現在の色を取得（設定されていなければ白）
        current_brush = self.scene.backgroundBrush()
        current_color = current_brush.color() if current_brush.style() != Qt.NoBrush else QColor("white")
        
        # カラーダイアログを開く
        color = QColorDialog.getColor(current_color, self, "背景色を選択")
        
        if color.isValid():
            self.scene.setBackgroundBrush(color)
            # CustomGraphicsView.drawBackground は super().drawBackground() を呼んでいるため、
            # シーンの背景ブラシを設定するだけで自動的に反映されます。
    
    def closeEvent(self, event: QCloseEvent) -> None:
        """ウィンドウを閉じる際のイベント処理"""
        if self.check_unsaved_changes():
            event.accept()
        else:
            event.ignore()
    
    def update_properties_panel(self) -> None:
        """選択アイテムに応じてプロパティパネルを更新"""
        # シグナルブロック
        self.text_visible_check.blockSignals(True)
        self.channel_visible_check.blockSignals(True)
        self.combo_dmx_mode.blockSignals(True)
        self.spin_universe.blockSignals(True)
        self.spin_address.blockSignals(True)
        
        selected_items = self.view.scene().selectedItems()
        
        enable_btn = False
        for item in selected_items:
            if isinstance(item, EquipmentItem):
                # 機材の場合、「名前」か「チャンネル」が選択状態なら有効
                if item.selection_mode in ['name_text', 'channel_text']:
                    enable_btn = True
                    break
            elif isinstance(item, OutletItem):
                # コンセントなら常に有効
                enable_btn = True
                break
        
        self.btn_text_color.setEnabled(enable_btn)
        
        # 一旦DMX/Outlet関連ウィジェットを非表示に
        self._set_dmx_widgets_visible(False)
        self._set_outlet_widgets_visible(False)
        
        if len(selected_items) == 1:
            item = selected_items[0]
            if isinstance(item, EquipmentItem):
                # 共通項目のセット
                self.name_edit.setText(item.name)
                rect = item.image.boundingRect()
                offset_x = rect.width() / 2
                offset_y = rect.height() / 2
                center_x = item.pos().x() + offset_x
                center_y = item.pos().y() + offset_y
                self.pos_x_edit.setText(f"{center_x:.2f}")
                self.pos_y_edit.setText(f"{center_y:.2f}")
                self.angle_edit.setText(f"{item.rotation() % 360:.2f}")
                self.text_visible_check.setChecked(item.text.isVisible())
                self.channel_visible_check.setChecked(item.channel_text.isVisible())
                
                # --- DMX機材の場合 ---
                if item.has_dmx:
                    self._set_dmx_widgets_visible(True)
                    
                    # コンボボックスの更新
                    item_type_data = item.data(0)
                    modes = item_type_data.get("dmx_modes", [])
                    
                    self.combo_dmx_mode.clear()
                    current_index = 0
                    for i, m in enumerate(modes):
                        self.combo_dmx_mode.addItem(m["name"])
                        if m["name"] == item.dmx_mode_name:
                            current_index = i
                    
                    if self.combo_dmx_mode.count() > 0:
                        self.combo_dmx_mode.setCurrentIndex(current_index)
                        self.combo_dmx_mode.setEnabled(True)
                    else:
                        self.combo_dmx_mode.addItem("No Modes")
                        self.combo_dmx_mode.setEnabled(False)
                        
                    self.spin_universe.setValue(item.dmx_universe)
                    self.spin_address.setValue(item.dmx_address)
            
            elif isinstance(item, OutletItem):
                # コンセントの処理（既存）
                self.name_edit.setText("コンセント")
                self.pos_x_edit.setText(f"{item.pos().x():.2f}")
                self.pos_y_edit.setText(f"{item.pos().y():.2f}")
                self.angle_edit.clear()
                self._set_outlet_widgets_visible(True)
                self.circuit_group_edit.setText(item.info.get("circuit_id", ""))
                self.tap_limit_edit.setValue(int(item.info.get("tap_capacity", 0)))
                self.circuit_limit_edit.setValue(int(item.info.get("circuit_capacity", 0)))
                self.btn_text_color.setEnabled(True)
        
        else:
            # 未選択または複数選択時
            self.name_edit.clear()
            self.pos_x_edit.clear()
            self.pos_y_edit.clear()
            self.angle_edit.clear()
        
        # シグナルブロック解除
        self.text_visible_check.blockSignals(False)
        self.channel_visible_check.blockSignals(False)
        self.combo_dmx_mode.blockSignals(False)
        self.spin_universe.blockSignals(False)
        self.spin_address.blockSignals(False)
    
    def _set_dmx_widgets_visible(self, visible: bool) -> None:
        """DMX関連ウィジェットの表示切替"""
        self.lbl_dmx_mode.setVisible(visible)
        self.combo_dmx_mode.setVisible(visible)
        self.lbl_dmx_addr.setVisible(visible)
        self.spin_universe.setVisible(visible)
        self.spin_address.setVisible(visible)
    
    def _set_outlet_widgets_visible(self, visible: bool) -> None:
        """コンセント関連ウィジェットの表示切替"""
        self.lbl_circuit.setVisible(visible)
        self.circuit_group_edit.setVisible(visible)
        self.lbl_tap_lim.setVisible(visible)
        self.tap_limit_edit.setVisible(visible)
        self.lbl_circ_lim.setVisible(visible)
        self.circuit_limit_edit.setVisible(visible)
    
    def on_property_edited(self) -> None:
        """プロパティ編集時の処理"""
        sender = self.sender()
        selected_items = [item for item in self.view.scene().selectedItems() if isinstance(item, EquipmentItem)]
        if not selected_items: return
        
        prop_name = None
        new_value_str = ""
        old_values = []
        has_changed = False
        
        try:
            # --- 既存の座標・角度処理 ---
            if sender is self.pos_x_edit:
                prop_name = "pos_x"
                new_value_str = self.pos_x_edit.text()
                val_float = float(new_value_str)
                old_values = [item.pos().x() + item.image.boundingRect().width() / 2 for item in selected_items]
                if not old_values or abs(old_values[0] - val_float) > 0.001:
                    has_changed = True
            
            elif sender is self.pos_y_edit:
                prop_name = "pos_y"
                new_value_str = self.pos_y_edit.text()
                val_float = float(new_value_str)
                old_values = [item.pos().y() + item.image.boundingRect().height() / 2 for item in selected_items]
                if not old_values or abs(old_values[0] - val_float) > 0.001:
                    has_changed = True
            
            elif sender is self.angle_edit:
                prop_name = "angle"
                new_value_str = self.angle_edit.text()
                val_float = float(new_value_str)
                old_values = [item.rotation() for item in selected_items]
                if not old_values or abs(old_values[0] - val_float) > 0.001:
                    has_changed = True
            
            # --- DMX関連の処理 (ここを追加) ---
            # ※ Undoコマンド化は複雑なため、ここでは直接値を適用します
            elif sender is self.combo_dmx_mode:
                new_mode = self.combo_dmx_mode.currentText()
                for item in selected_items:
                    if item.has_dmx and item.dmx_mode_name != new_mode:
                        item.dmx_mode_name = new_mode
                        item.updateDmxText() # 表示更新
                        # (注) Undo実装時はここで Command を push することになります
            
            elif sender is self.spin_universe:
                new_univ = self.spin_universe.value()
                for item in selected_items:
                    if item.has_dmx and item.dmx_universe != new_univ:
                        item.dmx_universe = new_univ
                        item.updateDmxText()
            
            elif sender is self.spin_address:
                new_addr = self.spin_address.value()
                for item in selected_items:
                    if item.has_dmx and item.dmx_address != new_addr:
                        item.dmx_address = new_addr
                        item.updateDmxText()
        
        except ValueError:
            print("無効な値が入力されました。")
            self.update_properties_panel() # 入力を元に戻す
            return
        
        # 座標・角度の変更があった場合のみUndoコマンドを発行
        if prop_name and has_changed:
            cmd = CommandChangeProperty(self, selected_items, prop_name, old_values, new_value_str, f"{prop_name} 変更")
            self.undoStack.push(cmd)
    
    def on_visibility_changed(self) -> None:
        """表示切替チェックボックスの変更時処理"""
        sender = self.sender()
        is_visible = sender.isChecked()
        
        selected_items = [item for item in self.view.scene().selectedItems() if isinstance(item, EquipmentItem)]
        if not selected_items: return
        
        # プロパティ変更時はコマンドとしてまとめて管理（Undo/Redo対応のため）
        prop_name = None
        old_values = []
        
        if sender is self.text_visible_check:
            prop_name = "text_visible"
            old_values = [item.text.isVisible() for item in selected_items]
        elif sender is self.channel_visible_check:
            prop_name = "channel_visible"
            old_values = [item.channel_text.isVisible() for item in selected_items]
        
        if prop_name:
            if not old_values or old_values[0] != is_visible:
                cmd = CommandChangeProperty(self, selected_items, prop_name, old_values, is_visible, "表示切替")
                self.undoStack.push(cmd)
        
        # self.on_scene_changed() # <- 削除
    
    def open_equipment_manager(self) -> None:
        """機材管理ダイアログを開く"""
        dialog = EquipmentManagerDialog(self.equipment_data, self)
        result = dialog.exec()
        if result == QDialog.Accepted:
            self.equipment_data = dialog.get_updated_data()
            self.update_main_tree()
            self._save_equipment_data()
            self.update_all_scene_equipment_items()
            # self.on_scene_changed()
        else:
            print("機材ライブラリの変更はキャンセルされました。")
    
    def update_main_tree(self) -> None:
        """メインツリーウィジェットを更新"""
        self.main_tree_widget.clear()
        self._add_main_tree_items_recursively(self.main_tree_widget, self.equipment_data)
        self.main_tree_widget.expandAll()
    
    def _add_main_tree_items_recursively(self, parent_widget: QTreeWidgetItem, children_data: list[dict]) -> None:
        """メインツリー項目を再帰的に追加"""
        for item_data in children_data:
            tree_item = QTreeWidgetItem(parent_widget)
            tree_item.setText(0, item_data["name"])
            if item_data.get("type") == "folder":
                tree_item.setFlags(tree_item.flags() & ~Qt.ItemIsDragEnabled)
            elif item_data.get("type") == "equipment":
                tree_item.setData(0, Qt.UserRole, item_data)
            if item_data.get("type") == "folder" and "children" in item_data:
                self._add_main_tree_items_recursively(tree_item, item_data["children"])
    
    def _load_equipment_data(self) -> None:
        """機材データをファイルから読み込む"""
        self.equipment_file = LIBRARY_FILE
        try:
            with open(self.equipment_file, 'r', encoding='utf-8') as f:
                self.equipment_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.equipment_data = [
                { "id": "folder_1", "type": "folder", "name": "灯体", "children": [
                        { "id": "equip_1", "type": "equipment", "name": "パーライト", "manufacturer": "Generic", "image_path": "placeholder.png", "can_be_wired": True }
                    ]
                },
                { "id": "folder_2", "type": "folder", "name": "その他オブジェクト", "children": [] }
            ]
            self._save_equipment_data()
    
    def _save_equipment_data(self) -> None:
        """機材データをファイルに保存"""
        try:
            with open(self.equipment_file, 'w', encoding='utf-8') as f:
                json.dump(self.equipment_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"機材データの保存中にエラーが発生しました: {e}")
    
    def update_all_scene_equipment_items(self) -> None:
        """シーン上の全EquipmentItemを最新データで更新"""
        items_to_remove = []
        wires_to_remove = []
        all_wires = [item for item in self.view.scene().items() if isinstance(item, WiringItem)]
        items_to_process = [item for item in self.view.scene().items() if isinstance(item, EquipmentItem)]
        for item in items_to_process:
            updated_info = self._find_data_by_id(self.equipment_data, item.type_id)
            if updated_info:
                # 保持しているデータも最新に更新する（消費電力の変更などを反映させるため）
                item.setData(0, updated_info)
                item.name = updated_info["name"]
                item.can_be_wired = updated_info["can_be_wired"]
                
                img_path = updated_info["image_path"]
                if not os.path.exists(img_path):
                    alt_path = os.path.join(DATA_DIR, img_path)
                    if os.path.exists(alt_path):
                        img_path = alt_path
                    else:
                        name_only = os.path.basename(img_path)
                        alt_path_2 = os.path.join(IMAGES_DIR, name_only)
                        if os.path.exists(alt_path_2):
                            img_path = alt_path_2
                
                pixmap = QPixmap(img_path)
                item.image.setPixmap(pixmap.scaledToWidth(50, Qt.SmoothTransformation))
                item.image.setTransformOriginPoint(item.image.boundingRect().center())
                item.text.setText(item.name)
                text_rect = item.text.boundingRect()
                image_rect = item.image.boundingRect()
                item.text.setPos(
                    (image_rect.width() - text_rect.width()) / 2,
                    image_rect.height()
                )
                item.update()
            else:
                items_to_remove.append(item)
                for wire in all_wires:
                    if wire.start_item is item or wire.end_item is item:
                        if wire not in wires_to_remove:
                            wires_to_remove.append(wire)
        for wire in wires_to_remove:
            if wire.scene(): 
                self.view.scene().removeItem(wire)
        for item in items_to_remove:
            if item.scene(): 
                self.view.scene().removeItem(item)
    
    def _set_mode(self, mode: str) -> None:
        """操作モードの切り替え"""
        self._current_mode = mode
        print(f"モードが '{self._current_mode}' に切り替わりました。")
        
        # Viewにモードを通知
        self.view.set_interaction_mode(mode)
        
        # モードに応じた表示制御 (レイヤー機能)
        if mode == "wiring_dmx":
            # DMXモード: DMXのみ表示、電源は隠す、チェックボックス無効化
            self.show_dmx_check.setChecked(True)
            self.show_power_check.setChecked(False)
            self.show_dmx_check.setEnabled(False)
            self.show_power_check.setEnabled(False)
            
        elif mode == "wiring_power":
            # 電源モード: 電源のみ表示、DMXは隠す、チェックボックス無効化
            self.show_dmx_check.setChecked(False)
            self.show_power_check.setChecked(True)
            self.show_dmx_check.setEnabled(False)
            self.show_power_check.setEnabled(False)
            
        else:
            # 配置/削除モード: ユーザーのチェックボックス設定に従う
            self.show_dmx_check.setEnabled(True)
            self.show_power_check.setEnabled(True)
            # 現在のチェックボックスの状態を適用
            self.update_wire_visibility()
    
    def _find_data_by_id(self, data_list: list[dict], target_id: str) -> dict | None:
        """IDでデータを再帰検索"""
        for item in data_list:
            if item.get("id") == target_id:
                return item
            if item.get("type") == "folder" and "children" in item:
                found = self._find_data_by_id(item["children"], target_id)
                if found:
                    return found
        return None
    
    def toggle_grid(self, checked: bool) -> None:
        """グリッド表示のON/OFF切替"""
        self.view.show_grid = checked
        self.view.scene().update() # シーン全体を再描画して背景を更新
        print(f"グリッド表示: {'ON' if checked else 'OFF'}")
    
    def update_wire_visibility(self) -> None:
        """配線の表示/非表示を更新"""
        show_dmx = self.show_dmx_check.isChecked()
        show_power = self.show_power_check.isChecked()
        
        for item in self.view.scene().items():
            if isinstance(item, WiringItem):
                w_type = item.wire_type
                if w_type == "dmx":
                    item.setVisible(show_dmx)
                elif w_type == "power":
                    item.setVisible(show_power)
    
    def open_venue_manager(self) -> None:
        """会場管理ダイアログを開く"""
        dialog = VenueManagerDialog(self)
        if dialog.exec() == QDialog.Accepted:
            venue_data = dialog.selected_venue_data
            if venue_data:
                self.apply_venue(venue_data)
    
    def apply_venue(self, venue_data: dict) -> None:
        """選択した会場データをシーンに適用"""
        # 既存の会場アイテムがあれば削除
        if self.current_venue_item:
            self.scene.removeItem(self.current_venue_item)
            self.current_venue_item = None
        
        # 既存のコンセントアイテムも削除
        for item in self.scene.items():
            if isinstance(item, OutletItem):
                self.scene.removeItem(item)
            
        walls_data = venue_data.get("walls", [])
        points_list = []
        for wall_pts in walls_data:
            pts = [QPointF(p["x"], p["y"]) for p in wall_pts]
            points_list.append(pts)
            
        if points_list:
            self.current_venue_item = VenueItem(points_list)
            self.scene.addItem(self.current_venue_item)
            
        # コンセントの配置
        outlets_data = venue_data.get("outlets", [])
        count = 0
        for out_info in outlets_data:
            outlet = OutletItem(out_info)
            self.scene.addItem(outlet)
            count += 1
            
        print(f"会場 '{venue_data.get('name')}' を適用しました。(コンセント: {count}個)")
    
    def show_power_report(self) -> None:
        """電力計算レポートダイアログを表示"""
        report_data = self.calculate_power()
        dialog = PowerReportDialog(report_data, self)
        dialog.exec()
    
    def calculate_power(self) -> dict:
        """シーン内の電力使用状況を計算"""
        """
        戻り値の構造:
        {
            "circuits": {
                "A-1": {
                    "limit": 2000,
                    "total_watts": 1500,
                    "outlets": {
                        outlet_item_obj: { "limit": 1500, "total_watts": 500, "equipment": [item1, item2...] },
                        ...
                    }
                },
                ...
            },
            "unpowered": [itemA, itemB...]
        }
        """
        # 1. グラフ構築 (隣接リスト) - 電源線のみ
        adj = {}
        for item in self.scene.items():
            if isinstance(item, WiringItem) and item.wire_type == "power":
                u, v = item.start_item, item.end_item
                if u and v:
                    adj.setdefault(u, []).append(v)
                    adj.setdefault(v, []).append(u)
        
        # 2. 全ての機材とコンセントを取得
        all_equipment = [i for i in self.scene.items() if isinstance(i, EquipmentItem)]
        all_outlets = [i for i in self.scene.items() if isinstance(i, OutletItem)]
        
        # 配線済み機材の集合（未配線検出用）
        powered_equipment = set()
        
        # 結果格納用データ
        circuits_data = {} 
        
        # 3. 各コンセントから探索 (BFS)
        for outlet in all_outlets:
            circuit_id = outlet.info.get("circuit_id", "Unknown")
            circuit_cap = int(outlet.info.get("circuit_capacity", 2000))
            tap_cap = int(outlet.info.get("tap_capacity", 1500))
            
            # 回路データエントリの初期化
            if circuit_id not in circuits_data:
                circuits_data[circuit_id] = {
                    "limit": circuit_cap,
                    "total_watts": 0,
                    "outlets": {}
                }
            
            # このコンセント（タップ）のデータ初期化
            outlet_data = {
                "limit": tap_cap,
                "total_watts": 0,
                "equipment": []
            }
            
            # BFS探索
            visited = set()
            queue = [outlet]
            visited.add(outlet)
            
            while queue:
                current = queue.pop(0)
                
                # 隣接ノードへ
                neighbors = adj.get(current, [])
                for neighbor in neighbors:
                    if neighbor in visited:
                        continue
                    
                    # 他のコンセントにぶつかったら探索停止（通常はありえないが、電源同士がつながっている場合）
                    if isinstance(neighbor, OutletItem):
                        continue
                        
                    visited.add(neighbor)
                    
                    # 機材なら電力を加算
                    if isinstance(neighbor, EquipmentItem):
                        # 配線可能かつ電源を消費するものだけ計算
                        if neighbor.can_be_wired:
                            # 既に他の電源から供給されているかチェック（多重給電の警告は今回は省略し、先に探索した方を優先）
                            if neighbor not in powered_equipment:
                                watts = neighbor.data(0).get("power_consumption", 0)
                                outlet_data["total_watts"] += watts
                                outlet_data["equipment"].append(neighbor)
                                powered_equipment.add(neighbor)
                                
                                # さらにその先へ
                                queue.append(neighbor)
            
            # 集計結果を格納
            circuits_data[circuit_id]["outlets"][outlet] = outlet_data
            circuits_data[circuit_id]["total_watts"] += outlet_data["total_watts"]
        
        # 4. 未配線の機材を特定
        # (カテゴリーがdeviceで、かつ配線可能フラグがTrueのもの)
        unpowered_list = []
        for eq in all_equipment:
            # データの取得
            d = eq.data(0)
            # コンセント(outlet)ではなく、配線可能(can_be_wired)で、まだ給電リストにない場合
            # ※ EquipmentItemにはカテゴリー情報が直接ないので、can_be_wiredで判断するか、
            #    EquipmentManagerでoutletとして作ったものは弾く必要があるが、
            #    現状の設計ではEquipmentItemは全て「機材」扱いなのでOK
            if eq.can_be_wired and eq not in powered_equipment:
                # ワット数が0より大きいものだけを警告対象にする場合
                if d.get("power_consumption", 0) > 0:
                    unpowered_list.append(eq)
        
        return {
            "circuits": circuits_data,
            "unpowered": unpowered_list
        }
    
    def update_arrange_actions_state(self) -> None:
        """配置メニューの有効/無効を更新"""
        has_selection = len(self.view.scene().selectedItems()) > 0
        self.front_action.setEnabled(has_selection)
        self.forward_action.setEnabled(has_selection)
        self.backward_action.setEnabled(has_selection)
        self.back_action.setEnabled(has_selection)
    
    def change_z_order(self, mode: str) -> None:
        """選択アイテムの重なり順を変更"""
        selected_items = self.view.scene().selectedItems()
        if not selected_items:
            return
        
        # シーン内の現在のZ値の範囲を取得
        all_items = self.view.scene().items()
        all_z = [i.zValue() for i in all_items]
        max_z = max(all_z, default=0)
        min_z = min(all_z, default=0)
        
        # 複数のアイテムが変更される可能性があるため、マクロを使ってUndoを1回にまとめる
        self.undoStack.beginMacro("順序の変更")
        
        # 選択順ではなく、現在のZ順などでソートしてから処理するとより自然ですが、
        # ここではシンプルに選択アイテムすべてに適用します。
        for item in selected_items:
            old_z = item.zValue()
            new_z = old_z
            
            if mode == "front":
                # 現在の最大値より上にする
                # 複数ある場合、重ならないように1ずつずらす処理を入れるとより良いですが
                # ここではシンプルに「最前面」設定とします
                max_z += 1.0
                new_z = max_z
            elif mode == "back":
                min_z -= 1.0
                new_z = min_z
            elif mode == "up":
                new_z = old_z + 1.0
            elif mode == "down":
                new_z = old_z - 1.0
            
            # コマンドを発行
            cmd = CommandChangeZValue(item, old_z, new_z, f"順序変更: {mode}")
            self.undoStack.push(cmd)
        
        self.undoStack.endMacro()
    
    def open_patch_window(self) -> None:
        """DMXパッチ管理ウィンドウを開く"""
        # モーダルで開くか、モードレスで開くかはお好みですが、
        # 作業しながら見たい場合はモードレス(.show())が良いでしょう。
        # 今回はシンプルにダイアログ(.exec())として実装しますが、
        # 必要なら self.patch_window = PatchWindow(...) として保持しても良いです。
        
        dialog = PatchWindow(self.view.scene(), self)
        dialog.exec() # ダイアログを閉じるまでメイン操作をブロックする場合
        
        # 閉じた後に、プロパティパネルなどが古くなっている可能性があるので更新
        self.update_properties_panel()
    
    def open_export_dialog(self) -> None:
        """エクスポートダイアログを開く"""
        dialog = ExportDialog(self)
        if dialog.exec() == QDialog.Accepted:
            options = dialog.get_options()
            self.perform_export(options)
    
    def perform_export(self, options: dict) -> None:
        """エクスポート処理を実行"""
        # 保存先ファイルの選択
        ext = "pdf" if options["format"] == "pdf" else "png"
        file_filter = "PDF Files (*.pdf)" if options["format"] == "pdf" else "PNG Files (*.png)"
        file_path, _ = QFileDialog.getSaveFileName(self, "エクスポート先を指定", "", file_filter)
        
        if not file_path:
            return
        
        # PNGの場合、ファイル名から拡張子を除いておく
        base_path = file_path
        if options["format"] == "png" and file_path.lower().endswith(".png"):
            base_path = file_path[:-4]
        
        # 表出力が選択されている場合はプレビュー画面を表示（ユーザー確認用）
        dmx_html = ""
        pwr_html = ""
        
        if options["dmx_list"] or options["pwr_list"]:
            preview_dlg = TablePreviewDialog(self)
            
            # 必要なタブのみ有効化
            preview_dlg.tab_widget.setTabEnabled(0, options["dmx_list"])
            preview_dlg.tab_widget.setTabEnabled(1, options["pwr_list"])
            
            # データ投入
            if options["dmx_list"]:
                preview_dlg.populate_dmx_data(self.view.scene())
            if options["pwr_list"]:
                report = self.calculate_power()
                preview_dlg.populate_power_data(report)
                
            # デフォルトで表示するタブを選択
            if options["dmx_list"]: preview_dlg.tab_widget.setCurrentIndex(0)
            elif options["pwr_list"]: preview_dlg.tab_widget.setCurrentIndex(1)
            
            # ダイアログ実行
            if preview_dlg.exec() != QDialog.Accepted:
                return # キャンセルされたら終了
            
            # 編集後のHTMLを取得
            if options["dmx_list"]:
                dmx_html = preview_dlg.get_dmx_html()
            if options["pwr_list"]:
                pwr_html = preview_dlg.get_power_html()
        
        # --- 以下、既存のエクスポート処理 (引数に html を渡すように変更) ---
        
        original_dmx_vis = self.show_dmx_check.isChecked()
        original_pwr_vis = self.show_power_check.isChecked()
        original_grid = self.view.show_grid
        
        self.view.show_grid = False
        self.view.scene().update()
        
        try:
            if options["format"] == "pdf":
                # HTMLを渡す
                self._export_to_pdf(file_path, options, dmx_html, pwr_html)
            else:
                self._export_to_png(base_path, options, dmx_html, pwr_html)
                
            QMessageBox.information(self, "完了", "エクスポートが完了しました。")
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"エクスポート中にエラーが発生しました:\n{e}")
            import traceback
            traceback.print_exc()
            
        finally:
            self.show_dmx_check.setChecked(original_dmx_vis)
            self.show_power_check.setChecked(original_pwr_vis)
            self.view.show_grid = original_grid
            self.update_wire_visibility()
            self.view.scene().update()
    
    def _set_scene_visibility(self, show_dmx: bool, show_pwr: bool) -> None:
        """エクスポート用の一時的な配線表示切替"""
        for item in self.view.scene().items():
            if isinstance(item, WiringItem):
                if item.wire_type == "dmx":
                    item.setVisible(show_dmx)
                elif item.wire_type == "power":
                    item.setVisible(show_pwr)
    
    def _render_scene_to_painter(self, painter: QPainter, target_rect: QRectF) -> None:
        """シーンを指定Painter領域に描画"""
        scene = self.view.scene()
        source_rect = scene.itemsBoundingRect()
        # 余白を追加
        source_rect.adjust(-50, -50, 50, 50)
        scene.render(painter, target_rect, source_rect, Qt.KeepAspectRatio)
    
    def _export_to_pdf(self, file_path: str, options: dict, dmx_html: str = "", pwr_html: str = "") -> None:
        """PDF形式でエクスポート"""
        from PySide6.QtGui import QPdfWriter
        
        writer = QPdfWriter(file_path)
        writer.setPageSize(QPageSize(QPageSize.A4))
        writer.setPageOrientation(QPageLayout.Landscape)
        writer.setTitle("DMX Layout Export")
        
        painter = QPainter(writer)
        page_rect = writer.pageLayout().paintRectPixels(writer.resolution())
        
        is_first_page = True
        def new_page_if_needed():
            nonlocal is_first_page
            if not is_first_page:
                writer.newPage()
            is_first_page = False
        
        margin = page_rect.width() * 0.05
        draw_rect = QRectF(
            page_rect.x() + margin, 
            page_rect.y() + margin + 300, 
            page_rect.width() - margin*2, 
            page_rect.height() - margin*2 - 300
        )
        
        if options["layout"]:
            new_page_if_needed()
            self._set_scene_visibility(False, False)
            self._draw_title(painter, page_rect, "1. 機材配置図")
            self._render_scene_to_painter(painter, draw_rect)
        
        if options["dmx_map"]:
            new_page_if_needed()
            self._set_scene_visibility(True, False)
            self._draw_title(painter, page_rect, "2. DMX配線図")
            self._render_scene_to_painter(painter, draw_rect)
        
        if options["dmx_list"]:
            new_page_if_needed()
            self._draw_title(painter, page_rect, "3. DMXアドレス一覧表")
            # DMXアドレス一覧表の描画には渡されたHTMLを使用
            self._draw_html_table_scaled(painter, page_rect, dmx_html)
        
        if options["pwr_map"]:
            new_page_if_needed()
            self._set_scene_visibility(False, True)
            self._draw_title(painter, page_rect, "4. 電源配線図")
            self._render_scene_to_painter(painter, draw_rect)
        
        if options["pwr_list"]:
            new_page_if_needed()
            self._draw_title(painter, page_rect, "5. 電源回路一覧表")
            # 電源回路一覧表の描画には渡されたHTMLを使用
            self._draw_html_table_scaled(painter, page_rect, pwr_html)

        painter.end()
    
    def _export_to_png(self, base_path: str, options: dict, dmx_html: str = "", pwr_html: str = "") -> None:
        """PNG形式でエクスポート"""
        scene = self.view.scene()
        source_rect = scene.itemsBoundingRect().adjusted(-50, -50, 50, 50)
        
        if options["layout"]:
            self._set_scene_visibility(False, False)
            self._save_scene_image(f"{base_path}_01_layout.png", source_rect)
        
        if options["dmx_map"]:
            self._set_scene_visibility(True, False)
            self._save_scene_image(f"{base_path}_02_dmx_map.png", source_rect)
        
        if options["dmx_list"]:
            # DMXアドレス一覧表の画像出力には渡されたHTMLを使用
            self._save_html_image(f"{base_path}_03_dmx_list.png", dmx_html, "DMXアドレス一覧")
        
        if options["pwr_map"]:
            self._set_scene_visibility(False, True)
            self._save_scene_image(f"{base_path}_04_power_map.png", source_rect)
        
        if options["pwr_list"]:
            # 電源回路一覧表の画像出力には渡されたHTMLを使用
            self._save_html_image(f"{base_path}_05_power_list.png", pwr_html, "電源回路一覧")
    
    def _save_scene_image(self, path: str, source_rect: QRectF) -> None:
        """シーン画像を保存"""
        image = QImage(source_rect.size().toSize(), QImage.Format_ARGB32)
        image.fill(Qt.white) # 背景白
        painter = QPainter(image)
        self.view.scene().render(painter, QRectF(image.rect()), source_rect)
        painter.end()
        image.save(path)
    
    def _save_html_image(self, path: str, html: str, title: str) -> None:
        """HTML表を画像化して保存"""
        # HTMLを表として画像化するための簡易実装
        doc = QTextDocument()
        full_html = f"<h1>{title}</h1>{html}"
        doc.setHtml(full_html)
        doc.setTextWidth(800) # 幅固定
        
        height = doc.documentLayout().documentSize().height()
        image = QImage(QSize(800, int(height) + 20), QImage.Format_ARGB32)
        image.fill(Qt.white)
        
        painter = QPainter(image)
        doc.drawContents(painter)
        painter.end()
        image.save(path)
    
    def _draw_title(self, painter: QPainter, page_rect: QRectF, text: str) -> None:
        """タイトル描画（サイズ修正版）"""
        painter.save()
        
        font = painter.font()
        # 修正点: 計算値ではなく、固定のポイント数(24pt)を指定して適切なサイズにする
        # PDFにおける 24pt は、印刷物としてちょうどよい見出しサイズになります
        font.setPointSize(24) 
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(Qt.black)
        
        # タイトル描画領域の高さ設定
        # 次のコンテンツ（表や図）までの余白（ページ幅の5%）を利用
        title_height = page_rect.width() * 0.05
        
        # 描画矩形を作成
        title_rect = QRectF(page_rect.x(), page_rect.y(), page_rect.width(), title_height)
        
        # 左端に少しインデント（余白）を入れて描画
        indent = page_rect.width() * 0.02
        draw_rect = title_rect.adjusted(indent, 0, -indent, 0)
        
        painter.drawText(draw_rect, Qt.AlignLeft | Qt.AlignVCenter, text)
        painter.restore()
    
    def _draw_html_table_scaled(self, painter: QPainter, page_rect: QRectF, html: str) -> None:
        """HTMLテーブルをPDFの幅に合わせて拡大して描画する"""
        doc = QTextDocument()
        
        # HTMLセット (デフォルトCSSを適用して白背景・黒文字を強制)
        doc.setDefaultStyleSheet("body { color: black; background-color: white; }")
        doc.setHtml(html)
        
        # 描画先の幅（ページ幅から余白を引く）
        target_width = page_rect.width() * 0.9
        
        # ドキュメントの仮想幅を設定（これが折り返しの基準になる）
        # ※ここを小さくしすぎると文字が巨大になり、大きくしすぎると文字が小さくなる
        # PDFの解像度が高すぎるため、一旦「読みやすいピクセル幅（例: 1000px）」でレイアウトさせ、
        # それを painter.scale で引き伸ばして描画する戦略をとります。
        layout_width = 1000.0 
        doc.setTextWidth(layout_width)
        
        # スケール比率を計算 (ターゲット幅 / レイアウト幅)
        scale_factor = target_width / layout_width
        
        painter.save()
        # タイトルの下あたりに移動
        margin_x = page_rect.width() * 0.05
        margin_y = page_rect.width() * 0.05 # タイトル分の高さなどを考慮
        painter.translate(page_rect.x() + margin_x, page_rect.y() + margin_y)
        
        # 拡大！これで豆粒化を防ぐ
        painter.scale(scale_factor, scale_factor)
        
        # 描画
        doc.drawContents(painter)
        painter.restore()
    
    def _generate_dmx_list_html(self) -> str:
        """DMX機材一覧のHTMLテーブル（配色修正版）"""
        items = [i for i in self.view.scene().items() if isinstance(i, EquipmentItem) and i.has_dmx]
        items.sort(key=lambda x: (x.dmx_universe, x.dmx_address))
        
        # style属性で 色（color: black）と背景（background-color）を明示的に指定
        html = "<table border='1' cellspacing='0' cellpadding='4' width='100%' style='color: black; background-color: white; border-collapse: collapse; font-size: 10pt;'>"
        
        # ヘッダー: 濃いグレー背景(#555)に白文字(white)で見やすく
        html += "<tr style='background-color: #555; color: white;'><th>Univ</th><th>Addr</th><th>機材名</th><th>モード</th><th>Ch数</th></tr>"
        
        for i, item in enumerate(items):
            modes = item.data(0).get("dmx_modes", [])
            ch_count = 1
            for m in modes:
                if m["name"] == item.dmx_mode_name:
                    ch_count = m.get("channels", 1)
                    break
            
            # 縞々模様（偶数行に薄いグレー）をつけて読みやすくする
            bg_color = "#f9f9f9" if i % 2 == 0 else "#ffffff"
            html += f"<tr style='background-color: {bg_color}; color: black;'><td>{item.dmx_universe}</td><td>{item.dmx_address}</td><td>{item.name}</td><td>{item.dmx_mode_name}</td><td>{ch_count}</td></tr>"
        html += "</table>"
        return html
    
    def _generate_power_list_html(self) -> str:
        """電力計算結果のHTMLテーブル（配色修正版）"""
        report = self.calculate_power()
        
        html = "<table border='1' cellspacing='0' cellpadding='4' width='100%' style='color: black; background-color: white; border-collapse: collapse; font-size: 10pt;'>"
        # ヘッダー
        html += "<tr style='background-color: #555; color: white;'><th>回路</th><th>コンセント</th><th>接続機材</th><th>消費電力</th><th>状態</th></tr>"
        
        for circuit_id, c_data in report["circuits"].items():
            c_limit = c_data["limit"]
            c_total = c_data["total_watts"]
            c_status = "<span style='color:red; font-weight:bold;'>OVER</span>" if c_total > c_limit else "OK"
            
            # 回路ごとの区切り行（少し濃いめのグレー）
            html += f"<tr style='background-color: #ccc; color: black;'><td colspan='5'><b>回路: {circuit_id}</b> (合計: {c_total}W / 上限: {c_limit}W) - {c_status}</td></tr>"
            
            for outlet_obj, o_data in c_data["outlets"].items():
                o_name = outlet_obj.info.get('circuit_id', 'Unknown') if hasattr(outlet_obj, 'info') else "Outlet"
                o_limit = o_data["limit"]
                o_total = o_data["total_watts"]
                o_status = "<span style='color:red; font-weight:bold;'>OVER</span>" if o_total > o_limit else "OK"
                
                equip_names = [eq.name for eq in o_data["equipment"]]
                equip_str = ", ".join(equip_names) if equip_names else "(なし)"
                
                html += f"<tr style='background-color: white; color: black;'><td></td><td>{o_name}</td><td>{equip_str}</td><td>{o_total}W</td><td>{o_status}</td></tr>"
        
        if report["unpowered"]:
            html += "<tr style='background-color: #ffcccc; color: black;'><td colspan='5'><b>⚠️ 電源未接続の機材</b></td></tr>"
            for item in report["unpowered"]:
                w = item.data(0).get("power_consumption", 0)
                html += f"<tr style='background-color: white; color: black;'><td>-</td><td>-</td><td>{item.name}</td><td>{w}W</td><td>未接続</td></tr>"
                
        html += "</table>"
        return html
    
    def change_text_color(self) -> None:
        """選択状態に応じて変更する対象の色を決定して変更"""
        selected_items = self.view.scene().selectedItems()
        if not selected_items: return
        
        target_type = None
        current_color = QColor("black") # デフォルト
        
        # 優先順位を決めてターゲットモードを特定する
        # 1. 名前テキストが選択されている機材があるか
        # 2. チャンネルテキストが選択されている機材があるか
        # 3. コンセントがあるか
        
        for item in selected_items:
            if isinstance(item, EquipmentItem):
                if item.selection_mode == 'name_text':
                    target_type = 'name'
                    current_color = item.getTextColor()
                    break
                elif item.selection_mode == 'channel_text':
                    target_type = 'channel'
                    current_color = item.getChannelTextColor()
                    break
            elif isinstance(item, OutletItem):
                # コンセントは優先度低め（機材テキスト選択と一緒に選んだ場合、機材テキストを優先など）
                # ここではまだtarget_typeが決まってなければ設定
                if target_type is None:
                    target_type = 'outlet'
                    current_color = item.getTextColor()
        
        # ターゲットが決まれば実行
        if target_type:
            color = QColorDialog.getColor(current_color, self, "文字色を選択")
            if color.isValid():
                # CommandChangeTextColorは渡されたitems全てに対して、target_typeに合う処理を行う
                cmd = CommandChangeTextColor(selected_items, color, target_type)
                self.undoStack.push(cmd)

class EquipmentItem(QGraphicsObject):
    """機材アイテム（ドラッグ・配線・DMX情報などを持つ）"""
    def __init__(self, type_info: dict, channel: int | None = None, dmx_data: dict | None = None) -> None:
        """機材アイテムの初期化"""
        super().__init__()
        self.setData(0, type_info)  # 機材情報を格納
        self._is_highlighted = False  # 配線時のハイライト用
        # 基本プロパティ
        self.selection_mode = None  # 選択モード
        self.type_id = type_info["id"]
        self.instance_id = type_info.get("instance_id") or f"inst_{uuid.uuid4().hex[:8]}"
        self.name = type_info["name"]
        # 属性の読み込み（旧データ互換も考慮）
        self.has_power = type_info.get("has_power", type_info.get("can_be_wired", False))
        self.has_dmx = type_info.get("has_dmx", type_info.get("can_be_wired", False))
        self.can_be_wired = self.has_power or self.has_dmx
        
        # --- DMX情報の保持 ---
        if dmx_data:
            self.dmx_universe = dmx_data.get("universe", 1)
            self.dmx_address = dmx_data.get("address", 1)
            self.dmx_mode_name = dmx_data.get("mode_name", "")
        else:
            self.dmx_universe = 1
            self.dmx_address = 1
            # デフォルトモードを設定
            modes = type_info.get("dmx_modes", [])
            self.dmx_mode_name = modes[0]["name"] if modes else ""
        
        # 表示サイズ
        self.target_width = type_info.get("default_width", 50)
        self.snap_points_data = type_info.get("snap_points", [])
        
        # --- 画像パスの解決ロジック ---
        img_path = type_info["image_path"]
        
        # 1. そのままのパスで存在するか確認
        if not os.path.exists(img_path):
            # 2. 存在しない場合、DATA_DIR 内を探す (例: "images/foo.png" -> "data/images/foo.png")
            alt_path = os.path.join(DATA_DIR, img_path)
            if os.path.exists(alt_path):
                img_path = alt_path
            # 3. それでもなければ、data/images 直下を探す (ファイル名のみの場合など)
            else:
                name_only = os.path.basename(img_path)
                alt_path_2 = os.path.join(IMAGES_DIR, name_only)
                if os.path.exists(alt_path_2):
                    img_path = alt_path_2
        
        # --- 子アイテム作成 (画像) ---
        self.image = QGraphicsPixmapItem(parent=self)
        pixmap = QPixmap(img_path)
        original_width = pixmap.width()
        self.scale_ratio = 1.0
        if original_width > 0:
            self.scale_ratio = self.target_width / original_width
        self.image.setPixmap(pixmap.scaledToWidth(self.target_width, Qt.SmoothTransformation))
        image_rect = self.image.boundingRect()
        self.image.setTransformOriginPoint(image_rect.center())
        
        # --- 子アイテム作成 (テキスト) ---
        self.text = DraggableTextItem(self.name, parent=self)
        self.text.setBrush(QColor("white"))
        self.text.setFlags(QGraphicsItem.ItemIsMovable)
        text_rect = self.text.boundingRect()
        self.text.setPos((image_rect.width() - text_rect.width()) / 2, image_rect.height())
        
        # --- 子アイテム作成 (チャンネル表示) ---
        self.channel_text = DraggableTextItem("", parent=self)
        self.channel_text.setBrush(QColor("cyan"))
        self.channel_text.setFlags(QGraphicsItem.ItemIsMovable)
        channel_rect = self.channel_text.boundingRect()
        self.channel_text.setPos(0, -channel_rect.height())
        
        self.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemSendsGeometryChanges)
        
        # Z値設定
        z_val = Z_VAL_EQUIPMENT_STD
        has_snaps = len(self.snap_points_data) > 0
        if self.can_be_wired: z_val = Z_VAL_EQUIPMENT_FRONT
        elif has_snaps: z_val = Z_VAL_EQUIPMENT_BACK
        self.setZValue(z_val)
        
        # 旧channel引数は互換性のため残しつつ、DMX表示を更新
        if channel: self.dmx_address = channel
        self.updateDmxText()
    
    # この機材が持つスナップポイントの現在のシーン座標リストを返すメソッド
    def get_scene_snap_points(self) -> list[QPointF]:
        """スナップ点のシーン座標リストを取得"""
        points = []
        if not self.scene(): return points
        
        # 画像の中心（ここを基準にローカル座標が定義されているため）
        img_rect = self.image.boundingRect()
        center = img_rect.center()
        
        for pt_data in self.snap_points_data:
            # データは中心からの相対座標(x, y)
            local_x = pt_data["x"] * self.scale_ratio
            local_y = pt_data["y"] * self.scale_ratio
            
            # 画像の中心にオフセットを足して、アイテムローカル座標系での位置を算出
            # (QGraphicsPixmapItemの座標系は左上が(0,0)なので、centerを加算)
            item_local_pos = QPointF(center.x() + local_x, center.y() + local_y)
            
            # それをシーン座標系に変換 (回転や移動が反映される)
            scene_pos = self.mapToScene(item_local_pos)
            points.append(scene_pos)
            
        return points
    
    def updateDmxText(self) -> None:
        """DMX情報をテキストに反映"""
        if self.has_dmx:
            # 表示形式: U1-001 (ユニバース-アドレス)
            disp_text = f"{self.dmx_universe}-{self.dmx_address}"
            self.channel_text.setText(disp_text)
        else:
            self.channel_text.setText("")
    
    def setDmxData(self, universe: int, address: int, mode_name: str) -> None:
        """DMXデータを設定"""
        self.dmx_universe = universe
        self.dmx_address = address
        self.dmx_mode_name = mode_name
        self.updateDmxText()
    
    def updateChannel(self, channel: int | None) -> None:
        """DMXアドレスを更新"""
        if channel is not None:
            self.dmx_address = channel
        self.updateDmxText()
    
    def shape(self) -> QPainterPath:
        """当たり判定の形状を返す"""
        path = QPainterPath() 
        rect = self.image.boundingRect()
        margin = 10
        rect = rect.adjusted(-margin, -margin, margin, margin)
        path.addRect(rect)
        return path
    
    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: object) -> object:
        """アイテムの状態変化時の処理"""
        # === 位置が変わる時の処理 (スナップロジック) ===
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            new_pos = value # これから移動しようとしている左上の座標
            
            # 画像の中心オフセットを取得
            rect = self.image.boundingRect()
            center_offset = rect.center()
            
            # 移動後の自分の「中心」座標（シーン基準）を計算
            current_center_scene = new_pos + center_offset
            
            SNAP_THRESHOLD = SNAP_THRESHOLD_ITEM # 吸着する距離 (ピクセル)
            snapped = False
            snap_target_pos = None
            
            # 1. 他の機材のスナップポイントへの吸着 (優先度高)
            # 自分以外の全てのアイテムをチェック
            items = self.scene().items()
            for item in items:
                if isinstance(item, EquipmentItem) and item != self:
                    # 相手がスナップポイントを持っているか確認
                    target_points = item.get_scene_snap_points()
                    for pt in target_points:
                        # 自分の中心と、相手のポイントとの距離を測る
                        dist = QLineF(current_center_scene, pt).length()
                        if dist < SNAP_THRESHOLD:
                            # 吸着！
                            # 自分の「中心」を相手のポイント(pt)に合わせる
                            # そのための「左上座標(new_pos)」を逆算する
                            snap_target_pos = pt - center_offset
                            snapped = True
                            break
                if snapped: break
            
            # スナップした場合はその位置を返す (グリッド処理はスキップ)
            if snapped:
                return snap_target_pos
            
            # 2. グリッドへの吸着 (優先度低 - 既存ロジック)
            views = self.scene().views()
            if views:
                view = views[0]
                if hasattr(view, "show_grid") and view.show_grid:
                    grid_size = view.grid_size
                    center_x = new_pos.x() + center_offset.x()
                    center_y = new_pos.y() + center_offset.y()
                    snapped_center_x = round(center_x / grid_size) * grid_size
                    snapped_center_y = round(center_y / grid_size) * grid_size
                    return QPointF(snapped_center_x - center_offset.x(), snapped_center_y - center_offset.y())
        
        # === 既存の処理 ===
        if change == QGraphicsItem.ItemSelectedChange:
            if value:
                if self.selection_mode is None:
                    self.selection_mode = 'whole'
            else:
                self.selection_mode = None
        
        if change == QGraphicsItem.ItemPositionHasChanged:
            view = self.scene().views()[0] if self.scene() and self.scene().views() else None
            if view and hasattr(view, '_redraw_all_wires'):
                view._redraw_all_wires()
            # シーン範囲の拡張処理
            if self.scene():
                current_rect = self.scene().sceneRect()
                my_pos = self.pos()
                trigger_margin = 5000 
                safe_rect = current_rect.adjusted(trigger_margin, trigger_margin, -trigger_margin, -trigger_margin)
                if not safe_rect.contains(my_pos):
                    item_rect = QRectF(my_pos.x(), my_pos.y(), 1, 1)
                    new_rect = current_rect.united(item_rect).adjusted(-1000, -1000, 1000, 1000)
                    self.scene().setSceneRect(new_rect)
                    
        return super().itemChange(change, value)
    
    def text_was_clicked(self, source_item: QGraphicsItem) -> None:
        """子テキストアイテムがクリックされたときの処理"""
        if source_item == self.text:
            self.selection_mode = 'name_text'
        elif source_item == self.channel_text:
            self.selection_mode = 'channel_text'
        self.update() # 再描画してハイライト更新
    
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """マウス押下イベント処理"""
        view = self.scene().views()[0] if self.scene() and self.scene().views() else None
        if view and view._interaction_mode != "cursor":
            event.ignore()
            return
        super().mousePressEvent(event)
        self.selection_mode = 'whole'
        self.update()
        
        self._group_start_positions = {}
        for item in self.scene().selectedItems():
            if isinstance(item, EquipmentItem):
                self._group_start_positions[item] = item.pos()
    
    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """マウスリリースイベント処理"""
        super().mouseReleaseEvent(event)
        items_to_move = []
        for item, start_pos in self._group_start_positions.items():
            current_pos = item.pos()
            if current_pos != start_pos:
                items_to_move.append((item, start_pos, current_pos))
        
        if items_to_move:
            if self.scene() and self.scene().views():
                mainWindow = self.scene().views()[0].mainWindow
                if mainWindow and hasattr(mainWindow, "undoStack"):
                    cmd = CommandMoveItems(items_to_move, "機材の移動")
                    mainWindow.undoStack.push(cmd)
        self._group_start_positions = {}
    
    def setWiringHighlight(self, highlighted: bool) -> None:
        """配線ハイライトの状態を設定する"""
        self._is_highlighted = highlighted
        self.update()
    
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget | None = None) -> None:
        """アイテムの描画処理"""
        my_option = QStyleOptionGraphicsItem(option)
        my_option.state &= ~QStyle.State_Selected
        
        if option.state & QStyle.State_Selected:
            # モードに応じたハイライト描画
            if self.selection_mode == 'whole':
                pen = QPen(QColor("cyan")); pen.setWidth(2); painter.setPen(pen)
                painter.drawRect(self.image.boundingRect().translated(self.image.pos()))
                painter.drawRect(self.text.boundingRect().translated(self.text.pos()))
                painter.drawRect(self.channel_text.boundingRect().translated(self.channel_text.pos()))
            
            elif self.selection_mode == 'name_text':
                pen = QPen(QColor("yellow")); pen.setWidth(2); painter.setPen(pen)
                painter.drawRect(self.text.boundingRect().translated(self.text.pos()))
                
            elif self.selection_mode == 'channel_text':
                pen = QPen(QColor("yellow")); pen.setWidth(2); painter.setPen(pen)
                painter.drawRect(self.channel_text.boundingRect().translated(self.channel_text.pos()))
                
        # 配線ハイライト
        if self._is_highlighted:
            highlight_pen = QPen(QColor("lime")); highlight_pen.setWidth(3); highlight_pen.setStyle(Qt.DotLine)
            painter.setPen(highlight_pen)
            painter.drawRect(self.image.boundingRect().translated(self.image.pos()))
    
    def boundingRect(self) -> QRectF:
        """アイテムの外接矩形を返す"""
        return self.childrenBoundingRect()
    
    def setRotation(self, angle: float) -> None:
        """画像の回転角度を設定する"""
        self.image.setRotation(angle)
    
    def rotation(self) -> float:
        """画像の回転角度を取得する"""
        return self.image.rotation()
    
    def setTextVisible(self, visible: bool) -> None:
        """テキストの表示・非表示を設定する"""
        self.text.setVisible(visible)
    
    def setChannelVisible(self, visible: bool) -> None:
        """チャンネルテキストの表示・非表示を設定する"""
        self.channel_text.setVisible(visible)
    
    def getTextColor(self) -> QColor:
        """テキストの色を取得する"""
        return self.text.brush().color()
    
    def setTextColor(self, color: QColor | str) -> None:
        """テキストの色を設定する"""
        if isinstance(color, str):
            color = QColor(color)
        self.text.setBrush(color)
        # 必要であればチャンネル文字の色も変える場合は以下をコメントアウト解除
        # self.channel_text.setBrush(color)
    
    def getChannelTextColor(self) -> QColor:
        """チャンネルテキストの色を取得する"""
        return self.channel_text.brush().color()
    
    def setChannelTextColor(self, color: QColor | str) -> None:
        """チャンネルテキストの色を設定する"""
        if isinstance(color, str):
            color = QColor(color)
        self.channel_text.setBrush(color)

class OutletItem(QGraphicsObject):
    """コンセント（電源）アイテム。配線可能・回路情報を持つ"""
    def __init__(self, info: dict, uid: str | None = None) -> None:
        """OutletItemの初期化"""
        super().__init__()
        self.info = info  # {x, y, circuit_id, tap_capacity, circuit_capacity, color}
        self.instance_id = uid if uid else f"outlet_{uuid.uuid4().hex[:8]}"
        self.name = f"Outlet {info.get('circuit_id', '?')}"
        self.can_be_wired = True  # 配線可能
        self.setPos(info.get("x", 0), info.get("y", 0))
        self.setZValue(Z_VAL_OUTLET)
        self.setFlags(QGraphicsItem.ItemIsSelectable)  # 移動不可
        # ツールチップ表示
        self.setToolTip(f"回路: {info.get('circuit_id')}\nタップ容量: {info.get('tap_capacity')}W\n回路容量: {info.get('circuit_capacity')}W")
        # テキストアイテム作成
        self.text_item = QGraphicsSimpleTextItem(self.info.get("circuit_id", ""), self)
        text_color_name = self.info.get("text_color", "black")
        self.text_item.setBrush(QColor(text_color_name))
        self.update_text_pos()
    
    def boundingRect(self) -> QRectF:
        """アイテムの外接矩形を返す"""
        return QRectF(-10, -10, 20, 20)
    
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget | None = None) -> None:
        """アイテムの描画処理"""
        # 本体
        color = QColor(self.info.get("color", "#FFA500"))
        painter.setBrush(color)
        
        # 選択時は枠線を強調
        if option.state & QStyle.State_Selected:
            painter.setPen(QPen(Qt.cyan, 2))
        else:
            painter.setPen(QPen(Qt.black, 1))
            
        painter.drawRect(-10, -10, 20, 20)
        # drawTextは不要（text_itemが描画を担当するため）
    
    def shape(self) -> QPainterPath:
        """当たり判定の形状を返す"""
        path = QPainterPath()
        path.addRect(-10, -10, 20, 20)
        return path
    
    def update_text_pos(self) -> None:
        """テキストの位置と内容を更新"""
        text = self.info.get("circuit_id", "")
        self.text_item.setText(text)
        
        # フォント設定
        font = QFont()
        font.setPixelSize(10)
        self.text_item.setFont(font)
        
        # 中央揃え（アイテムの上部に配置）
        r = self.text_item.boundingRect()
        self.text_item.setPos(-r.width() / 2, -22)
    
    def setWiringHighlight(self, highlighted: bool) -> None:
        """配線ハイライトの更新（ダミー）"""
        self.update()
    
    def getTextColor(self) -> QColor:
        """テキスト色を取得"""
        return self.text_item.brush().color()
    
    def setTextColor(self, color: QColor | str) -> None:
        """テキスト色を設定"""
        if isinstance(color, str):
            color = QColor(color)
        self.text_item.setBrush(color)
        # 情報を更新しておく（保存用）
        self.info["text_color"] = color.name()

class DraggableTextItem(QGraphicsSimpleTextItem):
    """ドラッグ可能なテキストアイテム（機材名やチャンネル表示用）"""
    def __init__(self, text: str, parent: QGraphicsItem | None = None) -> None:
        """初期化処理"""
        super().__init__(text, parent)
        self._old_pos = None
    
    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: object) -> object:
        """アイテムの状態変化時の処理"""
        # 位置変更時の処理（現状は未使用）
        if change == QGraphicsItem.ItemPositionHasChanged:
            if self.parentItem() and self.parentItem().scene():
                pass
        return super().itemChange(change, value)
    
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """マウス押下イベント処理"""
        # テキストクリック時の選択・移動処理
        parent = self.parentItem()
        if not parent:
            super().mousePressEvent(event)
            return
        view = parent.scene().views()[0] if parent.scene() and parent.scene().views() else None
        if not view or view._interaction_mode != "cursor":
            event.ignore()
            return
        # Shiftキーが押されていなければ他の選択を解除
        if not (event.modifiers() & Qt.ShiftModifier):
            for item in self.scene().selectedItems():
                item.setSelected(False)
        parent.setSelected(True)
        parent.text_was_clicked(self)
        event.accept()
        parent.setFlag(QGraphicsItem.ItemIsMovable, False)
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """マウスリリースイベント処理"""
        # 移動後のUndo処理
        if self._old_pos is not None:
            new_pos = self.pos()
            if self._old_pos != new_pos:
                parent = self.parentItem()
                if parent and parent.scene() and parent.scene().views():
                    mainWindow = parent.scene().views()[0].mainWindow
                    if mainWindow and hasattr(mainWindow, "undoStack"):
                        cmd = CommandMoveItems([(self, self._old_pos, new_pos)], "テキストの移動")
                        mainWindow.undoStack.push(cmd)
            self._old_pos = None
        
        parent = self.parentItem()
        if parent:
            parent.setFlag(QGraphicsItem.ItemIsMovable, True)
        super().mouseReleaseEvent(event)

class WiringItem(QGraphicsPathItem):
    """配線アイテム（DMX/電源線）。当たり判定や色分け対応"""
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget | None = None) -> None:
        """配線アイテムの描画処理"""
        super().paint(painter, option, widget)
    
    def __init__(self, start_item: QGraphicsItem, end_item: QGraphicsItem, middle_points: list[QPointF] = [], wire_type: str = "dmx") -> None:
        """配線アイテムの初期化"""
        super().__init__()
        self.start_item = start_item
        self.end_item = end_item
        self.middle_points = middle_points
        self.wire_type = wire_type  # "dmx"または"power"
        # 当たり判定幅
        self.delete_stroke_width = 1.0  # 削除用
        self.guard_stroke_width = 1.0   # 通常用
        # 線の色・スタイルをタイプで分岐
        if self.wire_type == "power":
            pen = QPen(QColor("red"), 2)
            pen.setStyle(Qt.SolidLine)
        else:
            pen = QPen(QColor("cyan"), 2)
            pen.setStyle(Qt.SolidLine)
        
        self.setPen(pen)
        
        self.setData(0, {"type": "wire"})
        self.wire_info = {
            "type": "wire",
            "wire_category": self.wire_type,
            "start_id": getattr(self.start_item, "instance_id", None),
            "end_id": getattr(self.end_item, "instance_id", None),
            "points": self.middle_points
        }
        self.setFlag(QGraphicsItem.ItemIsSelectable, False)
        self.setAcceptedMouseButtons(Qt.NoButton)
        self.setZValue(Z_VAL_WIRE)  # 線は機材より背面
        self.update_path()
    
    def update_path(self) -> None:
        """保持している情報に基づいて経路を再描画"""
        path = QPainterPath()
        if not self.start_item or not self.end_item:
            self.setPath(path)
            return
        
        # コンセント(OutletItem)にはimage属性がないため分岐処理
        if isinstance(self.start_item, EquipmentItem):
            start_pos = self.start_item.pos() + self.start_item.image.boundingRect().center()
        else: # OutletItem
            start_pos = self.start_item.pos() # OutletItemは(0,0)中心で作られているためpos()でOK
            # もしOutletItemのboundingRectの中心が(0,0)でない場合は以下を使用:
            # start_pos = self.start_item.pos() + self.start_item.boundingRect().center()
        
        if isinstance(self.end_item, EquipmentItem):
            end_pos = self.end_item.pos() + self.end_item.image.boundingRect().center()
        else:
            end_pos = self.end_item.pos()
        
        path.moveTo(start_pos)
        for point in self.middle_points:
            path.lineTo(point)
        path.lineTo(end_pos)
        self.setPath(path)
        
        self.wire_info = {
            "type": "wire",
            "wire_category": self.wire_type,
            "start_id": getattr(self.start_item, "instance_id", None),
            "end_id": getattr(self.end_item, "instance_id", None),
            "points": self.middle_points
        }
    
    def shape(self) -> QPainterPath:
        """View の現在のモードに応じて、当たり判定の幅を動的に変更する"""
        path = self.path()
        stroker = QPainterPathStroker()
        
        view = self.scene().views()[0] if self.scene() and self.scene().views() else None
        
        # デフォルトは「狭い」当たり判定 (wiring や wiring_delete 用)
        current_stroke_width = self.delete_stroke_width
        
        if view and isinstance(view, CustomGraphicsView):
            # 「配置」モード (cursor) の時だけ、バグ防止のため当たり判定を「広く」する
            if view._interaction_mode == "cursor":
                current_stroke_width = self.guard_stroke_width
        
        stroker.setWidth(current_stroke_width)
        stroker.setCapStyle(Qt.PenCapStyle.FlatCap)
        stroker.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        shape_path = stroker.createStroke(path)
        return shape_path

class CommandAddItems(QUndoCommand):
    """ 1つまたは複数のアイテムをシーンに追加するコマンド """
    def __init__(self, items: list[QGraphicsItem] | QGraphicsItem, scene: QGraphicsScene, description: str = "アイテムの追加") -> None:
        """初期化処理"""
        super().__init__(description)
        self.items = items if isinstance(items, list) else [items]
        self.scene = scene
    
    def redo(self) -> None:
        """コマンド実行（やり直し）"""
        for item in self.items:
            self.scene.addItem(item)
        self.scene.update()
    
    def undo(self) -> None:
        """コマンド取り消し（元に戻す）"""
        for item in self.items:
            if item.scene(): # シーンに存在する場合のみ削除
                self.scene.removeItem(item)
        self.scene.update()

class CommandRemoveItems(QUndoCommand):
    """ 1つまたは複数のアイテムをシーンから削除するコマンド """
    def __init__(self, items_to_delete_initially: list[QGraphicsItem], scene: QGraphicsScene, description: str = "アイテムの削除") -> None:
        """初期化処理"""
        super().__init__(description)
        self.scene = scene
        
        # 削除対象の機材に接続されている配線も検索し、削除リストに含める
        # (CustomGraphicsView.keyPressEvent のロジックをここに統合)
        items_set = set(items_to_delete_initially)
        wires_to_remove = []
        all_wires = [item for item in self.scene.items() if isinstance(item, WiringItem)]
        
        for item in items_set:
            if isinstance(item, EquipmentItem):
                for wire in all_wires:
                    if wire.start_item is item or wire.end_item is item:
                        if wire not in wires_to_remove:
                            wires_to_remove.append(wire)
        
        # 最終的に削除/復活させるアイテムのリスト（配線も含む）
        self.all_items_to_process = list(items_set | set(wires_to_remove))
        
        # 復活させる順序（機材 -> 配線）を考慮
        self.equip_items = [item for item in self.all_items_to_process if isinstance(item, EquipmentItem)]
        self.wire_items = [item for item in self.all_items_to_process if isinstance(item, WiringItem)]
    
    def redo(self) -> None:
        """コマンド実行（やり直し） -> アイテムを削除"""
        # 削除（配線 -> 機材の順が安全）
        for item in self.wire_items:
            if item.scene():
                self.scene.removeItem(item)
        for item in self.equip_items:
            if item.scene():
                self.scene.removeItem(item)
        self.scene.update()
    
    def undo(self) -> None:
        """コマンド取り消し（元に戻す） -> アイテムを復活"""
        # 復活（機材 -> 配線の順）
        for item in self.equip_items:
            if not item.scene():
                self.scene.addItem(item)
        for item in self.wire_items:
            if not item.scene():
                self.scene.addItem(item)
        self.scene.update()

class CommandMoveItems(QUndoCommand):
    """ 1つまたは複数のアイテムを移動するコマンド """
    def __init__(self, items_with_pos: list[tuple[QGraphicsItem, QPointF, QPointF]], description: str = "アイテムの移動") -> None:
        """初期化処理"""
        super().__init__(description)
        self.items_with_pos = items_with_pos
    
    def redo(self) -> None:
        """コマンド実行（やり直し）"""
        for item, _, new_pos in self.items_with_pos:
            if item.scene():
                item.setPos(new_pos)
        self.scene_update()
    
    def undo(self) -> None:
        """コマンド取り消し（元に戻す）"""
        for item, old_pos, _ in self.items_with_pos:
            if item.scene():
                item.setPos(old_pos)
        self.scene_update()
        
    def scene_update(self) -> None:
        """最初のアイテムのシーンを取得して更新する"""
        if self.items_with_pos:
            item = self.items_with_pos[0][0]
            if item.scene():
                item.scene().update()

class CommandRotateItems(QUndoCommand):
    """ 1つまたは複数のアイテムを回転するコマンド """
    def __init__(self, items_with_rot: list[tuple[QGraphicsItem, float, float]], description: str = "アイテムの回転") -> None:
        """ items_with_rot: (item, old_rot, new_rot) のタプルのリスト """
        super().__init__(description)
        self.items_with_rot = items_with_rot
    
    def redo(self) -> None:
        """コマンド実行（やり直し）"""
        for item, _, new_rot in self.items_with_rot:
            if item.scene():
                item.setRotation(new_rot)
        self.scene_update()
    
    def undo(self) -> None:
        """コマンド取り消し（元に戻す）"""
        for item, old_rot, _ in self.items_with_rot:
            if item.scene():
                item.setRotation(old_rot)
        self.scene_update()
    
    def scene_update(self) -> None:
        """シーンを更新する"""
        if self.items_with_rot:
            item = self.items_with_rot[0][0]
            if item.scene():
                item.scene().update()

class CommandChangeProperty(QUndoCommand):
    """ プロパティパネルからの変更（複数アイテム同時）を扱うクラス """
    def __init__(self, main_window: QMainWindow, items: list[QGraphicsItem], prop_name: str, old_values: list, new_value, description: str = "プロパティ変更") -> None:
        """初期化処理"""
        super().__init__(description)
        self.mainWindow = main_window
        self.items = items
        self.prop_name = prop_name
        self.old_values = old_values # item に対応する古い値のリスト
        self.new_value = new_value     # 適用する新しい単一の値
    
    def _set_property(self, item: QGraphicsItem, value) -> None:
        """ヘルパー: 1つのアイテムのプロパティを設定する"""
        try:
            if self.prop_name == "pos_x":
                rect = item.image.boundingRect()
                center_val = float(value)
                new_left = center_val - (rect.width() / 2)
                item.setPos(new_left, item.pos().y())
                
            elif self.prop_name == "pos_y":
                rect = item.image.boundingRect()
                center_val = float(value)
                new_top = center_val - (rect.height() / 2)
                item.setPos(item.pos().x(), new_top)
            elif self.prop_name == "angle":
                item.setRotation(float(value) % 360)
            elif self.prop_name == "channel":
                item.updateChannel(int(value) if str(value).strip() else None)
            elif self.prop_name == "text_visible":
                item.setTextVisible(bool(value))
            elif self.prop_name == "channel_visible":
                item.setChannelVisible(bool(value))
        except (ValueError, TypeError) as e:
            print(f"プロパティ設定エラー ({self.prop_name}={value}): {e}")
        
        # Undo/Redo後にプロパティパネルも更新（UIの状態を実態に合わせるため）
        if item.isSelected():
            # undo/redo後、パネルの表示が実態と合うように更新
            self.mainWindow.update_properties_panel()
    
    def redo(self) -> None:
        """コマンド実行（やり直し）"""
        for item in self.items:
            self._set_property(item, self.new_value)
        self.mainWindow.update_properties_panel() # 念のため全体を更新
    
    def undo(self) -> None:
        """コマンド取り消し（元に戻す）"""
        for item, old_val in zip(self.items, self.old_values):
            self._set_property(item, old_val)
        self.mainWindow.update_properties_panel() # 念のため全体を更新

class CommandChangeTextColor(QUndoCommand):
    """ 文字色変更のUndo/Redo (ターゲット対応版) """
    def __init__(self, items: list[QGraphicsItem], new_color: QColor, target_type: str = 'name', description: str = "文字色変更") -> None:
        """初期化処理"""
        super().__init__(description)
        self.items = items
        self.new_color = new_color
        self.target_type = target_type # 'name', 'channel', 'outlet'
        self.old_colors = {}
        
        # 変更前の色を保存
        for item in items:
            if target_type == 'name' and isinstance(item, EquipmentItem):
                self.old_colors[item] = item.getTextColor()
            elif target_type == 'channel' and isinstance(item, EquipmentItem):
                self.old_colors[item] = item.getChannelTextColor()
            elif target_type == 'outlet' and isinstance(item, OutletItem):
                self.old_colors[item] = item.getTextColor()
    
    def _apply_color(self, color: QColor) -> None:
        """指定した色をアイテムに適用する"""
        for item in self.items:
            if self.target_type == 'name' and isinstance(item, EquipmentItem):
                item.setTextColor(color)
            elif self.target_type == 'channel' and isinstance(item, EquipmentItem):
                item.setChannelTextColor(color)
            elif self.target_type == 'outlet' and isinstance(item, OutletItem):
                item.setTextColor(color)
        if self.items: self.items[0].scene().update()
    
    def redo(self) -> None:
        """コマンド実行（やり直し）"""
        self._apply_color(self.new_color)
    
    def undo(self) -> None:
        """コマンド取り消し（元に戻す）"""
        for item, color in self.old_colors.items():
            if self.target_type == 'name' and isinstance(item, EquipmentItem):
                item.setTextColor(color)
            elif self.target_type == 'channel' and isinstance(item, EquipmentItem):
                item.setChannelTextColor(color)
            elif self.target_type == 'outlet' and isinstance(item, OutletItem):
                item.setTextColor(color)
        if self.items: self.items[0].scene().update()

class VenueItem(QGraphicsPathItem):
    """会場の壁を表示するアイテム"""
    def __init__(self, points_list: list[QPointF], parent: QGraphicsItem | None = None) -> None:
        """初期化処理"""
        super().__init__(parent)
        self.points_list = points_list # [[p1, p2...], [p1, p2...]] 複数の壁に対応
        
        # 見た目の設定: 濃いグレーの太線
        pen = QPen(QColor(80, 80, 80), 5)
        pen.setJoinStyle(Qt.MiterJoin)
        self.setPen(pen)
        self.setBrush(Qt.NoBrush)
        
        self.setZValue(Z_VAL_VENUE) # 最背面
        self.setData(0, {"type": "venue"})
        self._update_path()
    
    def _update_path(self) -> None:
        """壁のパスを更新する"""
        path = QPainterPath()
        for points in self.points_list:
            if not points: continue
            path.moveTo(points[0])
            for p in points[1:]:
                path.lineTo(p)
            # 始点と終点が近ければ閉じる
            if len(points) > 2:
                if QLineF(points[0], points[-1]).length() < 10:
                    path.closeSubpath()
        self.setPath(path)

class VenueEditorView(QGraphicsView):
    """会場エディタ専用ビュー（編集モード・コンセントプレビュー対応）"""
    def __init__(self, scene: QGraphicsScene) -> None:
        """初期化処理"""
        super().__init__(scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setMouseTracking(True)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        # Undoスタックや各種状態
        self.undoStack = None
        self._mode = "edit"
        self._is_panning = False
        self._last_pan_pos = None
        self.current_start_point = None
        self._current_mouse_pos = None
        self._current_length_text = ""
        # プレビュー用アイテム
        self.preview_item = QGraphicsPathItem()
        pen = QPen(QColor("blue"), 2, Qt.DashLine)
        self.preview_item.setPen(pen)
        scene.addItem(self.preview_item)
        # コンセントプレビュー用
        self._outlet_preview_item = QGraphicsRectItem(-10, -10, 20, 20)
        self._outlet_preview_item.setBrush(QColor(255, 165, 0, 150))
        self._outlet_preview_item.setPen(QPen(Qt.NoPen))
        self._outlet_preview_item.setZValue(Z_VAL_PREVIEW)
        self._outlet_preview_item.setVisible(False)
        scene.addItem(self._outlet_preview_item)
        self._direction_priority = "horizontal"
        self.show_grid = True
        self.grid_size = int(DEFAULT_GRID_SIZE)
    
    def set_undo_stack(self, stack: QUndoStack) -> None:
        """Undoスタックを設定する"""
        self.undoStack = stack
    
    def set_mode(self, mode: str) -> None:
        """編集モードを切り替える"""
        # モード切替とUI更新
        self._mode = mode
        self.current_start_point = None
        self.preview_item.setPath(QPainterPath())
        self._current_length_text = ""
        self._outlet_preview_item.setVisible(mode == "outlet")
        self.viewport().update()
        if self._mode == "edit":
            self.setCursor(Qt.ArrowCursor)
            self.setDragMode(QGraphicsView.RubberBandDrag)
        elif self._mode == "draw":
            self.setCursor(Qt.CrossCursor)
            self.setDragMode(QGraphicsView.NoDrag)
        elif self._mode == "delete":
            self.setCursor(Qt.ForbiddenCursor)
            self.setDragMode(QGraphicsView.NoDrag)
        elif self._mode == "outlet":
            self.setCursor(Qt.BlankCursor)
            self.setDragMode(QGraphicsView.NoDrag)
    
    def wheelEvent(self, event: QWheelEvent) -> None:
        """マウスホイールイベント処理（ズーム対応）"""
        # Ctrl+ホイールでズーム
        if event.modifiers() == Qt.ControlModifier:
            zoom_factor = 1.25 if event.angleDelta().y() > 0 else 1 / 1.25
            self.scale(zoom_factor, zoom_factor)
            event.accept()
        else:
            super().wheelEvent(event)
    
    def keyPressEvent(self, event: QKeyEvent) -> None:
        """キー押下イベント処理"""
        # スペースで配線方向切替
        if event.key() == Qt.Key_Space and self._mode == "draw":
            if self._direction_priority == "horizontal":
                self._direction_priority = "vertical"
            else:
                self._direction_priority = "horizontal"
            cursor_pos = self.mapFromGlobal(QCursor.pos())
            fake_event = QMouseEvent(QEvent.Type.MouseMove, cursor_pos, Qt.MouseButton.NoButton, Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier)
            self.mouseMoveEvent(fake_event)
        else:
            super().keyPressEvent(event)
    
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """マウス押下イベント処理"""
        # Ctrl+左ドラッグでパン
        if event.button() == Qt.LeftButton and event.modifiers() == Qt.ControlModifier:
            self._is_panning = True
            self._last_pan_pos = event.position()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return
        if self._mode == "edit":
            super().mousePressEvent(event)
            return
        # 削除モード
        if self._mode == "delete" and event.button() == Qt.LeftButton:
            item = self.itemAt(event.position().toPoint())
            if (isinstance(item, VenueItem) or isinstance(item, VenueOutletItem)) and self.undoStack:
                cmd = VenueDeleteCommand(self.scene(), item)
                self.undoStack.push(cmd)
            event.accept()
            return
        # 壁描画モード
        if self._mode == "draw" and event.button() == Qt.LeftButton:
            pos = self.mapToScene(event.position().toPoint())
            snap_unit = DEFAULT_GRID_SIZE
            pos = QPointF(round(pos.x() / snap_unit) * snap_unit, round(pos.y() / snap_unit) * snap_unit)
            if self.current_start_point is None:
                self.current_start_point = pos
            else:
                points = [self.current_start_point]
                last = self.current_start_point
                curr = pos
                if last.x() != curr.x() and last.y() != curr.y():
                    if self._direction_priority == "horizontal":
                        corner = QPointF(curr.x(), last.y())
                    else:
                        corner = QPointF(last.x(), curr.y())
                    points.append(corner)
                points.append(curr)
                if self.undoStack:
                    item = VenueItem([points])
                    cmd = VenueAddCommand(self.scene(), item)
                    self.undoStack.push(cmd)
                else:
                    self.scene().addItem(VenueItem([points]))
                self.current_start_point = pos
            self._update_preview(pos)
            event.accept()
            return
        # コンセント配置モード
        elif self._mode == "outlet" and event.button() == Qt.LeftButton:
            pos = self._outlet_preview_item.pos()
            item = VenueOutletItem(pos.x(), pos.y())
            item.open_properties_dialog(self.scene())
            if self.undoStack:
                cmd = VenueAddOutletCommand(self.scene(), item)
                self.undoStack.push(cmd)
            else:
                self.scene().addItem(item)
            event.accept()
            return
        # 右クリックで描画キャンセル
        elif self._mode == "draw" and event.button() == Qt.RightButton:
            self.current_start_point = None
            self.preview_item.setPath(QPainterPath())
            self._current_length_text = ""
            self.viewport().update()
            event.accept()
    
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """マウス移動イベント処理"""
        if self._is_panning:
            delta = event.position() - self._last_pan_pos
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - int(delta.x()))
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - int(delta.y()))
            self._last_pan_pos = event.position(); event.accept(); return
        
        if self._mode == "outlet":
            pos = self.mapToScene(event.position().toPoint())
            snap_unit = DEFAULT_GRID_SIZE
            snapped_pos = QPointF(round(pos.x() / snap_unit) * snap_unit, round(pos.y() / snap_unit) * snap_unit)
            self._outlet_preview_item.setPos(snapped_pos)
            event.accept(); return
        
        if self._mode == "delete" and (event.buttons() & Qt.LeftButton):
            item = self.itemAt(event.position().toPoint())
            if (isinstance(item, VenueItem) or isinstance(item, VenueOutletItem)) and self.undoStack:
                if item.scene() is not None:
                    cmd = VenueDeleteCommand(self.scene(), item)
                    self.undoStack.push(cmd)
            event.accept(); return
        
        if self._mode == "draw" and self.current_start_point:
            pos = self.mapToScene(event.position().toPoint())
            snap_unit = DEFAULT_GRID_SIZE
            pos = QPointF(round(pos.x() / snap_unit) * snap_unit, round(pos.y() / snap_unit) * snap_unit)
            self._update_preview(pos)
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """マウスリリースイベント処理"""
        if self._is_panning and event.button() == Qt.LeftButton:
            self._is_panning = False; self.set_mode(self._mode); event.accept(); return
        super().mouseReleaseEvent(event)
    
    def _update_preview(self, mouse_pos: QPointF) -> None:
        """プレビュー用の壁パスを更新する"""
        self._current_mouse_pos = mouse_pos
        path = QPainterPath()
        if self.current_start_point is None: self.preview_item.setPath(path); self._current_length_text = ""; return
        start = self.current_start_point
        path.moveTo(start)
        if self._direction_priority == "horizontal": corner = QPointF(mouse_pos.x(), start.y())
        else: corner = QPointF(start.x(), mouse_pos.y())
        if corner != start and corner != mouse_pos: path.lineTo(corner)
        path.lineTo(mouse_pos)
        self.preview_item.setPath(path)
        dist_x = abs(mouse_pos.x() - start.x()); dist_y = abs(mouse_pos.y() - start.y()); total_len = dist_x + dist_y
        if total_len >= 100000: self._current_length_text = f"{total_len/100000:.2f}km"
        elif total_len >= 100: self._current_length_text = f"{total_len/100:.2f}m"
        else: self._current_length_text = f"{int(total_len)}cm"
        self.viewport().update()
    
    def drawForeground(self, painter: QPainter, rect: QRectF) -> None:
        """前景（長さ表示など）を描画する"""
        super().drawForeground(painter, rect)
        if self._mode == "draw" and self._current_length_text and self._current_mouse_pos:
            painter.save(); scale = self.transform().m11(); 
            if scale == 0: scale = 1.0
            font = painter.font(); font.setPointSizeF(12 / scale); font.setBold(True); painter.setFont(font)
            pos = self._current_mouse_pos + QPointF(20/scale, 20/scale)
            fm = QFontMetrics(painter.font()); text_rect = fm.boundingRect(self._current_length_text)
            bg_rect = QRectF(pos.x(), pos.y() - text_rect.height(), text_rect.width() + 10/scale, text_rect.height() + 5/scale)
            painter.setPen(Qt.NoPen); painter.setBrush(QColor(0, 0, 0, 150)); painter.drawRoundedRect(bg_rect, 3/scale, 3/scale)
            painter.setPen(QColor("white")); painter.drawText(pos, self._current_length_text); painter.restore()
    
    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:
        """背景（グリッドなど）を描画する"""
        super().drawBackground(painter, rect)
        scale = self.transform().m11()
        if scale == 0: scale = 1.0
        base_step_px = 100.0; step_px = base_step_px
        while (step_px * scale) < 50: step_px *= 2
        while (step_px * scale) > 150: step_px /= 2
        grid_pen = QPen(QColor(220, 220, 220)); grid_pen.setWidth(0)
        text_pen = QPen(QColor(100, 100, 100))
        font = painter.font(); font.setPointSizeF(10 / scale); painter.setFont(font)
        left = int(rect.left()) - (int(rect.left()) % int(step_px)); top = int(rect.top()) - (int(rect.top()) % int(step_px))
        viewport_rect = self.viewport().rect(); visible_rect = self.mapToScene(viewport_rect).boundingRect()
        text_offset_x = 5 / scale; text_offset_y = 15 / scale
        x = left
        while x < rect.right():
            painter.setPen(grid_pen); painter.drawLine(x, rect.top(), x, rect.bottom())
            val_cm = x; label = ""
            if abs(val_cm) < 0.1: label = "0"
            elif abs(val_cm) >= 100000: label = f"{val_cm/100000:.1f}km"
            elif abs(val_cm) >= 100: label = f"{val_cm/100:.1f}m"
            else: label = f"{int(val_cm)}cm"
            painter.setPen(text_pen); painter.drawText(QPointF(x + text_offset_x, visible_rect.top() + text_offset_y), label)
            x += step_px
        y = top
        while y < rect.bottom():
            painter.setPen(grid_pen); painter.drawLine(rect.left(), y, rect.right(), y)
            val_cm = y; label = ""
            if abs(val_cm) < 0.1: label = "0"
            elif abs(val_cm) >= 100000: label = f"{val_cm/100000:.1f}km"
            elif abs(val_cm) >= 100: label = f"{val_cm/100:.1f}m"
            else: label = f"{int(val_cm)}cm"
            painter.setPen(text_pen); painter.drawText(QPointF(visible_rect.left() + text_offset_x, y - (2/scale)), label)
            y += step_px

class VenueEditorDialog(QDialog):
    """会場を作成・編集するウィンドウ"""
    def __init__(self, parent: QWidget | None = None, load_data: dict | None = None) -> None:
        """初期化処理"""
        super().__init__(parent)
        self.setWindowTitle("会場エディタ")
        self.resize(900, 700)
        
        self.undoStack = QUndoStack(self)
        
        layout = QVBoxLayout()
        
        # --- ツールバー ---
        toolbar_layout = QHBoxLayout()
        
        # 編集（カーソル）モードボタンの追加
        self.btn_edit = QPushButton("カーソル")
        self.btn_edit.setCheckable(True)
        self.btn_edit.setChecked(True) # デフォルト選択
        self.btn_edit.clicked.connect(lambda: self.set_mode("edit"))
        
        self.btn_draw = QPushButton("壁描画")
        self.btn_draw.setCheckable(True)
        self.btn_draw.clicked.connect(lambda: self.set_mode("draw"))
        
        self.btn_outlet = QPushButton("コンセント配置")
        self.btn_outlet.setCheckable(True)
        self.btn_outlet.clicked.connect(lambda: self.set_mode("outlet"))
        
        self.btn_delete = QPushButton("削除")
        self.btn_delete.setCheckable(True)
        self.btn_delete.clicked.connect(lambda: self.set_mode("delete"))
        
        toolbar_layout.addWidget(self.btn_edit) # 追加
        toolbar_layout.addWidget(self.btn_draw)
        toolbar_layout.addWidget(self.btn_outlet)
        toolbar_layout.addWidget(self.btn_delete)
        
        toolbar_layout.addSpacing(20)
        
        self.btn_undo = QPushButton("元に戻す")
        self.btn_undo.setShortcut(QKeySequence.Undo)
        self.btn_undo.clicked.connect(self.undoStack.undo)
        self.btn_undo.setEnabled(False)
        
        self.btn_redo = QPushButton("やり直す")
        self.btn_redo.setShortcut(QKeySequence.Redo)
        self.btn_redo.clicked.connect(self.undoStack.redo)
        self.btn_redo.setEnabled(False)
        
        self.undoStack.canUndoChanged.connect(self.btn_undo.setEnabled)
        self.undoStack.canRedoChanged.connect(self.btn_redo.setEnabled)
        
        toolbar_layout.addWidget(self.btn_undo)
        toolbar_layout.addWidget(self.btn_redo)
        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)
        
        # --- 説明ラベル ---
        info_text = (
            "<b>[カーソル]</b> 選択 / ドラッグ移動 / ダブルクリック編集<br>"
            "<b>[壁]</b> 左クリック: 描画 / Space: 縦横切替 <br>"
            "<b>[コンセント]</b> クリック: 配置<br>"
            "<b>[削除]</b> アイテムをクリックして削除"
        )
        info_label = QLabel(info_text)
        info_label.setStyleSheet("color: #555;")
        layout.addWidget(info_label)
        
        # ビュー
        self.scene = QGraphicsScene(-2000, -2000, 4000, 4000)
        self.scene.setBackgroundBrush(QColor("white"))
        self.view = VenueEditorView(self.scene)
        self.view.set_undo_stack(self.undoStack)
        layout.addWidget(self.view)
        
        # 保存ボタン等
        btn_layout = QHBoxLayout()
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("会場名 (例: ホールA)")
        btn_save = QPushButton("保存して閉じる")
        btn_save.clicked.connect(self.save_venue)
        btn_cancel = QPushButton("キャンセル")
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(QLabel("会場名:"))
        btn_layout.addWidget(self.name_edit)
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        self.result_data = None
        
        # データ読み込み（編集時）
        if load_data:
            self.name_edit.setText(load_data.get("name", ""))
            
            points_data = load_data.get("walls", [])
            for wall_points in points_data:
                pts = [QPointF(p["x"], p["y"]) for p in wall_points]
                self.scene.addItem(VenueItem([pts]))
            
            outlets_data = load_data.get("outlets", [])
            for out_data in outlets_data:
                x = out_data.get("x", 0)
                y = out_data.get("y", 0)
                info = {k: v for k, v in out_data.items() if k not in ["x", "y"]}
                self.scene.addItem(VenueOutletItem(x, y, info))
                
            self.undoStack.setClean()
    
    def set_mode(self, mode: str) -> None:
        """編集モード（カーソル・壁・コンセント・削除）を切り替える"""
        self.btn_edit.setChecked(mode == "edit")
        self.btn_draw.setChecked(mode == "draw")
        self.btn_outlet.setChecked(mode == "outlet")
        self.btn_delete.setChecked(mode == "delete")
        self.view.set_mode(mode)
    
    def save_venue(self) -> None:
        """会場データを保存する"""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "エラー", "会場名を入力してください。")
            return
        
        walls_data = []
        outlets_data = []
        has_items = False
        
        for item in self.scene.items():
            if isinstance(item, VenueItem):
                has_items = True
                for points in item.points_list:
                    wall_pts = [{"x": p.x(), "y": p.y()} for p in points]
                    walls_data.append(wall_pts)
            
            elif isinstance(item, VenueOutletItem):
                has_items = True
                data = item.info.copy()
                data["x"] = item.pos().x()
                data["y"] = item.pos().y()
                outlets_data.append(data)
        
        if not has_items:
            QMessageBox.warning(self, "エラー", "壁またはコンセントが配置されていません。")
            return
            
        self.result_data = {
            "name": name,
            "walls": walls_data,
            "outlets": outlets_data
        }
        self.accept()
    
    def check_unsaved_changes(self) -> bool:
        """未保存の変更があるか確認する"""
        if self.undoStack.isClean():
            return True
        ret = QMessageBox.question(self, "変更の破棄", "変更が保存されていません。\n編集を破棄して閉じますか？", QMessageBox.Discard | QMessageBox.Cancel, QMessageBox.Cancel)
        return (ret == QMessageBox.Discard)
    
    def reject(self) -> None:
        """ダイアログを閉じる（未保存確認あり）"""
        if self.check_unsaved_changes():
            super().reject()
    
    def closeEvent(self, event: QCloseEvent) -> None:
        """ウィンドウのクローズイベント処理"""
        if self.check_unsaved_changes():
            event.accept()
        else:
            event.ignore()

class VenueManagerDialog(QDialog):
    """会場テンプレートを管理・選択するダイアログ"""
    def __init__(self, parent: QWidget = None) -> None:
        """初期化処理"""
        super().__init__(parent)
        self.setWindowTitle("会場管理")
        self.resize(400, 300)
        self.selected_venue_data = None
        
        # 保存フォルダの確保
        self.venue_dir = VENUES_DIR
        # すでに ensure_data_directories() で作成されているはずだが念のため
        if not os.path.exists(self.venue_dir):
            os.makedirs(self.venue_dir)
            
        layout = QVBoxLayout()
        
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)
        
        btn_layout = QHBoxLayout()
        btn_new = QPushButton("新規作成")
        btn_new.clicked.connect(self.create_new_venue)
        btn_edit = QPushButton("編集")
        btn_edit.clicked.connect(self.edit_venue)
        
        # 削除ボタンの追加
        btn_delete = QPushButton("削除")
        btn_delete.clicked.connect(self.delete_venue)
        
        btn_use = QPushButton("この会場を使用")
        btn_use.clicked.connect(self.use_venue)
        
        btn_layout.addWidget(btn_new)
        btn_layout.addWidget(btn_edit)
        btn_layout.addWidget(btn_delete) # レイアウトに追加
        btn_layout.addStretch()
        btn_layout.addWidget(btn_use)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        self.load_list()
    
    def load_list(self) -> None:
        """会場リストを読み込んで表示する"""
        self.list_widget.clear()
        files = glob.glob(os.path.join(self.venue_dir, "*.json"))
        for f in files:
            try:
                with open(f, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    name = data.get("name", "Unknown")
                    item = QListWidgetItem(f"{name} ({os.path.basename(f)})")
                    item.setData(Qt.UserRole, f) # ファイルパスを保持
                    self.list_widget.addItem(item)
            except Exception as e:
                print(f"会場データ読み込みエラー ({f}): {e}")
                continue
    
    def create_new_venue(self) -> None:
        """新しい会場データを作成する"""
        dialog = VenueEditorDialog(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.result_data
            # ファイル保存
            filename = f"venue_{uuid.uuid4().hex[:8]}.json"
            path = os.path.join(self.venue_dir, filename)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            self.load_list()
    
    def edit_venue(self) -> None:
        """選択した会場データを編集する"""
        item = self.list_widget.currentItem()
        if not item: return
        path = item.data(Qt.UserRole)
        
        if not os.path.exists(path):
            QMessageBox.warning(self, "エラー", "ファイルが見つかりません。")
            self.load_list()
            return
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        dialog = VenueEditorDialog(self, load_data=data)
        if dialog.exec() == QDialog.Accepted:
            new_data = dialog.result_data
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(new_data, f, indent=4, ensure_ascii=False)
            self.load_list()
    
    def delete_venue(self) -> None:
        """選択した会場データを削除する"""
        item = self.list_widget.currentItem()
        if not item: return
        
        venue_name = item.text()
        path = item.data(Qt.UserRole)
        
        ret = QMessageBox.question(
            self, 
            "削除の確認", 
            f"会場データ\n「{venue_name}」\nを本当に削除しますか？\nこの操作は元に戻せません。",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if ret == QMessageBox.Yes:
            try:
                if os.path.exists(path):
                    os.remove(path)
                self.load_list()
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"削除中にエラーが発生しました:\n{e}")
    
    def use_venue(self) -> None:
        """選択した会場データを使用する"""
        item = self.list_widget.currentItem()
        if not item: return
        path = item.data(Qt.UserRole)
        
        if not os.path.exists(path):
            QMessageBox.warning(self, "エラー", "ファイルが見つかりません。")
            self.load_list()
            return
        
        with open(path, 'r', encoding='utf-8') as f:
            self.selected_venue_data = json.load(f)
        self.accept()

class VenueAddCommand(QUndoCommand):
    """会場エディタ：アイテム追加のUndo/Redo"""
    def __init__(self, scene: QGraphicsScene, item: QGraphicsItem, description: str = "壁の追加") -> None:
        """初期化処理"""
        super().__init__(description)
        self.scene = scene
        self.item = item
    
    def redo(self) -> None:
        """コマンド実行（やり直し）"""
        # アイテムがシーンになければ追加（やり直し時）
        if self.item.scene() is None:
            self.scene.addItem(self.item)
    
    def undo(self) -> None:
        """コマンド取り消し（元に戻す）"""
        # アイテムがシーンにあれば削除（元に戻す時）
        if self.item.scene() is not None:
            self.scene.removeItem(self.item)

class VenueDeleteCommand(QUndoCommand):
    """会場エディタ：アイテム削除のUndo/Redo"""
    def __init__(self, scene: QGraphicsScene, item: QGraphicsItem, description: str = "壁の削除") -> None:
        """初期化処理"""
        super().__init__(description)
        self.scene = scene
        self.item = item
    
    def redo(self) -> None:
        """コマンド実行（やり直し）"""
        # 削除実行
        if self.item.scene() is not None:
            self.scene.removeItem(self.item)
    
    def undo(self) -> None:
        """コマンド取り消し（元に戻す）"""
        # 削除取り消し（復活）
        if self.item.scene() is None:
            self.scene.addItem(self.item)

class VenueOutletItem(QGraphicsRectItem):
    """会場エディタ上に表示されるコンセントアイテム"""
    def __init__(self, x: float, y: float, info: dict = None) -> None:
        """初期化処理"""
        super().__init__(-10, -10, 20, 20) # 20x20の矩形
        self.setPos(x, y)
        
        # データ (回路ID, タップ容量, 回路容量, 色)
        if info:
            self.info = info
        else:
            self.info = {
                "circuit_id": "A-1",
                "tap_capacity": 1500,
                "circuit_capacity": 2000,
                "color": "#FFA500" # デフォルト: オレンジ
            }
        
        # 色情報がない場合のフォールバック
        if "color" not in self.info:
            self.info["color"] = "#FFA500"
        
        self.setBrush(QColor(self.info["color"]))
        self.setPen(QPen(Qt.black))
        
        self.text_item = QGraphicsSimpleTextItem(self.info["circuit_id"], self)
        self.text_item.setBrush(QColor("black"))
        self.update_text_pos()
        
        self.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemSendsGeometryChanges)
    
    def update_text_pos(self) -> None:
        """テキストの位置を更新する"""
        self.text_item.setText(self.info["circuit_id"])
        r = self.text_item.boundingRect()
        self.text_item.setPos(-r.width()/2, -25)
    
    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """ダブルクリック時にプロパティダイアログを開く"""
        self.open_properties_dialog()
        super().mouseDoubleClickEvent(event)
    
    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: object) -> object:
        """アイテムの状態変化時の処理（グリッドスナップ対応）"""
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            new_pos = value
            views = self.scene().views()
            if views:
                view = views[0]
                if hasattr(view, "grid_size") and view.show_grid:
                    gs = view.grid_size
                    snapped_x = round(new_pos.x() / gs) * gs
                    snapped_y = round(new_pos.y() / gs) * gs
                    return QPointF(snapped_x, snapped_y)
        return super().itemChange(change, value)
    
    def open_properties_dialog(self, scene_context: QGraphicsScene = None) -> None:
        """コンセント設定ダイアログを開く"""
        dialog = QDialog()
        dialog.setWindowTitle("コンセント設定")
        layout = QFormLayout()
        
        id_edit = QLineEdit(self.info["circuit_id"])
        tap_edit = QSpinBox()
        tap_edit.setRange(0, 5000); tap_edit.setValue(int(self.info["tap_capacity"])); tap_edit.setSuffix(" W")
        circ_edit = QSpinBox()
        circ_edit.setRange(0, 20000); circ_edit.setValue(int(self.info["circuit_capacity"])); circ_edit.setSuffix(" W")
        
        # 色選択ボタン
        color_btn = QPushButton()
        current_hex = self.info["color"]
        color_btn.setText(current_hex)
        color_btn.setStyleSheet(f"background-color: {current_hex}; color: black;")
        selected_color_ref = [current_hex]
        
        def pick_color():
            c = QColorDialog.getColor(QColor(selected_color_ref[0]), dialog, "回路色を選択")
            if c.isValid():
                new_hex = c.name()
                selected_color_ref[0] = new_hex
                color_btn.setText(new_hex)
                color_btn.setStyleSheet(f"background-color: {new_hex}; color: black;")
        
        color_btn.clicked.connect(pick_color)
        
        layout.addRow("回路番号/名:", id_edit)
        layout.addRow("タップ容量:", tap_edit)
        layout.addRow("回路容量:", circ_edit)
        layout.addRow("表示色:", color_btn)
        
        btn_box = QHBoxLayout()
        ok_btn = QPushButton("OK"); ok_btn.clicked.connect(dialog.accept)
        cancel_btn = QPushButton("キャンセル"); cancel_btn.clicked.connect(dialog.reject)
        btn_box.addWidget(ok_btn); btn_box.addWidget(cancel_btn)
        layout.addRow(btn_box)
        
        dialog.setLayout(layout)
        
        if dialog.exec() == QDialog.Accepted:
            # 自身の更新
            new_circuit_id = id_edit.text()
            new_color = selected_color_ref[0]
            new_circuit_capacity = circ_edit.value()
            
            self.info["circuit_id"] = new_circuit_id
            self.info["tap_capacity"] = tap_edit.value() # タップ容量は同期しない
            self.info["circuit_capacity"] = new_circuit_capacity
            self.info["color"] = new_color
            
            self.setBrush(QColor(new_color))
            self.update_text_pos()
            
            # 同一回路への同期処理（他のVenueOutletItemにも色変更を反映）
            target_scene = self.scene() or scene_context
            if target_scene:
                # シーン内の全ての VenueOutletItem を走査
                for item in target_scene.items():
                    # 自分自身は除外（すでに更新済みのため）
                    if isinstance(item, VenueOutletItem) and item != self:
                        # 回路IDが一致する場合のみ同期
                        if item.info.get("circuit_id") == new_circuit_id:
                            item.info["color"] = new_color
                            item.info["circuit_capacity"] = new_circuit_capacity
                            # 見た目を更新
                            item.setBrush(QColor(new_color))
                            # タップ容量(tap_capacity)は変更しない

class VenueAddOutletCommand(QUndoCommand):
    """会場エディタ：コンセント追加のUndo/Redo"""
    def __init__(self, scene: QGraphicsScene, item: QGraphicsItem, description: str = "コンセント追加") -> None:
        """初期化処理"""
        super().__init__(description)
        self.scene = scene
        self.item = item
    
    def redo(self) -> None:
        """コマンド実行（やり直し）"""
        if self.item.scene() is None:
            self.scene.addItem(self.item)
    
    def undo(self) -> None:
        """コマンド取り消し（元に戻す）"""
        if self.item.scene() is not None:
            self.scene.removeItem(self.item)

class PowerReportDialog(QDialog):
    """電力計算結果を表示するダイアログ"""
    def __init__(self, report_data: dict, parent: QWidget = None) -> None:
        """初期化処理"""
        super().__init__(parent)
        self.setWindowTitle("電力計算レポート")
        self.resize(600, 500)
        
        layout = QVBoxLayout()
        
        # --- ツリー表示 ---
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["項目", "使用電力 / 上限", "状態"])
        self.tree.setColumnWidth(0, 250)
        self.tree.setColumnWidth(1, 150)
        layout.addWidget(self.tree)
        
        # --- データの流し込み ---
        self.populate_tree(report_data)
        
        # 閉じるボタン
        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_close = QPushButton("閉じる")
        btn_close.clicked.connect(self.accept)
        btn_box.addWidget(btn_close)
        layout.addLayout(btn_box)
        
        self.setLayout(layout)
    
    def populate_tree(self, data: dict) -> None:
        """電力計算結果データをツリーに表示する"""
        self.tree.clear()
        
        # 1. 回路ごとの表示
        for circuit_id, c_data in data["circuits"].items():
            # 回路アイテム
            total = c_data["total_watts"]
            limit = c_data["limit"]
            status = "OK"
            color = Qt.black
            
            if total > limit:
                status = "⚠️ 容量オーバー"
                color = Qt.red
            
            circuit_item = QTreeWidgetItem(self.tree)
            circuit_item.setText(0, f"回路: {circuit_id}")
            circuit_item.setText(1, f"{total}W / {limit}W")
            circuit_item.setText(2, status)
            circuit_item.setForeground(0, color); circuit_item.setForeground(1, color); circuit_item.setForeground(2, color)
            
            # コンセント（タップ）ごとの表示
            for outlet_obj, o_data in c_data["outlets"].items():
                o_total = o_data["total_watts"]
                o_limit = o_data["limit"]
                o_status = "OK"
                o_color = Qt.black
                
                if o_total > o_limit:
                    o_status = "⚠️ タップ容量オーバー"
                    o_color = Qt.red # 回路がOKでもタップがNGなら赤
                elif color == Qt.red:
                    o_color = Qt.red # 親（回路）がNGなら子も赤くしておく
                
                # アイテム名生成（OutletItemから情報を取る）
                outlet_name = "コンセント"
                if hasattr(outlet_obj, "info"):
                    outlet_name = f"コンセント ({outlet_obj.info.get('circuit_id')})"
                
                outlet_item = QTreeWidgetItem(circuit_item)
                outlet_item.setText(0, outlet_name)
                outlet_item.setText(1, f"{o_total}W / {o_limit}W")
                outlet_item.setText(2, o_status)
                outlet_item.setForeground(0, o_color); outlet_item.setForeground(1, o_color); outlet_item.setForeground(2, o_color)
                
                # 接続されている機材の表示
                for equip in o_data["equipment"]:
                    w = equip.data(0).get("power_consumption", 0)
                    eq_item = QTreeWidgetItem(outlet_item)
                    eq_item.setText(0, equip.name)
                    eq_item.setText(1, f"{w}W")
                    eq_item.setText(2, "-")
        
        # 2. 未配線の機材
        if data["unpowered"]:
            unpowered_root = QTreeWidgetItem(self.tree)
            unpowered_root.setText(0, "⚠️ 電源未接続の機材")
            unpowered_root.setForeground(0, Qt.darkYellow)
            
            for item in data["unpowered"]:
                w = item.data(0).get("power_consumption", 0)
                item_node = QTreeWidgetItem(unpowered_root)
                item_node.setText(0, item.name)
                item_node.setText(1, f"{w}W (未計上)")
                item_node.setText(2, "未接続")
        
        self.tree.expandAll()

class CommandChangeZValue(QUndoCommand):
    """アイテムのZ値（重なり順）を変更するコマンド"""
    def __init__(self, item: QGraphicsItem, old_z: float, new_z: float, description: str = "Z値変更") -> None:
        """初期化処理"""
        super().__init__(description)
        self.item = item
        self.old_z = old_z
        self.new_z = new_z
    
    def redo(self) -> None:
        """コマンド実行（やり直し）"""
        self.item.setZValue(self.new_z)
        self.item.update()
    
    def undo(self) -> None:
        """コマンド取り消し（元に戻す）"""
        self.item.setZValue(self.old_z)
        self.item.update()

class PatchWindow(QDialog):
    """DMXパッチを管理・一覧表示するウィンドウ"""
    def __init__(self, scene: QGraphicsScene, parent: QWidget = None) -> None:
        """初期化処理"""
        super().__init__(parent)
        self.scene = scene
        self.setWindowTitle("DMX パッチ管理")
        self.resize(1200, 600)
        
        layout = QVBoxLayout()
        
        # --- ツールバー ---
        top_layout = QHBoxLayout()
        self.btn_refresh = QPushButton("更新 / チェック")
        self.btn_refresh.clicked.connect(self.load_data)
        self.lbl_status = QLabel("状態: 準備完了")
        
        top_layout.addWidget(self.btn_refresh)
        top_layout.addWidget(self.lbl_status)
        top_layout.addStretch()
        layout.addLayout(top_layout)
        
        # --- パッチテーブル ---
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        
        # カスタムヘッダーを設定
        self.header = FilterHeaderView(self.table)
        self.header.filterChanged.connect(self.apply_filters)
        self.table.setHorizontalHeader(self.header)
        
        self.table.setHorizontalHeaderLabels([
            "ID", "機材名", "メーカー", "モード", 
            "Univ", "Start", "Ch数", "End"
        ])
        
        # ソート有効化
        self.table.setSortingEnabled(True)
        
        # リサイズモード: ユーザーが調整可能(Interactive)にする
        # ただし初期状態はある程度見やすくするため Stretch 等を組み合わせるのが一般的ですが、
        # ここではInteractiveにしてユーザーの自由度を優先します。
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        # 初期幅の調整（適当に広げる）
        self.table.setColumnWidth(1, 200) # 機材名
        self.table.setColumnWidth(3, 150) # モード
        
        # 編集時のシグナル
        self.table.itemChanged.connect(self.on_table_item_changed)
        
        layout.addWidget(self.table)
        self.setLayout(layout)
        
        # データ読み込み
        self.load_data()
    
    def load_data(self) -> None:
        """シーンからDMX機材を収集して表示する"""
        self.table.blockSignals(True)
        self.table.setSortingEnabled(False) 
        self.table.setRowCount(0)
        
        self.dmx_items = []
        for item in self.scene.items():
            # DMXを持ち、かつ EquipmentItem であるものを探す
            if isinstance(item, EquipmentItem) and item.has_dmx:
                # コントローラー（卓）はパッチ対象外なので除外
                if item.data(0).get("is_controller", False):
                    continue
                
                self.dmx_items.append(item)
        
        # デフォルトソート: ユニバース -> アドレス
        self.dmx_items.sort(key=lambda x: (x.dmx_universe, x.dmx_address))
        
        for row, item in enumerate(self.dmx_items):
            self.table.insertRow(row)
            
            # ID
            id_item = QTableWidgetItem(item.instance_id[:8])
            id_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            id_item.setData(Qt.UserRole, item) # 行にアイテム参照を持たせる
            self.table.setItem(row, 0, id_item)
            
            # 機材名
            name_item = QTableWidgetItem(item.name)
            name_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.table.setItem(row, 1, name_item)
            
            # メーカー
            manuf = item.data(0).get("manufacturer", "")
            manuf_item = QTableWidgetItem(manuf)
            manuf_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.table.setItem(row, 2, manuf_item)
            
            # モード (Combo + TextItem for Sorting)
            # ソートのために、セルのテキストにもモード名をセットしておく
            mode_item = QTableWidgetItem(item.dmx_mode_name)
            self.table.setItem(row, 3, mode_item)
            
            # コンボボックス作成
            mode_combo = QComboBox()
            modes = item.data(0).get("dmx_modes", [])
            for m in modes:
                mode_combo.addItem(m["name"], m["channels"])
            mode_combo.setCurrentText(item.dmx_mode_name)
            
            # コンボボックス変更シグナル
            # 行番号はソートやフィルタで変わるため、item参照を使って特定するアプローチが安全だが、
            # 簡易的にlambdaで処理し、呼び出し先で再検索する
            mode_combo.currentIndexChanged.connect(lambda idx, r=row, it=item: self.on_mode_changed(it, idx))
            self.table.setCellWidget(row, 3, mode_combo)
            
            # Universe (数値)
            univ_item = NumericTableWidgetItem(str(item.dmx_universe))
            self.table.setItem(row, 4, univ_item)
            
            # Start Addr (数値)
            addr_item = NumericTableWidgetItem(str(item.dmx_address))
            self.table.setItem(row, 5, addr_item)
            
            # Ch数 (数値・計算)
            current_ch = 1
            for m in modes:
                if m["name"] == item.dmx_mode_name:
                    current_ch = m.get("channels", 1)
                    break
            ch_item = NumericTableWidgetItem(str(current_ch))
            ch_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.table.setItem(row, 6, ch_item)
            
            # End Addr (数値・計算)
            end_addr = item.dmx_address + current_ch - 1
            end_item = NumericTableWidgetItem(str(end_addr))
            end_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.table.setItem(row, 7, end_item)
        
        self.table.setSortingEnabled(True)
        self.apply_filters()
        self.validate_patch()
        self.table.blockSignals(False)
    
    def apply_filters(self) -> None:
        """ヘッダーのフィルタ設定に基づいて行の表示/非表示を切り替え"""
        for row in range(self.table.rowCount()):
            visible = self.header.isRowVisible(row, self.table)
            self.table.setRowHidden(row, not visible)
    
    def on_table_item_changed(self, item: QTableWidgetItem) -> None:
        """テーブルセル編集時の処理"""
        row = item.row()
        col = item.column()
        target_item = self.table.item(row, 0).data(Qt.UserRole)
        if not target_item: return
        
        try:
            val = int(item.text())
            if col == 4: # Universe
                if target_item.dmx_universe != val:
                    target_item.dmx_universe = val
                    target_item.updateDmxText()
                    self.validate_patch()
            elif col == 5: # Address
                if target_item.dmx_address != val:
                    target_item.dmx_address = val
                    target_item.updateDmxText()
                    self.update_row_calculations(row, target_item) # End再計算
                    self.validate_patch()
        except ValueError: pass
    
    def on_mode_changed(self, item: EquipmentItem, index: int) -> None:
        """モードコンボボックス変更時の処理"""
        # ソートやフィルタで行番号が変わっている可能性があるため、アイテムから行を逆引き
        row = -1
        for r in range(self.table.rowCount()):
            if self.table.item(r, 0).data(Qt.UserRole) == item:
                row = r
                break
        if row == -1: return
        
        combo = self.table.cellWidget(row, 3)
        if not combo: return
        
        new_mode_name = combo.currentText()
        
        # ソート用の裏データ(テキスト)も更新
        self.table.item(row, 3).setText(new_mode_name)
        
        if item.dmx_mode_name != new_mode_name:
            item.dmx_mode_name = new_mode_name
            item.updateDmxText()
            self.update_row_calculations(row, item)
            self.validate_patch()
    
    def update_row_calculations(self, row: int, item: EquipmentItem) -> None:
        """行のチャンネル数・Endアドレスを再計算する"""
        self.table.blockSignals(True)
        modes = item.data(0).get("dmx_modes", [])
        current_ch = 1
        for m in modes:
            if m["name"] == item.dmx_mode_name:
                current_ch = m.get("channels", 1)
                break
        
        self.table.item(row, 6).setText(str(current_ch))
        end_addr = item.dmx_address + current_ch - 1
        self.table.item(row, 7).setText(str(end_addr))
        self.table.blockSignals(False)
    
    def validate_patch(self) -> None:
        """重複チェック、512ch超過、およびDMX未結線チェック"""
        overlap_count = 0
        universe_overflow = 0
        unconnected_count = 0 
        
        # --- 1. DMX結線の接続確認 (BFS探索) ---
        adj = {}
        for item in self.scene.items():
            if isinstance(item, WiringItem) and item.wire_type == "dmx":
                u, v = item.start_item, item.end_item
                if u and v:
                    adj.setdefault(u, []).append(v)
                    adj.setdefault(v, []).append(u)
        
        sources = []
        for item in self.scene.items():
            if isinstance(item, EquipmentItem) and item.has_dmx:
                if item.data(0).get("is_controller", False):
                    sources.append(item)
        
        reachable = set(sources)
        queue = list(sources)
        while queue:
            curr = queue.pop(0)
            for neighbor in adj.get(curr, []):
                if neighbor not in reachable and isinstance(neighbor, EquipmentItem):
                    reachable.add(neighbor)
                    queue.append(neighbor)
        # ---------------------------------------
        
        # 全行の背景と文字色をリセット（初期化）
        for r in range(self.table.rowCount()):
            for c in range(self.table.columnCount()):
                it = self.table.item(r, c)
                if it: 
                    it.setBackground(Qt.NoBrush)
                    it.setForeground(Qt.white) # デフォルト文字色を白に戻す
        
        entries = []
        for r in range(self.table.rowCount()):
            target_item = self.table.item(r, 0).data(Qt.UserRole)
            if not target_item: continue
            
            # --- Check A: 未結線チェック (Yellow) ---
            if target_item not in reachable:
                unconnected_count += 1
                # 黄色背景のときは文字色を黒(Qt.black)にする（視認性向上のため）
                self._set_row_color(r, QColor(255, 255, 200), Qt.black)
            
            try:
                name = self.table.item(r, 1).text()
                combo = self.table.cellWidget(r, 3)
                mode = combo.currentText() if combo else ""
                univ = int(self.table.item(r, 4).text())
                start = int(self.table.item(r, 5).text())
                end = int(self.table.item(r, 7).text())
                
                entries.append({
                    'row': r, 'u': univ, 's': start, 'e': end,
                    'name': name, 'mode': mode
                })
                
                # --- Check B: 512ch超過 (Orange) ---
                if end > 512:
                    universe_overflow += 1
                    # オレンジも見づらければ黒文字推奨ですが、今回は白(None)または黒を指定
                    self._set_row_color(r, QColor(255, 200, 100), Qt.black)
                    
            except Exception as e:
                print(f"パッチ検証エラー (行 {r}): {e}")
            
        # --- Check C: 重複チェック (Red) ---
        for i in range(len(entries)):
            for j in range(i + 1, len(entries)):
                a = entries[i]
                b = entries[j]
                
                if a['u'] == b['u']:
                    if a['s'] <= b['e'] and b['s'] <= a['e']:
                        is_same_machine = (a['name'] == b['name'])
                        is_same_mode = (a['mode'] == b['mode'])
                        is_same_start = (a['s'] == b['s'])
                        
                        if is_same_machine and is_same_mode and is_same_start:
                            continue
                        else:
                            overlap_count += 1
                            # 赤背景は白文字で見やすいので、文字色はデフォルト(Qt.white)でOK
                            self._set_row_color(a['row'], QColor(255, 100, 100), Qt.white)
                            self._set_row_color(b['row'], QColor(255, 100, 100), Qt.white)
        
        msg = []
        if overlap_count > 0: msg.append(f"重複: {overlap_count}件")
        if universe_overflow > 0: msg.append(f"512ch超過: {universe_overflow}件")
        if unconnected_count > 0: msg.append(f"未結線: {unconnected_count}件")
        
        if not msg:
            self.lbl_status.setText("状態: OK")
            self.lbl_status.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.lbl_status.setText("状態: ⚠️ " + ", ".join(msg))
            if overlap_count > 0:
                self.lbl_status.setStyleSheet("color: red; font-weight: bold;")
            elif universe_overflow > 0:
                self.lbl_status.setStyleSheet("color: orange; font-weight: bold;")
            else:
                self.lbl_status.setStyleSheet("color: #b58900; font-weight: bold;")
    
    def _set_row_color(self, row: int, bg_color: QColor, text_color: QColor = None) -> None:
        """指定した行のセル背景色と文字色を変更する"""
        for c in range(self.table.columnCount()):
            it = self.table.item(row, c)
            if it:
                it.setBackground(bg_color)
                if text_color:
                    it.setForeground(text_color)

class AdvancedTableWidget(QTableWidget):
    """ 並び替え、列移動、列表示切替、行ドラッグ移動に対応した高機能テーブル """
    def __init__(self, parent: QWidget = None) -> None:
        """初期化処理"""
        super().__init__(parent)
        
        # 基本設定
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        
        # ヘッダー設定
        self.horizontalHeader().setSectionsMovable(True) # 列の入れ替え
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive) # サイズ変更
        self.horizontalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.horizontalHeader().customContextMenuRequested.connect(self.show_header_menu)
        
        # 行のドラッグ移動設定 (行番号ヘッダーをドラッグして移動)
        self.verticalHeader().setSectionsMovable(True)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)
    
    def show_header_menu(self, pos: QPoint) -> None:
        """列ヘッダーの右クリックメニュー（表示/非表示の切り替え）"""
        header = self.horizontalHeader()
        global_pos = header.mapToGlobal(pos)
        
        menu = QMenu(self)
        for col in range(self.columnCount()):
            # ロジカルインデックス（データ上の列番号）を取得
            column_name = self.horizontalHeaderItem(col).text()
            
            action = menu.addAction(column_name)
            action.setCheckable(True)
            action.setChecked(not self.isColumnHidden(col))
            
            # ラムダ式で変数を固定してスロット接続
            action.triggered.connect(lambda checked, c=col: self.setColumnHidden(c, not checked))
            
        menu.exec(global_pos)
    
    def get_html_from_table(self, title: str) -> str:
        """現在のテーブルの見た目（並び順、非表示列）を反映したHTMLを生成"""
        html = f"<h2>{title}</h2>"
        # スタイル: 黒文字、白背景、境界線あり
        html += "<table border='1' cellspacing='0' cellpadding='4' width='100%' style='color: black; background-color: white; border-collapse: collapse; font-size: 10pt;'>"
        
        # --- ヘッダー ---
        html += "<tr style='background-color: #555; color: white;'>"
        
        # 表示されている列のインデックス（視覚的な順番）を取得
        header = self.horizontalHeader()
        visual_indices = []
        for v_idx in range(header.count()):
            l_idx = header.logicalIndex(v_idx)
            if not self.isColumnHidden(l_idx):
                visual_indices.append(l_idx)
                name = self.horizontalHeaderItem(l_idx).text()
                html += f"<th>{name}</th>"
        html += "</tr>"
        
        # --- データ行 ---
        # 行も視覚的な順番（ドラッグ移動後など）で処理したい場合は工夫が必要ですが、
        # QTableWidgetのソート/移動はVisualな行とLogicalな行が乖離することがあるため、
        # ここでは「現在見えている上からの順番」で取得します。
        
        row_count = self.rowCount()
        for v_row in range(row_count):
            # フィルタで隠されている行はスキップ
            if self.isRowHidden(v_row):
                continue
                
            bg_color = "#f9f9f9" if v_row % 2 == 0 else "#ffffff"
            html += f"<tr style='background-color: {bg_color}; color: black;'>"
            
            for l_col in visual_indices:
                item = self.item(v_row, l_col)
                text = item.text() if item else ""
                html += f"<td>{text}</td>"
            html += "</tr>"
            
        html += "</table>"
        return html

class TablePreviewDialog(QDialog):
    """エクスポート前のテーブルプレビュー・編集ダイアログ"""
    def __init__(self, parent: QWidget = None) -> None:
        """初期化処理"""
        super().__init__(parent)
        self.setWindowTitle("表のプレビューと編集")
        self.resize(1000, 600)
        
        layout = QVBoxLayout()
        
        # 説明ラベル
        info = QLabel(
            "<b>操作方法:</b><br>"
            "・<b>列の入れ替え:</b> ヘッダーをドラッグ<br>"
            "・<b>列の表示/非表示:</b> ヘッダーを右クリック<br>"
            "・<b>行の並び替え:</b> 左端の行番号をドラッグ<br>"
            "・<b>ソート:</b> ヘッダーをクリック (※ソート中は行のドラッグ移動が無効になる場合があります)"
        )
        info.setStyleSheet("background-color: #eee; color: black; padding: 5px; border-radius: 4px;")
        layout.addWidget(info)
        
        self.tab_widget = QTabWidget()
        
        # DMXテーブル
        self.dmx_table = AdvancedTableWidget()
        self.tab_widget.addTab(self.dmx_table, "DMXアドレス一覧表")
        
        # 電源テーブル
        self.pwr_table = AdvancedTableWidget()
        self.tab_widget.addTab(self.pwr_table, "電源回路一覧表")
        
        layout.addWidget(self.tab_widget)
        
        # ボタン
        btn_layout = QHBoxLayout()
        btn_export = QPushButton("この内容で出力")
        btn_export.clicked.connect(self.accept)
        btn_cancel = QPushButton("キャンセル")
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_export)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def populate_dmx_data(self, scene: QGraphicsScene) -> None:
        """DMXデータをシーンから読み込んでテーブルにセット"""
        items = [i for i in scene.items() if isinstance(i, EquipmentItem) and i.has_dmx]
        # デフォルトのソート順
        items.sort(key=lambda x: (x.dmx_universe, x.dmx_address))
        
        headers = ["No.", "Univ", "Addr", "機材名", "メーカー", "モード", "Ch数", "備考"]
        self.dmx_table.setColumnCount(len(headers))
        self.dmx_table.setHorizontalHeaderLabels(headers)
        self.dmx_table.setRowCount(0)
        
        for i, item in enumerate(items):
            row = self.dmx_table.rowCount()
            self.dmx_table.insertRow(row)
            
            modes = item.data(0).get("dmx_modes", [])
            ch_count = 1
            for m in modes:
                if m["name"] == item.dmx_mode_name:
                    ch_count = m.get("channels", 1)
                    break
            
            # No.
            self.dmx_table.setItem(row, 0, NumericTableWidgetItem(str(i + 1)))
            # Univ
            self.dmx_table.setItem(row, 1, NumericTableWidgetItem(str(item.dmx_universe)))
            # Addr
            self.dmx_table.setItem(row, 2, NumericTableWidgetItem(str(item.dmx_address)))
            # Name
            self.dmx_table.setItem(row, 3, QTableWidgetItem(item.name))
            # Manufacturer
            manuf = item.data(0).get("manufacturer", "")
            self.dmx_table.setItem(row, 4, QTableWidgetItem(manuf))
            # Mode
            self.dmx_table.setItem(row, 5, QTableWidgetItem(item.dmx_mode_name))
            # Ch
            self.dmx_table.setItem(row, 6, NumericTableWidgetItem(str(ch_count)))
            # Note (空欄)
            self.dmx_table.setItem(row, 7, QTableWidgetItem(""))
        
        self.dmx_table.resizeColumnsToContents()
    
    def populate_power_data(self, report_data: dict) -> None:
        """計算済みの電力データをテーブルにセット"""
        headers = ["回路", "コンセント", "接続機材", "消費電力", "上限", "状態"]
        self.pwr_table.setColumnCount(len(headers))
        self.pwr_table.setHorizontalHeaderLabels(headers)
        self.pwr_table.setRowCount(0)
        
        # フラットなリストに変換して表示しやすくする
        for circuit_id, c_data in report_data["circuits"].items():
            for outlet_obj, o_data in c_data["outlets"].items():
                row = self.pwr_table.rowCount()
                self.pwr_table.insertRow(row)
                
                outlet_name = outlet_obj.info.get('circuit_id', 'Unknown') if hasattr(outlet_obj, 'info') else "Outlet"
                equip_names = [eq.name for eq in o_data["equipment"]]
                equip_str = ", ".join(equip_names) if equip_names else "(なし)"
                status = "OVER" if o_data["total_watts"] > o_data["limit"] else "OK"
                
                self.pwr_table.setItem(row, 0, QTableWidgetItem(str(circuit_id)))
                self.pwr_table.setItem(row, 1, QTableWidgetItem(str(outlet_name)))
                self.pwr_table.setItem(row, 2, QTableWidgetItem(equip_str))
                self.pwr_table.setItem(row, 3, NumericTableWidgetItem(f"{o_data['total_watts']}"))
                self.pwr_table.setItem(row, 4, NumericTableWidgetItem(f"{o_data['limit']}"))
                
                status_item = QTableWidgetItem(status)
                if status == "OVER":
                    status_item.setForeground(QColor("red"))
                    status_item.setFont(QFont("Arial", 10, QFont.Bold))
                self.pwr_table.setItem(row, 5, status_item)
                
        # 未接続
        for item in report_data["unpowered"]:
            row = self.pwr_table.rowCount()
            self.pwr_table.insertRow(row)
            w = item.data(0).get("power_consumption", 0)
            
            self.pwr_table.setItem(row, 0, QTableWidgetItem("-"))
            self.pwr_table.setItem(row, 1, QTableWidgetItem("-"))
            self.pwr_table.setItem(row, 2, QTableWidgetItem(item.name))
            self.pwr_table.setItem(row, 3, NumericTableWidgetItem(str(w)))
            self.pwr_table.setItem(row, 4, QTableWidgetItem("-"))
            self.pwr_table.setItem(row, 5, QTableWidgetItem("未接続"))
            
        self.pwr_table.resizeColumnsToContents()
    
    def get_dmx_html(self) -> str:
        """DMXテーブルのHTMLを取得する"""
        return self.dmx_table.get_html_from_table("")
    
    def get_power_html(self) -> str:
        """電源テーブルのHTMLを取得する"""
        return self.pwr_table.get_html_from_table("")

class ExportDialog(QDialog):
    """出力設定ダイアログ"""
    def __init__(self, parent: QWidget = None) -> None:
        """初期化処理"""
        super().__init__(parent)
        self.setWindowTitle("エクスポート設定")
        self.resize(400, 350)
        
        layout = QVBoxLayout()
        
        # --- 出力内容の選択 ---
        layout.addWidget(QLabel("<b>出力する項目を選択:</b>"))
        self.chk_layout = QCheckBox("1. 機材配置図")
        self.chk_dmx_map = QCheckBox("2. DMX配線図")
        self.chk_dmx_list = QCheckBox("3. DMXアドレス一覧表")
        self.chk_pwr_map = QCheckBox("4. 電源配線図")
        self.chk_pwr_list = QCheckBox("5. 電源回路一覧表")
        
        # 全てデフォルトでON
        for chk in [self.chk_layout, self.chk_dmx_map, self.chk_dmx_list, self.chk_pwr_map, self.chk_pwr_list]:
            chk.setChecked(True)
            layout.addWidget(chk)
            
        layout.addSpacing(10)
        
        # --- 形式の選択 ---
        layout.addWidget(QLabel("<b>出力形式:</b>"))
        self.radio_pdf = QRadioButton("PDF (1つのファイルにまとめる)")
        self.radio_png = QRadioButton("PNG (画像ファイルとして個別に出力)")
        self.radio_pdf.setChecked(True)
        
        bg_group = QButtonGroup(self)
        bg_group.addButton(self.radio_pdf)
        bg_group.addButton(self.radio_png)
        
        layout.addWidget(self.radio_pdf)
        layout.addWidget(self.radio_png)
        
        layout.addSpacing(20)
        
        # --- ボタン ---
        btn_layout = QHBoxLayout()
        btn_export = QPushButton("エクスポート")
        btn_export.clicked.connect(self.accept)
        btn_cancel = QPushButton("キャンセル")
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_export)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def get_options(self) -> dict:
        """エクスポート設定の選択内容を辞書で返す"""
        return {
            "layout": self.chk_layout.isChecked(),
            "dmx_map": self.chk_dmx_map.isChecked(),
            "dmx_list": self.chk_dmx_list.isChecked(),
            "pwr_map": self.chk_pwr_map.isChecked(),
            "pwr_list": self.chk_pwr_list.isChecked(),
            "format": "pdf" if self.radio_pdf.isChecked() else "png"
        }

if __name__ == "__main__":
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())