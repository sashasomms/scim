# Sasha Sommerfeldt
# August 2022
# Get people associated with Interoception ECG data

# Clear the workspace ----------------------------------------------------------
rm(list=ls())

# Packages ---------------------------------------------------------------------
library(tidyverse)
library(readxl)
library(data.table)
library(sys)

dir = '../../processed-data/interoception/psychophys/ecgQA'
QA_file = paste0(dir, '/quality_notes/Interoception_ecgQA_main_updated.tsv')
outfile = paste0(dir, '/quality_notes/people.txt')
# Phases
phases = c("LightToneBlock1", "HeartToneBlock1", "HeartToneBlock2")

# Participants
# Get a participant list from the cmetx_output_ibis directory 
# Note this won't work if for some reason someone is missing the Recovery phase
participants_temp = Sys.glob(file.path(paste0(dir, '4*_t[12]/cmetx_output_ibis/*HeartToneBlock2_R1.txt')))
participants = participants_temp %>% basename() %>% str_remove('_interoception0000_ecgHeartToneBlock2_R1.txt')

# Read in data -----------------------------------------------------------------

# QA spreadsheet
dfp = read_tsv(QA_file, skip = 1)
dfp$ID_TP = dfp$Subject_Timepoint
dfp_ss = dfp %>% select(c(ID_TP, starts_with("Reviewer")))

write_tsv(dfp_ss, outfile)

# Format
#LightToneBlock1: NAME | HeartToneBlock1: NAME | HeartToneBlock2: NAME

# Extract relevant notes from QA spreadsheet -----------------------------------

dfr = read_tsv(QA_file, skip = 1)
dfr = dfr[!is.na(dfr$Subject_Timepoint), ]

# Multiple overall ratings now 
rating_types = c("Overall", "Exclude", "Added", "Ectopic")
# Take the relevant columns from both reviewer and student QA spreadsheets and 
# merge them into one dataframe 
for (t in rating_types) {
  df_t = dfr %>% 
              select(c(Subject_Timepoint, Reviewer_HeartToneBlock1, starts_with(t))) %>% 
              dplyr::rename(c('Reviewer' = 'Reviewer_HeartToneBlock1'))
  df_t = df_t[order(df_t$Subject_Timepoint), ]
  outfile = paste0(dir, '/quality_notes/parsed/', t, '.txt')
  write_tsv(df_t, outfile)
}
# Parse the different columns from the QA spreadsheets by phase
for (p in participants) {
  for (phase in phases) {
    print(p)
    outfile = paste0(dir, "/quality_notes/parsed/", p, "_", phase, ".txt")
    df_temp = dfr[dfr$Subject_Timepoint == p,]
    dfp = df_temp %>% 
                select(contains(c(phase))) %>% 
                select(starts_with(c("Reviewer", "Overall", "Exclude", "Added", "Ectopic")))
    write_tsv(dfp, outfile)
  }
}

