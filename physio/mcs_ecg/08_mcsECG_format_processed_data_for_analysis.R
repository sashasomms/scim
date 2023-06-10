# SCIM ECG Data Formatting (post-processing)
# Reads in cmetx group file and formats into a dataframe we can merge with the
# rest of our data
# Sasha Sommerfeldt, Wenqi Chen
# Originally for TSST, updated for MCS interoception task December 2022



# Clear the workspace ----------------------------------------------------------
rm(list=ls())

# Packages ---------------------------------------------------------------------
library(tidyverse)
library(psych)



# Paths ------------------------------------------------------------------------
physiodir = "../../processed-data/interoception/psychophys"
sdir = "../../scripts/physio/mcs_ecg"
setwd(sdir)
# CMETX output file
filename_ecg = paste0("INTEROCEPTION_ECG_OUTPUT_R1.CSV")
parse_by = ""


# Read in data -----------------------------------------------------------------
datafile_ecg = paste0(physiodir, '/cmetx_output_group/', filename_ecg)
df_ecgT = read_csv(datafile_ecg) %>% janitor::clean_names()
colnames(df_ecgT)

df_ecg <- df_ecgT %>% rename("original_filepath" = "id", "n_ibis" = "n_ib_is")
summary(df_ecg)
#view(df_ecg)

# Split first column ----------------------------------------------------------- 
# Split the first column of the cmetx ecg output (the filepath to the original
# participant ecg data file that was processed to give that row of output) into
# separate columns for ID, timepoint, and interoception block
df_ecg$original_filepath
# First split filepath 
if (parse_by == '') {
  # Names for what's in the first column
  split_columns <- c("drive", "folder1", "folder2", "folder3", "folder4", "folder5", "folder6",
                   "juicy")
  # Names for what's in the juicy column
  split_columns2 <- c("id", "timepoint", "interoception_block", "rater")
  # Names for wider 
  call_me <- c("timepoint", "interoception_block")
}
if (parse_by != ''){
  # Names for what's in the first column
  split_columns <- c("drive", "folder1", "folder2", "folder3", "folder4", "folder5", "folder6",
                    "juicy")
  # Names for what's in the juicy column
  split_columns2 <- c("id", "timepoint", "interoception_block", "rater", "parse_section")
  # Names for wider 
  call_me <- c("timepoint", "interoception_block", "parse_section")

}

df_temp <- separate(df_ecg, col = original_filepath, into = split_columns, sep = '\\\\')
df_temp$juicy <- gsub('interoception0000_', '', df_temp$juicy, ignore.case=TRUE)
df_temp2 <- df_temp %>% separate(col = juicy, 
                               into = split_columns2, sep = '_')
# discarding "clean" - that's ok

# Make sure it only has rater = R1, this will help get rid of mistakes
df_temp3 <- df_temp2[df_temp2$rater == "R1",]
# Get rid of unnecessary columns
df_temp4 <- df_temp3 %>% select(-contains("folder"), -drive, -rater)
# Remove anything that was a mistake where TSST was added
dfL <- df_temp4[df_temp4$interoception_block != "tsst0000",]


# True_idx vector: contains indices of all rows where the artifact filter was true (flagged) 
# These ecg files are likely to have a duplicate row when the flag was fixed and cmetx rerun. 
True_idx = seq(nrow(dfL))[dfL$arts_found]

keep_idx = c()

for (i in True_idx){
  dfL_i = dfL[i,][,1:3]   #filter row that has T and we only subset the first 4 cols for identifying purposes
  # Left join with any other rows in the main dataframe that have the same info in those first 3 rows
  joined_df = left_join(dfL_i, dfL)  
  
  # If there is only 1 row in that joined df, we're good. No duplicates. Add the row index to the keep_idx list.
  if (nrow(joined_df) == 1) {
    keep_idx = append(keep_idx, i)
  }
  else {
    # If there are multiple such rows, see if one has False for the artifact flag
    if (all((joined_df$arts_found))){
      # If there are multiple rows, but they are all True values (couldnt fix the artifact flag): 
      # Make a list of all the row indices 
      all_T_idx = which((dfL$id == dfL_i$id) & (dfL$timepoint == dfL_i$timepoint) & (dfL$interoception_block == dfL_i$interoception_block))
      # Keep only the last row (that is the most recent one added to the spreadsheet)
      keep_idx = append(keep_idx, max(all_T_idx))  
    }
    else {
      # Else, if it is a mix of True and False
      # Since False indices are not included in the True_idx, we don't do anything, just keep it on the True_idx?
      invisible()
    }
  }
}

# find different values between True_idx and keep_idx
remove_idx = setdiff(True_idx, unique(keep_idx))
if (length(remove_idx) > 0) {
  dfL1 = dfL[-remove_idx, ]
} else {
  dfL1 = dfL
}

# Remove duplicated False values (keep the last one) -- (from if cmetx was run multiple times for any given ecg file)
duplicated_F_idx = seq(nrow(dfL1))[duplicated(dfL1[,1:3], fromLast = T)]
if (length(duplicated_F_idx) > 0) {
  dfL1 = dfL1[-duplicated_F_idx,]
} else {
  dfL1 = dfL1
}

# Write out the long format data frame
filename_long = filename_ecg %>% str_replace(".CSV", "_longFormat_2022.12.09.csv")
print(filename_long)
write_csv(dfL1, paste0(physiodir, '/cmetx_output_group/formatted/', filename_long))




# Convert to wide format -------------------------------------------------------
values_cols <- c("n_ibis", "mean_ibi", "mean_hr",  "sdnn", "rmssd", "msd", 
                 "pnn50", "cvi", "csi", "toichi_l", "toichi_t", "log_hrv", 
                 "log_rsa")
dfW <- dfL %>% 
  pivot_wider(id_cols = id, 
              names_from = call_me,
              values_from = values_cols)
#colnames(dfW)

table(dfL$id)
view(dfW)


filename_wide = filename_ecg %>% str_replace(".CSV", "_wideFormat_2022.12.09.csv")
print(filename_wide)
write_csv(dfW, paste0(physiodir, '/cmetx_output_group/formatted/', filename_wide))



# Variable naming --------------------------------------------------------------
# Rename columns to fit our formatting
# this is the worst code but it works and I can't figure out how else to do this right now

oldnames = colnames(dfW)[-1]
newnames = 'id'
for (oldname in oldnames) {
  oldname_split = strsplit(oldname, "_", fixed = T)[[1]]
  print(length(oldname_split))
  if (length(oldname_split) == 3) {
    a = paste(oldname_split[c(2, 3, 1)], collapse = '_') 
    b = paste("pp_", a, sep = "")
    c = gsub('ecg', 'interoceptionECG_', b)
    firstpartsplit = strsplit(c, "_", fixed = T)[[1]][c(1, 2, 3)]
    firstpart = paste(firstpartsplit, collapse = '_')
    secondpartsplit = strsplit(c,"_",fixed=T)[[1]][c(4, 5)]
    secondpart = paste(c(secondpartsplit[1], secondpartsplit[2]), collapse = '')
    new = paste(c(firstpart, secondpart), collapse = '_')
  }
  if (length(oldname_split) == 4) {
    a = paste(oldname_split[c(3, 4, 1, 2)], collapse = '_') 
    b = paste("pp_", a, sep = "")
    c = gsub('ecg', 'interoceptionECG_', b)
    firstpartsplit = strsplit(c, "_", fixed = T)[[1]][c(1, 2, 3)]
    firstpart = paste(firstpartsplit, collapse = '_')
    secondpartsplit = strsplit(c,"_",fixed=T)[[1]][c(4, 5, 6)]
    secondpart = paste(c(secondpartsplit[1], secondpartsplit[2], str_to_title(secondpartsplit[3])), collapse = '')
    new = paste(c(firstpart, secondpart), collapse = '_')
  }
  newnames = c(newnames, new)
}
newnames
# change 'em!
colnames(dfW) = newnames

filename_wide = filename_ecg %>% str_replace(".CSV", "_wideFormat_goodNames_2022.12.09.csv")
write_csv(dfW, paste0(physiodir, '/cmetx_output_group/formatted/', filename_wide))
          