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



## Data

Raw participant data are not included in this public repository.

Place Gorilla Excel exports in:

data/raw/


Place the counterbalancing workbook in:

data/counterbalancing/Counterbalancing.xlsx


## Running the analysis

From the repository folder, run:

python pocket_tnt_preprocessing.py

The processed dataset will be saved to:

outputs/Pocket_TNT_combined.xlsx

## Requirements

- Python 3.10+
- pandas
- openpyxl

