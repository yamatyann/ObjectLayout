from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsPathItem, QGraphicsRectItem, QTreeWidget
)
from PySide6.QtCore import Qt, Signal, QRectF, QPointF, QSize, QTimer, QRect, QEvent
from PySide6.QtGui import (
    QPainter, QPen, QColor, QMouseEvent, QPainterPath, QCursor, QWheelEvent,
    QKeyEvent, QUndoStack, QFontMetrics
)

import constants
from items import EquipmentItem, WiringItem, VenueItem, VenueOutletItem, OutletItem
from commands import (
    CommandAddItems, CommandRemoveItems, CommandRotateItems,
    VenueDeleteCommand, VenueAddCommand, VenueAddOutletCommand
)

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
        self.grid_size = int(constants.DEFAULT_GRID_SIZE)  # グリッド間隔
        self._wiring_start_item = None  # 配線開始アイテム
        self._wiring_preview_path = None  # 配線プレビュー用パス
        self._snap_targets = []  # スナップ対象リスト
        self._snap_radius = constants.SNAP_DISTANCE_MOUSE  # スナップ判定半径
        self._current_wiring_points = []  # 現在の配線経路
        self._current_preview_points = []  # プレビュー用経路
        self._wiring_direction_priority = "horizontal"  # 配線の優先方向
        
        # Shiftキーによる軸固定用
        self._locked_axis = None # "horizontal" or "vertical" or None
        
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
        base_step = constants.DEFAULT_GRID_SIZE
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
            
        # 操作モード切替時にWiringItemのshapeキャッシュを破棄し、再計算させる
        if self.scene():
            for item in self.scene().items():
                if isinstance(item, WiringItem):
                    item.prepareGeometryChange()
    
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """マウス押下イベント処理"""
        if event.button() == Qt.RightButton:
            is_wiring_mode = self._interaction_mode.startswith("wiring_") and self._interaction_mode != "wiring_delete"
            if is_wiring_mode:
                if self._current_wiring_points:
                    # 中間点がある場合は一つ戻る
                    self._current_wiring_points.pop()
                    # プレビュー更新のためにマウス移動イベントを偽装発火
                    cursor_pos = self.mapFromGlobal(QCursor.pos())
                    fake_event = QMouseEvent(QEvent.Type.MouseMove, cursor_pos, Qt.MouseButton.NoButton, Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier)
                    self.mouseMoveEvent(fake_event)
                elif self._wiring_start_item:
                    # 中間点がない場合はキャンセル
                    self._cancel_wiring()
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
                    self._wiring_preview_path.setZValue(constants.Z_VAL_PREVIEW)
                    pen = QPen(QColor("white"), 1, Qt.DotLine)
                    self._wiring_preview_path.setPen(pen)
                    self.scene().addItem(self._wiring_preview_path)
                    
                    self._snap_targets = []
                    for item in self.scene().items():
                        if isinstance(item, (EquipmentItem, OutletItem)) and item != self._wiring_start_item:
                            self._snap_targets.append(item)
            else:
                self._current_wiring_points.extend(self._current_preview_points)
                # 直線上の冗長な点を削除
                if len(self._current_wiring_points) >= 2:
                    p1 = self._current_wiring_points[-2]
                    p2 = self._current_wiring_points[-1]
                    if len(self._current_wiring_points) == 2:
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
    
    def _add_wire_async(self, start_item: 'EquipmentItem', end_item: 'EquipmentItem', points: list, wire_type: str = "dmx") -> None:
        """非同期で配線アイテムを追加"""
        print("タイマーで WiringItem を追加")
        wire = WiringItem(start_item, end_item, points, wire_type=wire_type) 
        wire.setData(0, {"type": "wire"}) 
        wire.setZValue(constants.Z_VAL_WIRE)
        
        command = CommandAddItems(wire, self.scene(), "配線の追加")
        if self.mainWindow and self.mainWindow.undoStack:
             self.mainWindow.undoStack.push(command)
        else:
             print("エラー: undoStack が見つかりません。")
             self.scene().addItem(wire)
    
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
                    # A: スナップする場合（終点処理）
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
                    # B: スナップしない場合（中間点処理）
                    dx = current_pos_scene.x() - last_pos.x()
                    dy = current_pos_scene.y() - last_pos.y()
                    
                    # Shiftキーによる軸固定ロジック
                    is_shift_pressed = event.modifiers() & Qt.ShiftModifier
                    
                    if not is_shift_pressed:
                        self._locked_axis = None # Shift離したらロック解除
                    
                    # ロック軸の決定（Shift押下中で未決定なら、現在の移動量で決定）
                    if is_shift_pressed and self._locked_axis is None:
                         self._locked_axis = "horizontal" if abs(dx) >= abs(dy) else "vertical"
                    
                    # 軸判定
                    is_horizontal = False
                    if self._locked_axis:
                        is_horizontal = (self._locked_axis == "horizontal")
                    else:
                        is_horizontal = (abs(dx) > abs(dy))
                    
                    if is_horizontal:
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
            self.scene().addItem(equipment_item)
        event.acceptProposedAction()
    
    def wheelEvent(self, event: QEvent) -> None:
        """マウスホイールイベント処理"""
        if self._r_key_is_pressed:
            selected_items = [item for item in self.scene().selectedItems() if isinstance(item, EquipmentItem)]
            if not selected_items: return
            
            delta = 1.5 if event.angleDelta().y() > 0 else -1.5
            
            items_with_rot = []
            for item in selected_items:
                old_rot = item.rotation()
                new_rot = (old_rot + delta) % 360
                items_with_rot.append((item, old_rot, new_rot))
            
            if items_with_rot and self.mainWindow and self.mainWindow.undoStack:
                cmd = CommandRotateItems(items_with_rot, "アイテムの回転")
                self.mainWindow.undoStack.push(cmd)
            
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
        # Escキーで配線を一括キャンセル
        if event.key() == Qt.Key_Escape:
            if self._interaction_mode.startswith("wiring_"):
                self._cancel_wiring()
            # カーソルモードなら選択解除などの標準動作に任せる
            else:
                super().keyPressEvent(event)
            return
        
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
                fake_event = QMouseEvent(QEvent.Type.MouseMove, cursor_pos, Qt.MouseButton.NoButton, Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier)
                self.mouseMoveEvent(fake_event)
        elif event.key() == Qt.Key_Delete:
            selected_items = self.scene().selectedItems()
            if selected_items:
                command = CommandRemoveItems(selected_items, self.scene(), "アイテムの削除")
                self.mainWindow.undoStack.push(command)
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
        self._snap_targets = []
        self._locked_axis = None # ロック解除
    
    def _get_target_item_at(self, pos: QPointF) -> object:
        """指定座標にある配線可能なアイテムを返す"""
        rect = QRect(pos - QPointF(5, 5).toPoint(), QSize(10, 10))
        items = self.items(rect)
        
        for item in items:
            temp = item
            while temp:
                if isinstance(temp, (EquipmentItem, OutletItem)):
                    return temp
                temp = temp.parentItem()
        return None

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
        self._outlet_preview_item.setZValue(constants.Z_VAL_PREVIEW)
        self._outlet_preview_item.setVisible(False)
        scene.addItem(self._outlet_preview_item)
        self._direction_priority = "horizontal"
        self.show_grid = True
        self.grid_size = int(constants.DEFAULT_GRID_SIZE)
    
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
            snap_unit = constants.DEFAULT_GRID_SIZE
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
            snap_unit = constants.DEFAULT_GRID_SIZE
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
            snap_unit = constants.DEFAULT_GRID_SIZE
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
