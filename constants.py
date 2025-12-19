import os

# ディレクトリ設定
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
IMAGES_DIR = os.path.join(DATA_DIR, "images")
VENUES_DIR = os.path.join(DATA_DIR, "venues")
LIBRARY_FILE = os.path.join(DATA_DIR, "equipment_library.json")

# 定数定義
Z_VAL_PREVIEW         = 100.0
Z_VAL_EQUIPMENT_FRONT = 30.0
Z_VAL_EQUIPMENT_STD   = 25.0
Z_VAL_EQUIPMENT_BACK  = 20.0
Z_VAL_OUTLET          = 15.0
Z_VAL_WIRE            = 10.0
Z_VAL_VENUE           = -10.0

DEFAULT_GRID_SIZE     = 50.0
SNAP_DISTANCE_MOUSE   = 15.0
SNAP_THRESHOLD_ITEM   = 20.0

# ディレクトリ作成関数
def ensure_data_directories():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"Created data directory: {DATA_DIR}")
    if not os.path.exists(IMAGES_DIR):
        os.makedirs(IMAGES_DIR)
        print(f"Created images directory: {IMAGES_DIR}")
    if not os.path.exists(VENUES_DIR):
        os.makedirs(VENUES_DIR)
        print(f"Created venues directory: {VENUES_DIR}")