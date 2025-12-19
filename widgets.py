import os
from PySide6.QtWidgets import (
    QWidget, QTableWidget, QHeaderView, QTableWidgetItem, QMenu,
    QAbstractItemView
)
from PySide6.QtCore import Qt, Signal, QPoint, QRect, QPointF
from PySide6.QtGui import QPainter, QColor, QPen, QPixmap, QMouseEvent, QPainterPath, QPaintEvent, QAction, QCursor

# 定数ファイルからインポート
from constants import DATA_DIR

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

