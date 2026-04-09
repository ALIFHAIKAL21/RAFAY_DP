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

# EVENT CLASSIFIER PATHS
EVENT_RAW_LABEL_STUDIO = Path(
    os.getenv(
        "EVENT_RAW_LABEL_STUDIO_PATH",
        str(CHAT_RAW_DIR / "tahap2" / "export_label_studio_tahap.2.json"),
    )
)
EVENT_TRAIN_DATA = Path(
    os.getenv(
        "EVENT_TRAIN_DATA_PATH",
        str(CHAT_PROCESSED_DIR / "tahap2" / "intent_event_dataset.json"),
    )
)
EVENT_OUTPUT_DIR = Path(
    os.getenv("EVENT_OUTPUT_DIR_PATH", str(MODEL_DIR / "indobert_event_classifier"))
)
EVENT_MODEL_CHECKPOINT = os.getenv(
    "EVENT_MODEL_CHECKPOINT", "indobenchmark/indobert-base-p2"
)

# HYPERPARAMETERS 
BATCH_SIZE = 8
EPOCHS = 5
LEARNING_RATE = 2e-5
MAX_SEQ_LEN = 128

# EVENT CLASSIFIER HYPERPARAMETERS
EVENT_BATCH_SIZE = int(os.getenv("EVENT_BATCH_SIZE", "8"))
EVENT_EPOCHS = int(os.getenv("EVENT_EPOCHS", "4"))
EVENT_LEARNING_RATE = float(os.getenv("EVENT_LEARNING_RATE", "2e-5"))
EVENT_MAX_SEQ_LEN = int(os.getenv("EVENT_MAX_SEQ_LEN", "256"))

# REVISION MATCHER PATHS
REVISION_MATCH_TRAIN_DATA = Path(
    os.getenv(
        "REVISION_MATCH_TRAIN_DATA_PATH",
        str(CHAT_PROCESSED_DIR / "tahap2" / "revision_matcher_dataset.json"),
    )
)
REVISION_MATCH_OUTPUT_DIR = Path(
    os.getenv(
        "REVISION_MATCH_OUTPUT_DIR_PATH",
        str(MODEL_DIR / "indobert_revision_matcher"),
    )
)
REVISION_MATCH_MODEL_CHECKPOINT = os.getenv(
    "REVISION_MATCH_MODEL_CHECKPOINT",
    "indobenchmark/indobert-base-p2",
)

# REVISION MATCHER HYPERPARAMETERS
REVISION_MATCH_BATCH_SIZE = int(os.getenv("REVISION_MATCH_BATCH_SIZE", "8"))
REVISION_MATCH_EPOCHS = int(os.getenv("REVISION_MATCH_EPOCHS", "4"))
REVISION_MATCH_LEARNING_RATE = float(os.getenv("REVISION_MATCH_LEARNING_RATE", "2e-5"))
REVISION_MATCH_MAX_SEQ_LEN = int(os.getenv("REVISION_MATCH_MAX_SEQ_LEN", "256"))
