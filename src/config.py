import os
from pathlib import Path

# BASE DIRECTORY 
# mendeteksi lokasi file config.py
BASE_DIR = Path(__file__).resolve().parent.parent

# DATA PATHS 
DATA_DIR = BASE_DIR / "data"

# Chat Paths
CHAT_DIR = DATA_DIR / "chat"
CHAT_RAW_DIR = CHAT_DIR / "raw"
CHAT_PROCESSED_DIR = CHAT_DIR / "processed"

# Input/Output Files
# File input untuk cleaner (hasil convert)
TRAIN_DATA_UNCLEAN = Path(
    os.getenv("TRAIN_DATA_UNCLEAN_PATH", str(CHAT_PROCESSED_DIR / "data_siap_training.json"))
)
# File output cleaner (siap training)
TRAIN_DATA_CLEAN = Path(
    os.getenv("TRAIN_DATA_CLEAN_PATH", str(CHAT_PROCESSED_DIR / "data_augmented.json"))
)
# File Label Studio asli
RAW_LABEL_STUDIO = Path(
    os.getenv("RAW_LABEL_STUDIO_PATH", str(CHAT_RAW_DIR / "export_label_studio.json"))
)

# MODEL PATHS
MODEL_DIR = BASE_DIR / "models"
BERT_OUTPUT_DIR = Path(
    os.getenv("BERT_OUTPUT_DIR_PATH", str(MODEL_DIR / "indobert_finetuned"))
)

# HYPERPARAMETERS 
BATCH_SIZE = 8
EPOCHS = 5
LEARNING_RATE = 2e-5
MAX_SEQ_LEN = 128
