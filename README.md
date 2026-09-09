# Pocket TNT Data Processing

Python preprocessing pipeline for the Pocket Think/No-Think (Pocket TNT) study, which is a test battery which quantifies memory control.

## Overview

This repository contains code used to preprocess Pocket TNT behavioral data exported from Gorilla.

The pipeline:

- loads Gorilla Excel exports,
- extracts rating-scale trials,
- merges responses with the relevant counterbalancing sheet,
- converts intrusion ratings into binary scores,
- calculates mean intrusion rates by condition and repetition,
- reshapes the data to participant-level wide format,
- combines datasets across counterbalancing conditions, and
- exports the final processed dataset.

## Repository structure

```text
pocket-tnt-analysis/
│
├── pocket_tnt_preprocessing.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── data/
│   ├── raw/
│   └── counterbalancing/
│
└── outputs/
```

## Installation

Clone the repository and install the required Python packages:

```bash
pip install -r requirements.txt
```

## Data

Raw participant data are not included in this public repository.

Place Gorilla Excel exports in:

```text
data/raw/
```

Place the counterbalancing workbook in:

```text
data/counterbalancing/Counterbalancing.xlsx
```

## Running the analysis

From the repository folder, run:

```bash
python pocket_tnt_preprocessing.py
```

The processed dataset will be saved to:

```text
outputs/Pocket_TNT_combined.xlsx
```

## Requirements

- Python 3.10+
- pandas
- openpyxl

## Author

Ketaki Sengupta
