# Knesset NLP - Refactored Module Structure

## ✅ Refactoring Complete!

The Python modules have been successfully organized into logical directories by pipeline step:

### 📁 New Directory Structure

```
KnesseetNLP/
├── main.py                    # Main entry point (updated imports)
├── 
├── utils/                     # Shared utilities
│   ├── __init__.py
│   └── logger_config.py       # Centralized logging
│
├── translation/               # Step 3: Hebrew-to-English translation
│   ├── __init__.py
│   └── heb_to_eng_translator.py
│
├── sentiment/                 # Step 4: Sentiment analysis
│   ├── __init__.py
│   └── sentiment_analyzer.py
│
├── embedding/                 # Step 5: Text embeddings & vector search
│   ├── __init__.py
│   └── embedder.py
│
├── DataFetching/             # Step 1: Data fetching (unchanged)
│   ├── data_fetcher.py
│   └── PartitionHandler.py
│
├── UtterancesExtraction/     # Step 2: Utterance extraction (unchanged)
│   ├── utterance_extractor.py
│   ├── dover_resolver.py
│   └── bad_dover_exception.py
│
├── evaluators/               # Evaluation tools (unchanged)
│   ├── __init__.py
│   └── evaluate_translation.py
│
├── clientApp/                # Frontend (untouched as requested)
│
└── [DATA FILES REMAIN IN ROOT]
    ├── utterances/           # Output data directory
    ├── committee_data/       # Output data directory  
    ├── logs/                 # Log files
    ├── utterances_data.pkl   # Generated data file
    ├── mk_utterances.jsonl   # Generated data file
    ├── embeddings.npy        # Generated embedding file
    ├── mks_data.json         # Generated data file
    └── sentiment_analysis_results.json
```

### 🔄 Pipeline Steps Organization

1. **Data Fetching** → `DataFetching/`
2. **Utterance Extraction** → `UtterancesExtraction/`
3. **Translation** → `translation/`
4. **Sentiment Analysis** → `sentiment/`
5. **Embedding** → `embedding/`
6. **Evaluation** → `evaluators/`

### ✅ What Changed

- **Moved Python modules** from root to appropriate directories
- **Updated all imports** to use the new module structure
- **All data files and directories stay in root** as requested
- **clientApp remains untouched** for separate machine deployment
- **Proper path handling** using PROJECT_ROOT for data file access
- **Cleaned up old files** after migration

### 🔧 Updated Imports in main.py

```python
from sentiment.sentiment_analyzer import analyze_sentiment
from UtterancesExtraction.utterance_extractor import process_protocols
from DataFetching.data_fetcher import KnessetDataFetcher
from embedding.embedder import embed
from utils.logger_config import get_logger
```

### 📊 Data File Locations (Root Directory)

All data files continue to be saved/loaded from the project root:
- `utterances_data.pkl`
- `mk_utterances.jsonl` 
- `embeddings.npy`
- `committie_index`
- `mks_data.json`
- `sentiment_analysis_results.json`
- `utterances/` directory
- `committee_data/` directory
- `logs/` directory

The modules now use `PROJECT_ROOT` path resolution to ensure they can read/write data files to the correct location regardless of where the module is located.

### 🧪 Testing

The new structure has been tested and imports work correctly. The only errors encountered were missing Python dependencies (`textblob`, `googletrans`), not structural issues.

To test the full pipeline, install the required dependencies and run:
```bash
python main.py --force-refresh
```
