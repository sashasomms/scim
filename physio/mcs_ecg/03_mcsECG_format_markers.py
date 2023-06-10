# Sasha Sommerfeldt
# November 2022

import pandas as pd
pd.options.mode.chained_assignment = None  
import sys
import glob
import os
import path

# Path to the processed data directory
raw_dir = '../../raw-data/interoception/behavioral'
processed_dir = '../../processed-data/interoception/psychophys'
trial_dir = '../interoception/task/trials'
data_dirs = sorted(glob.glob('%s/4???_t[12]' % processed_dir))

# List any participants to exclude from this processing here
exclude_ids = []


for each_data_dir in data_dirs :
    print("")
    print(each_data_dir)
    # participantID_timepoint
    id_tp = os.path.basename(each_data_dir)
    print(id_tp)
    if id_tp not in exclude_ids:
        ## Read in the behavioral data files
        # Practice trials: has both lt and ht, 6 practice trials each
        df_p = pd.read_csv('%s/%s_MCSinteroception_practice.csv' %(raw_dir, id_tp))
        # light-tone trials (1 block)
        df_lt =  pd.read_csv('%s/%s_MCSinteroception_lightTone.csv' %(raw_dir, id_tp))
        df_lt['block'] = 'lightTone_block1'
        # heartbeat-tone trials (2 blocks)
        df_ht_temp =  pd.read_csv('%s/%s_MCSinteroception.csv' %(raw_dir, id_tp))
        #df_ht = df_ht_temp[0:60] # Take only the first 60 rows so those who did 90 end up the same
        df_ht = df_ht_temp
        df_ht.at[0:30, 'block'] = 'heartTone_block1'
        df_ht.at[30:60, 'block'] = 'heartTone_block2'
        
        # the trial markers file from acq DINs
        df_markers = pd.read_csv('%s/%s/raw_converted_to_txt/%s_interoception0000_markers.txt' %(processed_dir, id_tp, id_tp), sep='\t')
        # Print number of markers in the ECG file
        n_markers_total = len(df_markers['time_seconds'])
        print("%s markers" %n_markers_total)
        
        
        # Sort the markers file by time
        df_markers.sort_values(by='time_seconds', inplace=True, ignore_index=True)
        if (n_markers_total == 218) or (n_markers_total == 278) or (n_markers_total == 206) or (n_markers_total == 266) or (n_markers_total == 230) :
             # Sometimes an extra 200 ms trial start and trial end gets added to the start of the ECG markers, so trim those first 2 markers ("200 ms" start & end)
            df_markers = df_markers.tail(-2)
        if n_markers_total == 208 or n_markers_total == 268 :
            # Sometimes an extra 200 ms trial start and trial end gets added to the start of the ECG markers, so trim those first 4 markers ("200 ms" start & end)
            df_markers = df_markers.tail(-4)
        # Reset the index so index order matches time order
        df_markers.reset_index(drop = True, inplace = True)
        # Take just the start markers
        df_markers_starts = df_markers[df_markers['event_type'].str.contains('msTrialStart')]
        # Reset the index of starts so marker starts index corresponds to behavioral trial number when you add 1 (bc 0 start of indexing in python)
        df_markers_starts.reset_index(drop = True, inplace = True)
        df_markers_starts['trialNum'] = df_markers_starts.index.to_series() + 1
        # Strip the non-numeric part of the trialDelay column so just numeric ms of trialDelay
        df_markers_starts['trialDelay_markers'] = df_markers_starts['event_type'].str.replace('msTrialStart', '')

        # Determine trial set
        trial_set = df_ht.trialSet[1]
        print("Trial set is %s" %trial_set)
      
        # Get number of trials for each segment from behavioral data
        n_trials_p = len(df_p['trialNum'])
        n_trials_lt = len(df_lt['trialNum'])
        n_trials_ht = len(df_ht['trialNum'])
        
        # Sort out practice trials
        print("%s practice trials\n%s light-tone trials\n%s heart-tone trials" %(n_trials_p, n_trials_lt, n_trials_ht))
        
        
        # 18 practice trials: Repeated either lightTone practice or heartTone practice (not both)
        # If there are 18 practice trials it's tricky because the way the task output data, we can't tell if repeated practice for lightTone or heartTone (oops). 
        # Have to compare trial order from ECG to ground truth trial orders (that task presentation script pulls from) to determine.
        if n_trials_p == 18 :
            print("Practice trials = 18")
            # Read in ground truth trial orders
            df_trials_V1 = pd.read_csv("%s/all_trials_%s_18practiceV1.txt" %(trial_dir, trial_set), sep='\t')        
            df_trials_V2 = pd.read_csv("%s/all_trials_%s_18practiceV2.txt" %(trial_dir, trial_set), sep='\t')
  
            if n_trials_ht == 90 :
                print("Heart Tone trials = 90")
                df_ht.at[60:90, 'block'] = 'heartTone_block3'
                df_trials = pd.read_csv("%s/all_trials_%s_90.txt" %(trial_dir, trial_set), sep='\t')
                # Read in ground truth trial orders -- overwrite previous with 90 trial versions
                df_trials_V1 = pd.read_csv("%s/all_trials_%s_90_18practiceV1.txt" %(trial_dir, trial_set), sep='\t')        
                df_trials_V2 = pd.read_csv("%s/all_trials_%s_90_18practiceV2.txt" %(trial_dir, trial_set), sep='\t')
            
            ##  Compare trial order to the two options to determine which one
            # V1 (did 2 rounds of practice for lightTone)        
            df_diff_V1 = pd.concat([df_trials_V1, df_markers_starts], axis = 1)
            df_diff_V1['diff'] = pd.to_numeric(df_diff_V1['trialDelay_markers']) - pd.to_numeric(df_diff_V1['trialDelay'])
            sum_diff_V1 = sum(abs(df_diff_V1['diff']))
            if sum_diff_V1 != 0:
                print("Not V1")
            if sum_diff_V1 == 0:
                version = "V1"
                print("V1 is the one!")
            # V2 (did 2 rounds of practice for heartTone)
            df_diff_V2 = pd.concat([df_trials_V2, df_markers_starts], axis = 1)
            df_diff_V2['diff'] = pd.to_numeric(df_diff_V2['trialDelay_markers']) - pd.to_numeric(df_diff_V2['trialDelay'])
            sum_diff_V2 = sum(abs(df_diff_V2['diff']))
            if sum_diff_V2 != 0:
                print("Not V2")
            if sum_diff_V2 == 0:
                version = "V2"
                print("V2 is the one!")
            if version == "V1":
                # concatenate participant behavioral data in V1 order
                df_p_lt = pd.concat([df_p[0:6], df_p[6:12]])
                df_p_ht = df_p[12:19]
                df_p_lt['block'] = 'lightTone_practice'
                df_p_ht['block'] = 'heartTone_practice'
                df_all_lt = pd.concat([df_p_lt, df_lt])
                df_all_ht = pd.concat([df_p_ht, df_ht])
                df_all_behav = pd.concat([df_all_lt, df_all_ht])
                df_all_behav.reset_index(drop = True, inplace = True)
                df_all_behav['trialNum'] = df_all_behav.index.to_series() + 1
                # Save ground truth trials as the V1 order
                df_trials = df_trials_V1
            elif version == "V2":
                # concatenate participant behavioral data in V2 order
                df_p_lt = df_p[0:6]
                df_p_ht = pd.concat([df_p[0:6], df_p[0:6]])
                df_p_lt['block'] = 'lightTone_practice'
                df_p_ht['block'] = 'heartTone_practice'
                df_trials = pd.read_csv("%s/all_trials_%s_18practiceV2.txt" %(trial_dir, trial_set), sep='\t')
                df_all_lt = pd.concat([df_p_lt, df_lt])
                df_all_ht = pd.concat([df_p_ht, df_ht])
                df_all_behav = pd.concat([df_all_lt, df_all_ht])
                df_all_behav.reset_index(drop = True, inplace = True)
                df_all_behav['trialNum'] = df_all_behav.index.to_series() + 1
                # Save ground truth trials as the V2 order
                df_trials = df_trials_V2
            
            
        # 24 practice trials: Repeated practice trials for both lightTone trials and heartTone
        if n_trials_p == 24 :
            print("24 practice trials")
            df_p_lt = df_p[0:12]
            df_p_lt['block'] = 'lightTone_practice'
            df_p_ht = df_p[12:24]
            df_p_ht['block'] = 'heartTone_practice'
            # Read in the ground truth trials order
            df_trials = pd.read_csv("%s/all_trials_%s_24practice.txt" %(trial_dir, trial_set), sep='\t')
            
            # Merge the behavioral files in order the trials occured to match the acq file
            df_all_lt = pd.concat([df_p_lt, df_lt])
            df_all_ht = pd.concat([df_p_ht, df_ht])
            df_all_behav = pd.concat([df_all_lt, df_all_ht])
            df_all_behav.reset_index(drop = True, inplace = True)
            df_all_behav['trialNum'] = df_all_behav.index.to_series() + 1
            df_all_behav.to_csv("%s/raw_converted_to_txt/%s_behav.txt" %(each_data_dir, id_tp), sep='\t', index = False)
            
            
        # 12 practice trials: Did not repeat practice trials for either lightTone or heartTone, only typical 6 of each
        if n_trials_p == 12 :
            print("12 practice trials")
            df_p_lt = df_p[0:6]
            df_p_lt['block'] = 'lightTone_practice'
            df_p_ht = df_p[6:13]
            df_p_ht['block'] = 'heartTone_practice'
            # Read in the ground truth trials order
            df_trials = pd.read_csv("%s/all_trials_%s.txt" %(trial_dir, trial_set), sep='\t')
            
            if n_trials_ht == 90 :
                print("Heart Tone trials = 90")
                df_ht.at[60:90, 'block'] = 'heartTone_block3'
                df_trials = pd.read_csv("%s/all_trials_%s_90.txt" %(trial_dir, trial_set), sep='\t')

            # Merge the behavioral files in order the trials occured to match the acq file
            df_all_lt = pd.concat([df_p_lt, df_lt])
            df_all_ht = pd.concat([df_p_ht, df_ht])
            df_all_behav = pd.concat([df_all_lt, df_all_ht])
            df_all_behav.reset_index(drop = True, inplace = True)
            df_all_behav['trialNum'] = df_all_behav.index.to_series() + 1
            df_all_behav.to_csv("%s/raw_converted_to_txt/%s_behav.txt" %(each_data_dir, id_tp), sep='\t', index = False)
        
        
        # Below is for  all practice trial numbers
        # Print total number of behavioral trials
        n_trials_total = len(df_all_behav['trialNum'])
        print("%s Trials from behav files" %n_trials_total)

        # First verify that the ECG Markers are in the expected order
        df_diff = pd.concat([df_trials, df_markers_starts], axis = 1)
        df_diff['diff'] = pd.to_numeric(df_diff['trialDelay_markers']) - pd.to_numeric(df_diff['trialDelay'])
        sum_diff_ecg = sum(abs(df_diff['diff']))
        if sum_diff_ecg == 0:
            print("Good, ECG markers match expected trial order")
            # Pull out only the trialEnds -- drop index, add as +1 for trialNum
            df_markers_ends = df_markers[df_markers['event_type'].str.contains('msTrialEnd')]
            df_markers_ends.reset_index(drop = True, inplace = True)
            df_markers_ends['trialNum'] = df_markers_ends.index.to_series() + 1
            df_markers_ends['trialDelay_markers'] = df_markers_ends['event_type'].str.replace('msTrialEnd', '')
            df_markers_ends.rename(columns={"time_seconds": "time_trialEnd"}, inplace = True)
            df_markers_ends.rename(columns={"trialDelay_markers": "trialDelay_ends"}, inplace = True)
            df_markers_starts.rename(columns={"time_seconds": "time_trialStart"}, inplace = True)
            # Merge starts with ends, should end up with a column for the start time and a column for the end time
            df_markers_wide = pd.concat([df_markers_starts, df_markers_ends])
            df_markers_wide = df_markers_starts.merge(df_markers_ends, on = 'trialNum')
            # We already know that the starts file matches the expected trial order so just a double check that the ends matches the starts for trial type order
            df_markers_wide['trialDelay_diff'] = pd.to_numeric(df_markers_wide['trialDelay_markers']) - pd.to_numeric(df_markers_wide['trialDelay_ends'])
            sum_diff_ecg_ends = sum(abs(df_markers_wide['trialDelay_diff']))
            if sum_diff_ecg_ends == 0:
                print("Good, ECG markers for starts and ends match")
                df_markers_wide.drop(['nid_x', 'nid_y', 'event_type_x', 'event_type_y', 'trialDelay_ends', 'trialDelay_diff'], axis=1, inplace = True)

                # Now verify that the concatenated behavioral data is in the expected order
                df_all_behav.rename(columns={"trialDelay": "trialDelay_behav"}, inplace = True)
                df_diff = pd.concat([df_trials, df_all_behav], axis = 1)
                df_diff['diff'] = pd.to_numeric(df_diff['trialDelay_behav']) - pd.to_numeric(df_diff['trialDelay'])
                sum_diff_behav = sum(abs(df_diff['diff']))
                if sum_diff_behav == 0:
                    print("Good, behavioral data match expected trial order")

                    # Merge ECG markers for start and end times in ECG timeseries with behavioral data
                    df_behav_markers = df_all_behav.merge(df_markers_wide, on = 'trialNum')
                    df_behav_markers.to_csv("%s/raw_converted_to_txt/%s_behav_plus_markers.txt" %(each_data_dir, id_tp), sep='\t', index = False)

                    # Start and end times of blocks
                    # LightTonePractice
                    start_time_ltp = df_behav_markers['time_trialStart'][df_behav_markers['block'] == 'lightTone_practice'].iloc[0]
                    end_time_ltp = df_behav_markers['time_trialEnd'][df_behav_markers['block'] == 'lightTone_practice'].iloc[-1]
                    # LightToneBlock1
                    start_time_lt = df_behav_markers['time_trialStart'][df_behav_markers['block'] == 'lightTone_block1'].iloc[0]
                    end_time_lt = df_behav_markers['time_trialEnd'][df_behav_markers['block'] == 'lightTone_block1'].iloc[-1]
                    # HeartTonePractice
                    start_time_htp = df_behav_markers['time_trialStart'][df_behav_markers['block'] == 'heartTone_practice'].iloc[0]
                    end_time_htp = df_behav_markers['time_trialEnd'][df_behav_markers['block'] == 'heartTone_practice'].iloc[-1]
                    # HeartToneBlock1
                    start_time_htb1 = df_behav_markers['time_trialStart'][df_behav_markers['block'] == 'heartTone_block1'].iloc[0]
                    end_time_htb1 = df_behav_markers['time_trialEnd'][df_behav_markers['block'] == 'heartTone_block1'].iloc[-1]
                    # HeartToneBlock2
                    start_time_htb2 = df_behav_markers['time_trialStart'][df_behav_markers['block'] == 'heartTone_block2'].iloc[0]
                    end_time_htb2 = df_behav_markers['time_trialEnd'][df_behav_markers['block'] == 'heartTone_block2'].iloc[-1]

                    # Setup data for writing out the table
                    values = [start_time_ltp, end_time_ltp, start_time_lt, end_time_lt, start_time_htp, end_time_htp, start_time_htb1, end_time_htb1, start_time_htb2, end_time_htb2]
                    labels = ["LightTonePracticeStart", "LightTonePracticeEnd", "LightToneBlock1Start", "LightToneBlock1End", "HeartTonePracticeStart", "HeartTonePracticeEnd", "HeartToneBlock1Start", "HeartToneBlock1End", "HeartToneBlock2Start", "HeartToneBlock2End"]
                    
                    # HeartToneBlock3 (only some participants did a 3rd block)
                    if (n_trials_ht == 90):
                        start_time_htb3 = df_behav_markers['time_trialStart'][df_behav_markers['block'] == 'heartTone_block3'].iloc[0]
                        end_time_htb3 = df_behav_markers['time_trialEnd'][df_behav_markers['block'] == 'heartTone_block3'].iloc[-1]
                        # Overwrite so includes a 3rd block in table for 90 trial folks
                        values = [start_time_ltp, end_time_ltp, start_time_lt, end_time_lt, start_time_htp, end_time_htp, start_time_htb1, end_time_htb1, start_time_htb2, end_time_htb2, start_time_htb3, end_time_htb3]
                        labels = ["LightTonePracticeStart", "LightTonePracticeEnd", "LightToneBlock1Start", "LightToneBlock1End", "HeartTonePracticeStart", "HeartTonePracticeEnd", "HeartToneBlock1Start", "HeartToneBlock1End", "HeartToneBlock2Start", "HeartToneBlock2End", "HeartToneBlock3Start", "HeartToneBlock3End"]
                    
                    df_block_times = pd.DataFrame(list(zip(values, labels)), columns = ['time', "label"])
                    print(df_block_times)

                    # Change to participant processed dir 
                    df_block_times.to_csv("%s/raw_converted_to_txt/%s_block_times.txt" %(each_data_dir, id_tp), sep='\t', index = False)

                elif sum_diff_behav != 0:
                    print("ERROR: Unexpected trial order for behavioral data")
            elif sum_diff_ecg_ends != 0:
                print("ERROR: Unexpected trial order within ECG markers for starts vs ends")
        elif sum_diff_ecg != 0:
            print("ERROR: Unexpected trial order for ECG")

