import subprocess
import time
from pathlib import Path
from PIL import Image, ImageTk, ImageDraw, ImageGrab
import json
import os
import tkinter as tk
from tkinter import messagebox, filedialog
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.lib import fonts
from reportlab.pdfbase.ttfonts import TTFont

font_path = Path(os.path.dirname(__file__), "yumin.ttf")
pdfmetrics.registerFont(TTFont('Yumin', font_path))

# processingのパスを指定
# processing_exe_path = Path(os.path.dirname(os.path.abspath(__file__)), "..", "..", "processing")
processing_exe_path = Path(os.path.dirname(os.path.abspath(__file__)), "processing")

# 処理の実行をsubprocess.Popenで行い、標準出力をキャプチャする
process = subprocess.Popen([processing_exe_path / "setuzokuzu.exe"], cwd=processing_exe_path,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

# 標準出力をリアルタイムで読み取る
output = ""
for line in process.stdout:
    output += line
    print(line.strip())  # デバッグ用に出力を確認

# プロセスが終了するまで待機
process.wait()

# 標準出力の中に`true`か`false`が含まれているかを確認
if "true" in output:
    print("Processingからの出力: 表を作成するように指定されました。")
    
    # 画像とJSONファイルのパス
    base_path = processing_exe_path  # ここでprocessing_exe_pathと一致させる
    image_path = base_path / "image.png"
    json_file_path = base_path / "project_data.json"

    # ファイルの存在確認
    if image_path.exists() and json_file_path.exists():
        # 表の作成処理へ移行
        print("image.png と project_data.json が存在します。表の作成に移行します。")
        
        # JSONファイルの読み込み
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

                # 灯体のリスト
        lighting_info = [
            {"name": "led", "nickname": "LED", "formal_name": "LEDPAR64"},
            {"name": "mega64", "nickname": "MEGA64", "formal_name": "Mega 64 Profile Plus"},
            {"name": "moving", "nickname": "ムービング", "formal_name": "4 in 1 LED Moving Head Zoom Wash Light"},
            {"name": "par12", "nickname": "par12", "formal_name": "LEDPAR12"},
            {"name": "strobe", "nickname": "ストロボ", "formal_name": "Mega Flash DMX"},
            {"name": "dekker", "nickname": "デッカー", "formal_name": "Mini Dekker"},
            {"name": "oldColorbar", "nickname": "旧カラーバー", "formal_name": "COLORBAR LED II"},
            {"name": "newColorbar", "nickname": "新カラーバー", "formal_name": "Mega Bar RGBA"},
            {"name": "phantom", "nickname": "ファントム", "formal_name": "Phantom2048"},
            {"name": "sceneSetter", "nickname": "シーンセッター", "formal_name": "SCENE SETTER"},
            {"name": "miniDesk", "nickname": "ミニ卓", "formal_name": "MC6"},
            {"name": "ePar38", "nickname": "ePar38", "formal_name": "ePar38"},
            {"name": "led38B", "nickname": "LED38B", "formal_name": "38B LED PRO"},
            {"name": "flatPar", "nickname": "フラットパー", "formal_name": "FLAT PAR TRI7X"},
            {"name": "bk75", "nickname": "bk75", "formal_name": "bk-75-jo"},
            {"name": "par20", "nickname": "par20", "formal_name": "PAR 20"},
            {"name": "par30", "nickname": "par30", "formal_name": "PAR 30"},
            {"name": "par46", "nickname": "par46", "formal_name": "PAR 46"},
            {"name": "bold", "nickname": "ボールド", "formal_name": "BOLD"},
            {"name": "dimmerPack", "nickname": "ディマーパック", "formal_name": "DPDMX20L"},
            {"name": "stand", "nickname": "スタンド", "formal_name": "LS2 照明用スタンド"},
            {"name": "truss", "nickname": "トラス", "formal_name": "Lsibeam"}
        ]

        # ケーブルの長さを色で判定する辞書
        color_to_length = {
            -65536: "1m",
            -3669761: "2m",
            -16711681: "3m",
            -32256: "5m",
            -16711936: "10m",
            -16776961: "15m"
        }

        # 表の作成処理
        # 灯体の数を数える
        def count_lighting_objects(data):
            lighting_counts = {}

            for obj_info in lighting_info:
                obj_name = obj_info["name"]
                if obj_name in data:
                    count = data[obj_name] - 1  # 実際の数は1引いた値
                    if count > 0:
                        lighting_counts[obj_name] = count
                    else:
                        lighting_counts[obj_name] = 0
                else:
                    lighting_counts[obj_name] = 0

            return lighting_counts

        # メインGUIの構築
        root = tk.Tk()
        root.attributes("-topmost", True)
        root.title("照明設定表")
        root.geometry("1200x700")  # ウィンドウサイズの設定
        
        subject_list = []

        # 団体名、会場、控室の入力欄を作成
                # 団体名、会場、控室の入力欄
        def create_text_entries(root):
            tk.Label(root, text="団体名:　　").grid(row=0, column=0, sticky="w")
            group = tk.Entry(root, width=20)
            group.grid(row=0, column=1, sticky="w")
            subject_list.append(group)            

            tk.Label(root, text="会場:").grid(row=1, column=0, sticky="w")
            room = tk.Entry(root, width=20)
            room.grid(row=1, column=1, sticky="w")
            subject_list.append(room)

            tk.Label(root, text="控室:").grid(row=2, column=0, sticky="w")
            rest = tk.Entry(root, width=20)
            rest.grid(row=2, column=1, sticky="w")
            subject_list.append(rest)

        subject_table_frame = tk.Frame(root)
        subject_table_frame.grid(row=0, column=0, sticky="nsew")
        create_text_entries(subject_table_frame)

        # 画像エリア (image.png)
        img = Image.open(image_path)
        img = img.resize((400, 300))  # サイズ調整
        img_tk = ImageTk.PhotoImage(img)
        tk.Label(root, image=img_tk).grid(row=3, column=0, padx=10, pady=10)

        # 灯体情報を表示するエリア
        lighting_table_frame = tk.Frame(root)
        lighting_table_frame.grid(row=4, column=0, sticky="nsew")

        labels = []
        lighting_counts = count_lighting_objects(data)

        entries = []

        # 名前を更新する関数
        def update_names():
            ix = 1
            for i, obj_info in enumerate(lighting_info):
                # カウントが0より大きい場合にのみ表示
                if lighting_counts[obj_info["name"]] > 0:
                    entry_name = tk.Entry(lighting_table_frame, width=20)
                    entry_name.insert(0, obj_info["nickname"] if use_nickname.get() else obj_info["formal_name"])
                    entry_name.grid(row=ix, column=1, sticky="w")  # 名前のテキストボックスを配置
                    ix = ix + 1

        # トグルボタンの作成
        use_nickname = tk.BooleanVar(value=True)
        toggle_button = tk.Checkbutton(subject_table_frame, text="俗称/正式名称 切り替え", width=35, variable=use_nickname, command=update_names)
        toggle_button.grid(row=0, column=2, sticky="w")

        name_entries = []
        count_entries = []
        sch_entries = []
        chmode_entries = []


        # 灯体ごとに情報を表示
        tk.Label(lighting_table_frame, text="　　").grid(row=0, column=0)
        tk.Label(lighting_table_frame, text="名称").grid(row=0, column=1)
        tk.Label(lighting_table_frame, text="数").grid(row=0, column=2)
        tk.Label(lighting_table_frame, text="起点ch").grid(row=0, column=3)
        tk.Label(lighting_table_frame, text="ch(モード)").grid(row=0, column=4)

        row = 1
        for index, obj_info in enumerate(lighting_info):
            
            # カウントが0より大きい場合にのみ表示
            if lighting_counts[obj_info["name"]] > 0:

                # 画像パスの設定
                object_image_path = os.path.join(os.path.dirname(__file__), "..", "ObjectList", f"{obj_info['name']}.png")

                # 画像の表示
                if os.path.exists(object_image_path):
                    object_img = Image.open(object_image_path)
                    object_img = object_img.resize((object_img.width // 2, object_img.height // 2))
                    object_img_tk = ImageTk.PhotoImage(object_img)
                    label_img = tk.Label(lighting_table_frame, image=object_img_tk)
                    label_img.image = object_img_tk
                    label_img.grid(row=row, column=0)
                else:
                    print(f"警告: 画像が見つかりません - {object_image_path}")
                    

                # 俗称か正式名称かを保持するための変数を設定
                name_var = tk.StringVar(value=obj_info["nickname"] if use_nickname.get() else obj_info["formal_name"])
            
                # テキストボックス (Entry) を作成し、ユーザーが名前を書き換え可能に
                entry_name = tk.Entry(lighting_table_frame, width=20)
                entry_name.insert(0, obj_info["nickname"] if use_nickname.get() else obj_info["formal_name"])
                name_entries.append(entry_name)  # テキストボックスをリストに追加して保持

                # 照明のカウントを編集可能にするための変数を設定
                count_var = tk.StringVar(value=str(lighting_counts[obj_info["name"]]))
                entry_count = tk.Entry(lighting_table_frame, textvariable=count_var, width=5)  # カウント用のテキストボックス
                count_entries.append(entry_count)

                # 起点ch用のテキストボックスを作成
                entry_sch = tk.Entry(lighting_table_frame, width=8)
                sch_entries.append(entry_sch)

                # chモード用のテキストボックスを作成
                entry_chmode = tk.Entry(lighting_table_frame, width=10)
                chmode_entries.append(entry_chmode)

                entry_name.grid(row=row, column=1, sticky="w")  # 名前のテキストボックスを配置
                entry_count.grid(row=row, column=2)  # カウントのテキストボックスを配置
                entry_sch.grid(row=row, column=3)
                entry_chmode.grid(row=row, column=4)
                row = row + 1

        tk.Label(lighting_table_frame, text="　　").grid(row=0, column=5)
        tk.Label(lighting_table_frame, text="DMX色").grid(row=0, column=6)
        tk.Label(lighting_table_frame, text="長さ").grid(row=0, column=7)
        tk.Label(lighting_table_frame, text="本数").grid(row=0, column=8)

        # ケーブルの長さを数える
        cable_lengths = {}
        
        for line_type in ["justLine", "lLine", "bracketLine"]:
            # lineの数を確認
            if line_type in data:
                line_count = data[line_type] - (2 if line_type == "bracketLine" else 1)
                
                for i in range(1, line_count + 1):
                    key = f"{line_type}C{i}"
                    if key in data:
                        color = data[key]
                        if color in color_to_length:
                            length = color_to_length[color]
                            if length in cable_lengths:
                                cable_lengths[length] += 1
                            else:
                                cable_lengths[length] = 1
        
        # 結果を表示
        print("\n必要なケーブル:")
        for length, count in cable_lengths.items():
            print(f"{length}: {count} 本")

        # ケーブルデータ
        dmx_data = []
        if "1m" in cable_lengths:
            dmx_data.append({"color": "赤", "length": "1m", "count": cable_lengths["1m"]})
        if "2m" in cable_lengths:
            dmx_data.append({"color": "紫", "length": "2m", "count": cable_lengths["2m"]})
        if "3m" in cable_lengths:
            dmx_data.append({"color": "水", "length": "3m", "count": cable_lengths["3m"]})
        if "5m" in cable_lengths:
            dmx_data.append({"color": "橙", "length": "5m", "count": cable_lengths["5m"]})
        if "10m" in cable_lengths:
            dmx_data.append({"color": "緑", "length": "10m", "count": cable_lengths["10m"]})
        if "15m" in cable_lengths:
            dmx_data.append({"color": "青", "length": "15m", "count": cable_lengths["15m"]})

        dmx_color_list = []
        dmx_length_list = []
        dmx_count_list = []

        # DMX表にデータを挿入
        for idx, dmx in enumerate(dmx_data, start=1):
            entry = tk.Entry(lighting_table_frame, width=10)
            entry.insert(0, dmx["color"])
            entry.grid(row=idx, column=6)
            dmx_color_list.append(entry)

            entry = tk.Entry(lighting_table_frame, width=10)
            entry.insert(0, dmx["length"])
            entry.grid(row=idx, column=7)
            dmx_length_list.append(entry)

            entry = tk.Entry(lighting_table_frame, width=10)
            entry.insert(0, dmx["count"])
            entry.grid(row=idx, column=8)
            dmx_count_list.append(entry)
        # PDF出力用の関数
        def save_as_pdf():
            pdf_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
            if not pdf_path:
                return

            # PDFの初期設定（A4サイズ）
            pdf = canvas.Canvas(pdf_path, pagesize=A4)
            width, height = A4
            pdf.translate(20, height - 40)  # マージンを設定

            # 団体名、会場、控室をPDFに書き込む
            pdf.setFont('Yumin', 12)
            y_offset = 0
            for idx, entry in enumerate(subject_list):
                label = ["団体名", "会場", "控室"][idx]
                value = entry.get()
                pdf.drawString(20, y_offset, f"{label}: {value}")
                y_offset -= 20

                
            p_img = img.resize((400, 300))
            y_offset -= 30
            y_offset -= p_img.height

            img_x = round(width/2 - p_img.width/2 - 20)
            pdf.drawImage(image_path, img_x, y_offset, p_img.width, p_img.height)

            pdf.line(img_x, y_offset + p_img.height, img_x + p_img.width, y_offset + p_img.height)
            pdf.line(img_x, y_offset, img_x + p_img.width, y_offset)
            pdf.line(img_x, y_offset + p_img.height, img_x, y_offset)
            pdf.line(img_x + p_img.width, y_offset + p_img.height, img_x + p_img.width, y_offset)

            # 照明リストをPDFに書き込む
            y_offset -= 40
            pdf.drawString(20, y_offset, "　使用機材")
            n = 0
            startY = y_offset + 10
            startX = 10
            y_offset -= 20

            nameLenMax = 6
            for idx, entry_name in enumerate (name_entries):
                name = entry_name.get()
                pdf.drawString(20, y_offset, f"　 {name}")
                y_offset -= 20
                
                n += 1

                nameLen = len(name)
                if nameLenMax < nameLen:
                    nameLenMax = nameLen
            
            y_offset = startY - 30
            for idx, obj_info in enumerate (lighting_info):
                if lighting_counts[obj_info["name"]] > 0:
                    y_offset -= 20
                    if (obj_info["name"] != "stand") and (obj_info["name"] != "truss"):
                        object_image_path = os.path.join(os.path.dirname(__file__), "..", "ObjectList", f"_{obj_info['name']}.png")
                        if os.path.exists(object_image_path):
                            pdf.drawImage(object_image_path, 15, y_offset + 16, 18, 18)

            x1 = startX + 20*(nameLenMax - 1)

            y_offset = startY - 30
            
            pdf.drawString(20 * nameLenMax - 5, startY - 10, "数")
            countLenMax = 1
            for idx, entry_count in enumerate (count_entries):
                count = entry_count.get()

                countLen = len(count)

                if countLen == 1:
                    pdf.drawString(20 * nameLenMax, y_offset, f"{count}")
                else:
                    pdf.drawString(20 * nameLenMax - 5, y_offset, f"{count}")

                y_offset -= 20

            x2 = x1 + 20*countLenMax

            y_offset = startY - 30

            pdf.drawString(20 * (nameLenMax + countLenMax), startY - 10, "起点ch")
            schLenMax = 3
            for idx, entry_sch in enumerate (sch_entries):
                ch = entry_sch.get()
                pdf.drawString(20 * (nameLenMax + countLenMax + 2), y_offset, f"{ch}")
                y_offset -= 20

                schLen = len(ch)
                if schLen > 10:
                    schLenMax = 5

            x3 = x2 + 20*schLenMax

            y_offset = startY - 30

            pdf.drawString(20 * (nameLenMax + countLenMax + schLenMax), startY - 10, "chモード")
            chmodeLenMax = 3
            for idx, entry_chmode in enumerate (chmode_entries):
                ch = entry_chmode.get()
                pdf.drawString(20 * (nameLenMax + countLenMax + schLenMax + 2), y_offset, f"{ch}")
                y_offset -= 20

                chmodeLen = len(ch)
                if chmodeLen > 10:
                    chmodeLenMax = 5

            endX = x3 + 20*chmodeLenMax
            endY = startY - 20*(n + 1) + 5

            y_offset = startY - 30
            dx = width/2 + 40
            pdf.drawString(dx, startY - 10, "色")
            m = 0
            colLen = 1


            for idx, entry_color in enumerate (dmx_color_list):
                color = entry_color.get()

                pdf.drawString(dx, y_offset, f"{color}")

                y_offset -= 20

                m += 1

            y_offset = startY - 30
            pdf.drawString(dx + 20, startY - 10, " 長さ")
            colLen = 2

            for idx, entry_length in enumerate (dmx_length_list):
                length = entry_length.get()

                lengthLen = len(length)
                if lengthLen == 2:
                    pdf.drawString(dx + 20 + 10, y_offset, f"{length}")
                else:
                    pdf.drawString(dx + 20 + 5, y_offset, f"{length}")

                y_offset -= 20

            y_offset = startY - 30
            pdf.drawString(dx + 60, startY - 10, "数")
            numLen = 1

            for idx, entry_count in enumerate (dmx_count_list):
                count = entry_count.get()

                countLen = len(count)
                if countLen == 1:
                    pdf.drawString(dx + 60 + 5, y_offset, f"{count}")
                else:
                    pdf.drawString(dx + 60, y_offset, f"{count}")

                y_offset -= 20

            # 表の描画
            for row in range(n + 2):
                pdf.line(startX, startY - 20*row + 5, endX, startY - 20*row + 5)

            pdf.line(startX, startY + 5, startX, endY)
            pdf.line(x1, startY + 5, x1, endY)
            pdf.line(x2, startY + 5, x2, endY)
            pdf.line(x3, startY + 5, x3, endY)
            pdf.line(endX, startY + 5, endX, endY)

            dstartX = dx - 5
            dendY = startY - 20*(m + 1) + 5

            for row in range(m + 2):
                pdf.line(dstartX, startY - 20*row + 5, dstartX + 80, startY - 20*row + 5)

            pdf.line(dstartX, startY + 5, dstartX, dendY)
            pdf.line(dstartX + 20, startY + 5, dstartX + 20, dendY)
            pdf.line(dstartX + 60, startY + 5, dstartX + 60, dendY)
            pdf.line(dstartX + 80, startY + 5, dstartX + 80, dendY)
            
            pdf.save()
            print(f"PDF saved as {pdf_path}")

        def on_exit():
            if messagebox.askyesno("確認", "表をPDFで出力します"):
                save_as_pdf()
            else:
                print("出力をキャンセルしました。")

        # 終了ボタン
        exit_button = tk.Button(root, text="終了", command=on_exit)
        exit_button.grid(row=5, column=0)

        # メインループ開始
        root.mainloop()
        
        # ファイルの削除
        try:
            os.remove(image_path)
            os.remove(json_file_path)
            print("ファイルを削除しました。")
        except OSError as e:
            print(f"ファイル削除中にエラーが発生しました: {e}")
    else:
        print("必要なファイルが存在しません。処理を終了します。")

elif "false" in output:
    print("Processingからの出力: 表を作成しないように指定されました。処理を終了します。")
else:
    print("Processingからの出力が確認できませんでした。")