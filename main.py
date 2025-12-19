import sys
import os
import json
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QDockWidget, QWidget, QTreeWidget,
    QFormLayout, QLineEdit, QLabel, QComboBox, QHBoxLayout,
    QSpinBox, QCheckBox, QPushButton, QGraphicsScene, QFileDialog,
    QMessageBox, QTreeWidgetItem, QToolBar, QColorDialog, QMenu,
    QDialog
)
from PySide6.QtCore import Qt, QPointF, QRectF, QSize
from PySide6.QtGui import (
    QColor, QKeySequence, QAction, QActionGroup, QUndoStack,
    QPixmap, QCloseEvent, QPainter, QPageSize, QPageLayout,
    QImage, QTextDocument
)

# 分割したファイルのインポート
import constants
from items import EquipmentItem, OutletItem, WiringItem, VenueItem
from views import CustomGraphicsView
from commands import (
    CommandChangeProperty, CommandChangeTextColor, CommandChangeZValue,
    CommandMoveItems # 必要に応じて
)
from dialogs import (
    EquipmentManagerDialog, VenueManagerDialog, PatchWindow,
    PowerReportDialog, ExportDialog, TablePreviewDialog
)

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
            
            # --- DMX関連の処理 ---
            # ※ Undoコマンド化は複雑なため、ここでは直接値を適用
            elif sender is self.combo_dmx_mode:
                new_mode = self.combo_dmx_mode.currentText()
                for item in selected_items:
                    if item.has_dmx and item.dmx_mode_name != new_mode:
                        item.dmx_mode_name = new_mode
                        item.updateDmxText() # 表示更新
                        # Undo実装時はここで Command を push する
            
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
        self.equipment_file = constants.LIBRARY_FILE
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
                    alt_path = os.path.join(constants.DATA_DIR, img_path)
                    if os.path.exists(alt_path):
                        img_path = alt_path
                    else:
                        name_only = os.path.basename(img_path)
                        alt_path_2 = os.path.join(constants.IMAGES_DIR, name_only)
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

if __name__ == "__main__":
    constants.ensure_data_directories()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())