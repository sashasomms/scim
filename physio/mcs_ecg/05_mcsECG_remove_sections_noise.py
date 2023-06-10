# Sasha Sommerfeldt, Wenqi Chen, Tiffany Bahar, Natalie Shulstad
# June 2022
# This script is designed to exclude the sections of the ECG timeseries that
# were identified as too noisy during processing.

import pandas as pd
import sys
import glob
import os
import path
import numpy as np


# Location of downloaded QA spreadsheet (QA spreadsheet is on Google Drive for collaboration across data processors)
qa_file = "../../processed-data/interoception/psychophys/ecgQA/quality_notes/Interoception_ecgQA_main_updated.tsv"
# From this we will want: Subject_Timepoint and ExcludeSections_math columns (or per phase)

# Path to processed data directory
processed_dir = '../../processed-data/interoception/psychophys'
# Initials of data processor
initials = 'R1'

phases_dict = {1:'LightToneBlock1', 2:'HeartToneBlock1', 3:'HeartToneBlock2'}

# Read in the QA sheet
df_QA = pd.read_csv(qa_file, skiprows = 1, sep ='\t')

# Filter to only include rows where a Subject_Timepoint is listed
df_QA = df_QA[df_QA.Subject_Timepoint.notna()]
df_QA.drop(columns=['acq2txt_script_run', 'Subset_script_run', 'Participant_done', 'Total_time_to_process'], inplace=True)


# Convert to long format (then have just one column for exclude sections)
stubs = ['Reviewer_', 'DateReviewed_', 'Added_beat_', 'Ectopic_beat_', 'Exclude_sections_', 'Cleaned_', 'Ran_CMeTX_', 'Saved_cleaned_as_qrs_file_', 'Notes_', 'Overall_quality_', 'Time_to_process_minutes_']
# Translate phases to numeric
for key in phases_dict.keys():
    df_QA.columns = df_QA.columns.str.replace(str(phases_dict[key]), str(key))
# Convert to long
df_QA_L = pd.wide_to_long(df_QA, stubnames=stubs, i='Subject_Timepoint', j='phase').reset_index()
# Make phases words again
for key in phases_dict.keys():
    df_QA_L.phase = df_QA_L.phase.replace(key, str(phases_dict[key]))


# Filter that long data frame to only have rows where Exclude_sections != N/A
df_QA_L['Exclude_sections_'].value_counts()
df_QA_Lss = df_QA_L[df_QA_L['Exclude_sections_'].notna()]


for i, row in df_QA_Lss.iterrows() :
    id_tp = row['Subject_Timepoint']
    phase = row['phase']
    print("\n\n\n")
    print(id_tp)
    print(phase)
    # Rows might contain more than 1 section to exclude, separated by a comma. Split them into items in a list
    sections = row['Exclude_sections_'].split(',')

    # Read in the beat-time file ---
    relevant_beats_files = glob.glob('%s/%s/%s/%s_interoception0000_ecg%s*_%s.txt' % (processed_dir, id_tp, 'cmetx_output_beats', id_tp, phase, initials))

    for beat_file in relevant_beats_files :
        print("\n\n")
        print(beat_file)
        df_beats = pd.read_csv(beat_file, sep='\t', names=['time']).reset_index()
        beat_outfile = beat_file[:len(beat_file)-4]
        #print(beat_outfile)
        ibis_file = beat_file.replace("beats", "ibis")
        df_ibis = pd.read_csv(ibis_file, sep='\t', names=['ibi']).reset_index()
        ibis_outfile = ibis_file[:len(ibis_file)-4]

        # Start an empty list for section lengths so can get the total later
        s_lengths = []

        sections_dict = {}
        for s in sections:
            # Split the start and end times into separate items in a list and strip out the whitespace
            s_split = s.split('-')
            # Start time of this section
            s_start = float(s_split[0].strip())
            # End time of this section
            s_end = float(s_split[1].strip())
            sections_dict.update({s_start:s_end})

        # Sort in reverse order, we have to remove last sections first otherwise timing of later sections gets messed up
        for s_start in sorted(sections_dict, reverse = True):
            print("")
            s_end = sections_dict[s_start]
            print("Exclude section: %s-%s" %(s_start, s_end))
            # reset s_length
            s_length = ''

            ## Check if the s_start and s_end are contained in df_beats
            # Start time for beats file
            b_start = df_beats['time'].iloc[0]
            # End time for beats file
            b_end = df_beats['time'].iloc[-1]

            # Is s_start in the beat file?
            s_start_in_b = (s_start > b_start) and (s_start < b_end)
            # Is s_end in the beat file?
            s_end_in_b = (s_end > b_start) and (s_end < b_end)

            # It's possible that either the start or end of the noisy section, or both, are not
            # contained in the beats file (due to parsing the beats file to greater precision).

            # A. The noise does not affect this file, i.e., the noise is either entirely before this file or entirely after it
            if ((s_end < b_start) or (s_start > b_end)):
                print("File not impacted by this noise section")
                s_length = 0
                break

            # B. If the noise starts in the file but extends past the end of the file, then
            # Set s_length to use b_end instead of s_end in calculating the length of s
            if (s_end > b_end) and s_start_in_b:
                print("Noise starts in file and continues after the file")
                ## Find nearest beat to the manually identified noise start times
                # calculate the difference array
                diff_array_s_start = np.absolute(df_beats['time'] - s_start)
                # find the index of minimum element from the array
                index_nearestBeat2s_start = diff_array_s_start.argmin()
                s_start_beatTime = df_beats['time'][index_nearestBeat2s_start]
                s_end_beatTime = b_end
                # Calculate length of noise using nearest beats to manually marked start/stop times of noise
                s_length = round(s_end_beatTime - s_start_beatTime, 4)

            # C. If the noise starts before the file but ends within it, then
            # Set s_length to use b_start instead of s_start in calculating the length of s
            if (s_start < b_start) and s_end_in_b:
                print("Noise starts before this file and ends within the file")
                ## Find nearest beat to the manually identified noise end times
                # calculate the difference array
                diff_array_s_end = np.absolute(df_beats['time'] - s_end)
                # find the index of minimum element from the array
                index_nearestBeat2s_end = diff_array_s_end.argmin()
                s_end_beatTime = df_beats['time'][index_nearestBeat2s_end]
                s_start_beatTime = b_start
                # Calculate length of noise using nearest beats to manually marked start/stop times of noise
                s_length = round(s_end_beatTime - s_start_beatTime, 4)

            # D. If the noise starts before the file and continues after the file, then the whole file is junk
            if (s_start < b_start) and (s_end > b_end):
                # for this case all the beats in the file will be dropped
                print("No useable data in this file")
                s_length = 0

            # E. The noisy section is entirely contained within the file
            # Then s_length is just the length of the noisy section
            if (s_start > b_start) and (s_end < b_end):
                print("Noise is entirely contained in this file")
                ## Find nearest beat to the manually identified noise start times
                # calculate the difference array
                diff_array_s_start = np.absolute(df_beats['time'] - s_start)
                # find the index of minimum element from the array
                index_nearestBeat2s_start = diff_array_s_start.argmin()
                s_start_beatTime = df_beats['time'][index_nearestBeat2s_start]
                ## Find nearest beat to the manually identified noise end times
                # calculate the difference array
                diff_array_s_end = np.absolute(df_beats['time'] - s_end)
                # find the index of minimum element from the array
                index_nearestBeat2s_end = diff_array_s_end.argmin()
                s_end_beatTime = df_beats['time'][index_nearestBeat2s_end]
                print("Should drop beats with indices %s-%s" %(index_nearestBeat2s_start+1, index_nearestBeat2s_end)) # don't drop beat at start of noise
                # Calculate length of noise using nearest beats to manually marked start/stop times of noise
                s_length = round(s_end_beatTime - s_start_beatTime, 2)

            # Append this length to the list for this section
            print("Section length (s): %s" %s_length)
            s_lengths.append(s_length)

            ## Remove any beats in noise section incase any were marked there during processing
            beats_in_s = df_beats[(df_beats['time'] > s_start_beatTime) & (df_beats['time'] <= s_end_beatTime)].index.tolist()
            print("Number of beats marked in noise (dropping): %s" %len(beats_in_s))
            # If beats_in_s is not empty, (i.e., there are beats that were marked within the noisy section)
            if len(beats_in_s) > 0:
                # Then drop any beats and corresponding ibis marked in the noise
                df_beats.drop(index = beats_in_s, inplace = True)
                ibis_in_s = [x - 1 for x in beats_in_s]
                print("Indices of ibis to drop:")
                print(ibis_in_s)
                if ibis_in_s[0] == -1 :
                    ibis_in_s = ibis_in_s[1:]
                    print("New ibis_in_s: %s" %ibis_in_s)
                df_ibis.drop(index = ibis_in_s, inplace = True)

            ## Back the data up over the noise
            # For every beat time that comes after the noisy section, subtract the length of noise from the beat time
            # This is essentially "backing the data up" to exclude the noise
            # Results in losing 1 beat and 1 ibi row from the timeseries: last beat before the noise is replaced by the first good beat after the noise
            df_beats.loc[df_beats['time'] > s_end_beatTime, 'time'] -= s_length

        print("\nFILE SUMMARY:")
        ## Calculate total noise for this beat_file
        s_lengths_sum = round(sum(s_lengths), 4)
        print("Total noise for this file (s): %s" %s_lengths_sum)

        # Total length of beat file
        beat_file_length = round((b_end - b_start), 4)
        print("Beat file length (s): %s" %(beat_file_length))

        # Percent of beat file that's noise
        # It's getting file length from first and last beats marked so if few
        # or no beats marked in this file during processing (d/t noise),
        # then this percent wont correspond well to percent of expected length of this file
        perc_noise = round(round(s_lengths_sum/beat_file_length, 3)*100, 1)
        print("Percent of this file that's noise: %s" %perc_noise)
        # Write out the cleaned beat file
        print(beat_outfile)
        print(ibis_outfile)
        # Eventually this should overwrite the original
        df_beats['time'].round(4).to_csv('%s_clean.txt' % (beat_outfile), sep='\t', index=False, header=False)
        df_ibis['ibi'].to_csv('%s_clean.txt' % (ibis_outfile), sep='\t', index=False, header=False)

