# Speech-to-Text Data Preparation - Uzbek Voice

## Dataset Description
- **Source:** Custom scraped using data/create_data.py
- **Size:** 206 audio samples
- **Format:** WAV, mono, 16kHz
- **Duration:** 2-6 seconds per sample
- **Language:** Uzbek

## Installation
```bash
pip install -r requirement.txt
```

## Usage
```bash
jupyter notebook eda.ipynb
```

## Project Structure
```
├── data/
│   ├── audio/          # Audio files
│   ├── metadata.csv    # Transcriptions
│   ├── create_data.py  # Scraping script
│   ├── X_train.npy
│   ├── X_val.npy
│   └── X_test.npy
├── eda.ipynb          # Main analysis notebook
└── requirement.txt
```

## Features Extracted
- MFCCs (13 coefficients)
- Fixed length: 300 frames
- Train/Val/Test: 70/15/15 split

## Insights from EDA
1. Average audio duration: 3.3s (±0.58s)
2. Most frequent words: "kerak", "qilish", "bilan"
3. Natural conversational style

## Challenges & Solutions
- **Challenge:** Variable audio lengths
- **Solution:** Implemented padding/truncation to 300 frames

## Next Steps
- Train baseline STT model
- Experiment with data augmentation
- Test on real-world samples