"""
Pocket TNT Data Processing Pipeline

This script:
1. Loads predefined Gorilla Excel files.
2. Extracts Pocket TNT rating-scale responses.
3. Merges participant responses with the corresponding counterbalancing sheet.
4. Converts intrusion ratings into binary values.
5. Calculates mean intrusion rates for each repetition and condition.
6. Reshapes the data into one row per participant.
7. Combines all processed datasets.
8. Removes rows containing missing values.

Author: Ketaki Sengupta
"""

from pathlib import Path
import pandas as pd



DATA_PATH = Path("data/raw")
COUNTERBALANCING_FILE = Path("data/counterbalancing/Counterbalancing.xlsx")

CODES = [
    "scp3", "ca3i", "dqih", "m7tz", "sb6w", "7elq", "ibqa", "ai78",
    "5gka", "5nhp", "5huk", "9lyj", "nk7m", "43kj", "vwo5", "xhu4",
    "5k5p", "h2c3", "wufa", "a26j", "56fu", "e1w2", "yqbw", "yohe",
    "77if", "tx6j", "pni5", "4xtk", "fep6", "ryey", "xie7", "dli1",
    "wut4", "cqkq", "2cwa", "pwtn", "ewyl", "73aw", "hi1p", "j9pc"
]

REP_COLS = [f"rep{i:02d}" for i in range(1, 11)]


def get_data_files(data_path, codes):
    """Return the Gorilla Excel files that exist in the raw-data folder."""
    files = [
        data_path / f"data_exp_244697-v3_task-{code}.xlsx"
        for code in codes
    ]

    existing_files = [file for file in files if file.exists()]
    missing_files = [file for file in files if not file.exists()]

    if missing_files:
        print(f"{len(missing_files)} expected files were not found.")

    return existing_files


def prepare_tnt_data(data):
    """Select and clean Pocket TNT rating-scale rows."""
    columns = [
        "Condition",
        "Rep",
        "Participant Starting Group",
        "tripletNr",
        "cue_name",
        "target",
        "PairNr",
        "Participant Public ID",
        "randomiser-zwfq",
        "Screen Name",
        "Response",
        "Manipulation: Spreadsheet",
    ]

    tnt_data = data[columns].copy()

    tnt_data = tnt_data[
        tnt_data["Screen Name"] == "rating scale"
    ].copy()

    tnt_data = tnt_data.rename(
        columns={
            "Participant Public ID": "id",
            "Manipulation: Spreadsheet": "CBL",
            "randomiser-zwfq": "randomizer",
        }
    )

    return tnt_data


def load_counterbalancing(tnt_data):
    """Load the relevant sheet from the counterbalancing workbook."""
    cbl_value = str(tnt_data["CBL"].iloc[0])
    sheet_name = cbl_value.replace("CBL_", "", 1)

    return pd.read_excel(
        COUNTERBALANCING_FILE,
        sheet_name=sheet_name,
    )


def counterbalance_participant(counterbalancing, participant_data):
    """Merge one participant with the counterbalancing table."""
    merged = counterbalancing.merge(
        participant_data,
        on="PairNr",
        how="left",
    )

    index_columns = [
        "CBL",
        "PairNr",
        "Time",
        "group",
        "tripletNr (Exp)",
        "cue",
        "Condition_T",
        "Counterbalance",
        "randomizer",
    ]

    wide = merged.pivot_table(
        index=index_columns,
        columns="Rep",
        values="Response",
        aggfunc="first",
    ).reset_index()

    wide.columns.name = None
    return wide


def recode_intrusion_ratings(df):
    """Convert 0/1/2 ratings into binary intrusion scores."""
    df = df.copy()

    for column in REP_COLS:
        if column in df.columns:
            df[column] = df[column].map({0: 0, 1: 1, 2: 1})

    return df


def calculate_condition_means(df):
    """Calculate mean intrusion rates for each TNT condition."""
    participant_id = df["ParticipantID"].iloc[0]
    randomizer = df["randomizer"].iloc[0]
    counterbalance = df["Counterbalance"].iloc[0]
    cbl = df["CBL"].iloc[0]

    available_rep_cols = [
        column for column in REP_COLS if column in df.columns
    ]

    summary = (
        df.groupby("Condition_T", as_index=False)[available_rep_cols]
        .mean()
    )

    summary["ParticipantID"] = participant_id
    summary["randomizer"] = randomizer
    summary["Counterbalance"] = counterbalance
    summary["CBL"] = cbl

    return summary


def reshape_participant_summary(combined_summary):
    """Reshape condition summaries so each participant has one row."""
    id_columns = [
        "ParticipantID",
        "Counterbalance",
        "randomizer",
        "CBL",
    ]

    conditions = (
        combined_summary["Condition_T"]
        .drop_duplicates()
        .tolist()
    )

    long_df = combined_summary.melt(
        id_vars=id_columns + ["Condition_T"],
        value_vars=REP_COLS,
        var_name="Rep",
        value_name="IntrusionRate",
    )

    long_df["column_name"] = (
        long_df["Rep"]
        + "_"
        + long_df["Condition_T"].astype(str)
    )

    final_df = long_df.pivot(
        index=id_columns,
        columns="column_name",
        values="IntrusionRate",
    ).reset_index()

    final_df.columns.name = None

    response_columns = []

    for condition in conditions:
        response_columns.extend(
            [f"{rep}_{condition}" for rep in REP_COLS]
        )

    desired_order = [
        "ParticipantID",
        "randomizer",
        "Counterbalance",
        "CBL",
    ] + response_columns

    desired_order = [
        column
        for column in desired_order
        if column in final_df.columns
    ]

    return final_df[desired_order]


def process_file(file_path):
    """Process one Gorilla Excel export."""
    print(f"Processing file: {file_path.name}")

    data = pd.read_excel(file_path)
    tnt_data = prepare_tnt_data(data)

    if tnt_data.empty:
        raise ValueError("No rating-scale rows found.")

    counterbalancing = load_counterbalancing(tnt_data)
    participant_results = []

    for participant_id, participant_df in tnt_data.groupby("id"):
        participant_output = counterbalance_participant(
            counterbalancing,
            participant_df,
        )

        participant_output["ParticipantID"] = participant_id
        participant_results.append(participant_output)

    participant_results = [
        recode_intrusion_ratings(df)
        for df in participant_results
    ]

    summary_results = [
        calculate_condition_means(df)
        for df in participant_results
    ]

    combined_summary = pd.concat(
        summary_results,
        ignore_index=True,
    )

    final_df = reshape_participant_summary(combined_summary)

    cb_value = final_df["Counterbalance"].iloc[0]
    rand_value = final_df["randomizer"].iloc[0]

    dataset_name = f"pTNT_{cb_value}_{rand_value}"

    print(f"Created dataset: {dataset_name}")

    return dataset_name, final_df


def main():
    """Run the complete Pocket TNT preprocessing pipeline."""
    files = get_data_files(DATA_PATH, CODES)

    print(f"Found {len(files)} Gorilla files.")

    processed_datasets = {}

    for file_path in files:
        try:
            dataset_name, final_df = process_file(file_path)
            processed_datasets[dataset_name] = final_df

        except Exception as error:
            print(
                f"ERROR processing {file_path.name}: {error}"
            )

    if not processed_datasets:
        raise RuntimeError("No files were successfully processed.")

    combined_df = pd.concat(
        processed_datasets.values(),
        ignore_index=True,
    )

    combined_df = combined_df.dropna().reset_index(drop=True)

    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / "Pocket_TNT_combined.xlsx"

    combined_df.to_excel(
        output_file,
        index=False,
    )

    print("Processing complete.")
    print(f"Final participants: {len(combined_df)}")
    print(f"Saved output to: {output_file}")

    return combined_df, processed_datasets


if __name__ == "__main__":
    combined_df, processed_datasets = main()
