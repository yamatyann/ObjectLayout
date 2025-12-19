import os
import uuid
from PySide6.QtWidgets import (
    QGraphicsObject, QGraphicsPixmapItem, QGraphicsSimpleTextItem,
    QGraphicsItem, QGraphicsPathItem, QGraphicsRectItem, QWidget,
    QStyleOptionGraphicsItem, QStyle, QDialog, QFormLayout, QLineEdit,
    QSpinBox, QPushButton, QColorDialog, QHBoxLayout, QMessageBox,
    QGraphicsSceneMouseEvent, QGraphicsScene
)
from PySide6.QtCore import Qt, QRectF, QPointF, QLineF
from PySide6.QtGui import (
    QPixmap, QColor, QPen, QPainterPath, QPainter, QBrush,
    QFont, QPainterPathStroker
)

# 自作モジュールのインポート
import constants
# コマンドは循環参照回避のためメソッド内でインポート推奨


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
            alt_path = os.path.join(constants.DATA_DIR, img_path)
            if os.path.exists(alt_path):
                img_path = alt_path
            # 3. それでもなければ、data/images 直下を探す (ファイル名のみの場合など)
            else:
                name_only = os.path.basename(img_path)
                alt_path_2 = os.path.join(constants.IMAGES_DIR, name_only)
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
        z_val = constants.Z_VAL_EQUIPMENT_STD
        has_snaps = len(self.snap_points_data) > 0
        if self.can_be_wired: z_val = constants.Z_VAL_EQUIPMENT_FRONT
        elif has_snaps: z_val = constants.Z_VAL_EQUIPMENT_BACK
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
            
            SNAP_THRESHOLD = constants.SNAP_THRESHOLD_ITEM # 吸着する距離 (ピクセル)
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
        from commands import CommandMoveItems
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
        self.setZValue(constants.Z_VAL_OUTLET)
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
                        from commands import CommandMoveItems
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
        self.setZValue(constants.Z_VAL_WIRE)  # 線は機材より背面
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
        
        if view and type(view).__name__ == "CustomGraphicsView":
            # 「配置」モード (cursor) の時だけ、バグ防止のため当たり判定を「広く」する
            if view._interaction_mode == "cursor":
                current_stroke_width = self.guard_stroke_width
        
        stroker.setWidth(current_stroke_width)
        stroker.setCapStyle(Qt.PenCapStyle.FlatCap)
        stroker.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        shape_path = stroker.createStroke(path)
        return shape_path

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
        
        self.setZValue(constants.Z_VAL_VENUE) # 最背面
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
