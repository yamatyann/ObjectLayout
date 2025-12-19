import os
import copy
import uuid
import shutil
import glob
import json

from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QTreeWidget,
    QPushButton, QFormLayout, QTabWidget, QSpinBox, QCheckBox, QLabel,
    QComboBox, QTableWidget, QHeaderView, QTableWidgetItem, QTreeWidgetItem,
    QFileDialog, QMessageBox, QProgressDialog, QAbstractItemView,
    QStackedWidget, QListWidget, QListWidgetItem, QGraphicsScene,
    QRadioButton, QButtonGroup, QDoubleSpinBox,
    QApplication
)
from PySide6.QtCore import Qt, QSize, QTimer, QPoint, QRectF, QPointF
from PySide6.QtGui import (
    QPixmap, QColor, QPen, QPainter, QPageSize, QPageLayout,
    QTextDocument, QImage, QFont, QCloseEvent, QUndoStack, QKeySequence
)
from PySide6.QtPrintSupport import QPrinter

import constants
from widgets import SnapPreviewWidget, NumericTableWidgetItem, FilterHeaderView, AdvancedTableWidget
from items import EquipmentItem, VenueItem, VenueOutletItem, WiringItem, OutletItem
from views import VenueEditorView


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
        self.image_path_edit.textChanged.connect(lambda: (self._on_form_edited(), self._update_preview()))
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
            alt_path = os.path.join(constants.DATA_DIR, current_image_path)
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
        images_dir = constants.IMAGES_DIR
        abs_images_dir = os.path.abspath(images_dir)
        
        # imagesフォルダ作成
        if not os.path.exists(images_dir):
            os.makedirs(images_dir)
        
        # ■ 修正点1: normcaseを使ってパスの区切り文字や大文字小文字を正規化して比較
        is_inside_images = os.path.normcase(abs_file_path).startswith(os.path.normcase(abs_images_dir))
        
        if is_inside_images:
            # imagesフォルダ内の場合、相対パスとして保存
            try:
                # dataフォルダを基準とした相対パスにするのが扱いやすい
                relative_path = os.path.relpath(file_path, constants.DATA_DIR).replace("\\", "/")
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
                
                # ■ 修正点2: コピー元と先が同じファイルでないか確認
                if os.path.normcase(abs_file_path) == os.path.normcase(os.path.abspath(dest_path)):
                     # 同じ場所ならコピーせず、そのままパスを設定
                     try:
                        relative_path = os.path.relpath(dest_path, constants.DATA_DIR).replace("\\", "/")
                        self.image_path_edit.setText(relative_path)
                     except ValueError:
                        self.image_path_edit.setText(dest_path)
                     QMessageBox.information(self, "完了", "画像は既にimagesフォルダ内にあります。")
                     return

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
                        relative_path = os.path.relpath(dest_path, constants.DATA_DIR).replace("\\", "/")
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
        
        toolbar_layout.addWidget(self.btn_edit)
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
        self.venue_dir = constants.VENUES_DIR
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
