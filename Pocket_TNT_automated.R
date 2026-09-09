library(tidyverse)
library(stats)
library(ez)
library(openxlsx)
library(broom)
library(purrr)
library(lavaan)
library(writexl)
library(readxl)
library(stringr)


# 1. Define your folder path
data_path <- "C:/Users/ketak/OneDrive/Desktop/Psychometry_PocketTNT_Study/Pocket TNT/Gorilla_Data/Gorilla_data_version_11_cueAB - 2"

# 2. List your 40 unique codes
codes <- c("scp3", "ca3i", "dqih", "m7tz", "sb6w", "7elq", "ibqa", "ai78", "5gka", "5nhp",
           "5huk","9lyj", "nk7m", "43kj", "vwo5", "xhu4", "5k5p", "h2c3", "wufa", "a26j", 
           "56fu", "e1w2","yqbw", "yohe", "77if", "tx6j", "pni5", "4xtk", "fep6", "ryey",
           "xie7", "dli1", "wut4","cqkq", "2cwa", "pwtn", "ewyl", "73aw", "hi1p", "j9pc")

# 3. Build full paths for those specific Excel files
files <- file.path(data_path, paste0("data_exp_244697-v3_task-", codes, ".xlsx"))
files <- files[file.exists(files)]  # skip any missing files

# 4. Loop through each file and run your full script
for (file_path in files) {
  message("Processing file: ", basename(file_path))
  
  # ---- Your full existing code starts here ----
  
  try({
  data <- read_excel(file_path)
  
  #select relevant columns from data
  
  
  tnt_data <- data %>%
    select(Condition, Rep, `Participant Starting Group`, tripletNr, cue_name, target, PairNr, `Participant Public ID` ,`randomiser-zwfq`,
           `Screen Name`, Response, `Manipulation: Spreadsheet`)
  
  #filter for rows with just rating scale
  
  tnt_data <- tnt_data %>%
    filter(`Screen Name` == "rating scale")
  
  tnt_data <- tnt_data %>% 
    rename(id = `Participant Public ID`,
           CBL = `Manipulation: Spreadsheet`,
           randomizer = `randomiser-zwfq`)
  
  ##upload Counterbalancing dataset
  
  sheet_name <- str_remove(tnt_data$CBL[1], "CBL_")
  
  # Import that sheet from Counterbalancing.xlsx
  Counterbalancing <- read_excel("Counterbalancing.xlsx", sheet = sheet_name)
  
  
  # Define the function
  counterbalance_fn <- function(Counterbalancing, tnt_data) {
    Counterbalancing %>%
      left_join(tnt_data, by = "PairNr") %>%
      pivot_wider(
        id_cols = c(CBL, PairNr, Time, group, `tripletNr (Exp)`, cue, Condition_T, Counterbalance, randomizer),
        names_from = Rep,
        values_from = Response
      )
  }
  
  
  
  results <- tnt_data %>%
    group_split(id) %>%
    lapply(function(sub_df) {
      pid <- unique(sub_df$id)
      out <- counterbalance_fn(Counterbalancing, sub_df)
      out$ParticipantID <- pid   # add ID column to the output
      out
    })
  
  #changing the responses into intrusion rating 0 or 1
  
  # Columns you want to recode
  cols_to_recode <- c("rep01", "rep02", "rep03", "rep04", "rep05", "rep06", "rep07", "rep08", "rep09", "rep10") 
  
  # Apply to every dataframe in the list
  results_int <- lapply(results, function(df) {
    df %>%
      mutate(across(all_of(cols_to_recode),
                    ~ case_when(
                      . %in% c(1, 2) ~ 1,
                      . == 0 ~ 0
                    )))
  })
  
  ##intrusion rating calculation for each condition
  
  
  summary_results <- lapply(results_int, function(df) {
    ParticipantID <- unique(df$ParticipantID)      # extract ParticipantID
    Counterbalance <- unique(df$Counterbalance)    # extract Counterbalance
    randomizer <- unique(df$randomizer)
    CBL <- unique(df$CBL)
    # extract ParticipantID
    df %>%
      group_by(Condition_T) %>%
      summarise(across(all_of(cols_to_recode), ~ mean(.x, na.rm = TRUE)), .groups = "drop") %>%
      mutate(ParticipantID = ParticipantID,
             randomizer = randomizer,
             Counterbalance = Counterbalance,
             CBL = CBL)     # add it back
  })
  
  
  # Combine all participants into one dataframe
  combined_df <- bind_rows(summary_results)
  
  # wide format
  
  final_df <- combined_df %>%
    pivot_wider(
      id_cols = c(ParticipantID, Counterbalance, randomizer, CBL),        # each participant = one row
      names_from = Condition_T,       # spread by Condition
      values_from = rep01:rep10,      # all rep columns
      names_sep = "_"                 
    )
  
  # Reorder columns: group rep01–rep10 for each condition together
  # Get the condition names in order
  conds <- unique(combined_df$Condition_T)
  
  # Create the desired column order
  rep_cols <- paste0("rep", sprintf("%02d", 1:10))
  new_order <- c("ParticipantID", "randomizer", "Counterbalance", "CBL", as.vector(sapply(conds, function(c) paste0(rep_cols, "_", c))))
  
  # Reorder columns
  final_df <- final_df[, new_order]
  
  ##rename based on counterbalancing condition
  
  cb_value <- final_df$Counterbalance[1]
  rand_value <- final_df$randomizer[1]
  
  # Create the new variable name
  new_name <- paste0("pTNT_", cb_value, "_", rand_value)
  
  # Assign final_df to a new object with that name
  
  assign(new_name, final_df) 
  
  message("Created object: ", new_name)
  })
}
  
  
  ##combine all data 
  
  # List all objects that start with "data_"
  data_objects <- ls(pattern = "^pTNT_")
  
  # Get the objects as a list
  data_list <- mget(data_objects)
  
  # Combine into a single dataframe
  combined_df <- bind_rows(data_list)
  
  ##remove NAs
  
  combined_df <- combined_df %>%
    drop_na()
  