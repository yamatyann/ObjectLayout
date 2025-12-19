from PySide6.QtGui import QUndoCommand, QColor
from PySide6.QtWidgets import QGraphicsItem, QGraphicsScene, QMainWindow
from PySide6.QtCore import QPointF

# 型ヒントの循環参照回避のため
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from items import EquipmentItem, WiringItem, OutletItem, VenueItem, VenueOutletItem

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
        from items import EquipmentItem, WiringItem
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
        from items import EquipmentItem, OutletItem
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
