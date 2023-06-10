# Sasha Sommerfeldt
# November 2022
# Creates subfolders within each participant's processed data folder for physio processing output
# Then segments the data by the block of the method of constant stimulus interoception task
# Includes the 12 seconds before and 12 seconds after the end of the phase to account for the CMETX filter

import pandas as pd
import sys
import glob
import os
import path

# Path to processed data directory
processedDir = '../../processed-data/interoception/psychophys'
dataDirs = glob.glob('%s/4???_t[12]' % processedDir)

# Phases/blocks to segment the data by
phases = ["LightTonePractice", "LightToneBlock1", "HeartTonePractice", "HeartToneBlock1", "HeartToneBlock2"]

# Enter any ID_Timepoints here to exclude. Put them between the square brackets with each id_tp in quotes.
exclude_ids = []

# Start a empty dataframe where length of each phase will be appended (as a double check on phase lengths)
time_data = []

for each_dataDir in dataDirs :
    print("")
    print(each_dataDir)
    subjID_timepoint = os.path.basename(each_dataDir)
    print(subjID_timepoint)

    # Segment the ECG data
    if os.path.isfile('%s/%s/%s/%s_interoception0000_ecgHeartToneBlock2_12s.txt' % (processedDir, subjID_timepoint, 'ecg_by_block', subjID_timepoint)) :
        print('%s already completed ecg segmentation, skipping' %subjID_timepoint)
    else :
        if subjID_timepoint not in exclude_ids :
            if os.path.isfile('%s/raw_converted_to_txt/%s_block_times.txt' %(each_dataDir, subjID_timepoint)) :
                # Create the folder structure
                ecg_by_block_dir = '%s/%s/%s' % (processedDir, subjID_timepoint, 'ecg_by_block')
                ecg_by_block_processed_through_qrs_dir = '%s/%s/%s' % (processedDir, subjID_timepoint, 'ecg_by_block_processed_through_qrs')
                cmetx_output_beats_dir = '%s/%s/%s' % (processedDir, subjID_timepoint, 'cmetx_output_beats')
                cmetx_output_ibis_dir = '%s/%s/%s' % (processedDir, subjID_timepoint, 'cmetx_output_ibis')

                dirs_to_create = [ecg_by_block_dir, ecg_by_block_processed_through_qrs_dir, cmetx_output_beats_dir, cmetx_output_ibis_dir]
                for d in dirs_to_create:
                    try:
                        os.mkdir(d)
                    except OSError:
                        print ("Creation of the directory %s failed (may already be created)" % d)
                    else:
                        print ("Successfully created the directory %s " % d)

                # Read in the participant's markers and data files to pandas dataframes
                df_simplified_markers = pd.read_csv('%s/%s/%s/%s_block_times.txt' % (processedDir, subjID_timepoint, 'raw_converted_to_txt', subjID_timepoint), sep='\t')
                df_ECG = pd.read_csv('%s/%s/%s/%s_interoception0000_ecg.txt' % (processedDir, subjID_timepoint, 'raw_converted_to_txt', subjID_timepoint), sep='\t', names=['time','ecg'])

                # Parse the  big ol' timeseries down into pieces so it is easier to manage in QRStool.
                for phase in phases :
                    # Find the time when each phase started
                    # Subtract 12 seconds from the start time so we get a buffer for the CMeTX filter
                    phaseStartTime = float(df_simplified_markers['time'][df_simplified_markers['label'] == '%sStart' %phase]) - 12.000
                    phaseEndTime = float(df_simplified_markers['time'][df_simplified_markers['label'] == '%sEnd' %phase]) + 12.000
                    dfTemp = df_ECG[df_ECG['time'] >= phaseStartTime]
                    dfPhase = dfTemp[dfTemp['time'] < phaseEndTime]
                    dfPhase.to_csv('%s/%s_interoception0000_ecg%s_12s.txt' % (ecg_by_block_dir, subjID_timepoint, phase), sep='\t', index=False, header=False)
                    phase_length = (dfPhase['time'].iloc[-1] - dfPhase['time'].iloc[0])/60
                    print("%s is %s minutes long" %(phase, phase_length))
                    time_data.append([subjID_timepoint, phase, phase_length])

                df_time = pd.DataFrame(time_data)
                df_time.to_csv('%s/%s/ecg_by_block/%s_block_lengths.txt' % (processedDir, subjID_timepoint, subjID_timepoint), sep='\t', index=False)
