# Sasha Sommerfeldt
# SCIM Processed EDA Data Formatting
# Reads in individual-participant EDA data processed through Ledalab, extracts relevant columns
# and compiles all participants' data into a dataframe

import os
import pandas as pd

# Paths
physio_dir = '../../../../processed-data/tsst/psychophys'

# Read in data
filename_ending = '_tsst0000_eda_R1_era'
subfolder = 'eda_processed_through_ledalab'

participants_file = '../../../../subj_lists/T1_IDs.txt'
participant_list = pd.read_csv(participants_file, header=None, names=['ids']).astype(str)

exclude_participants = ['4010', '4017', '4018', '4073']
participants = participant_list[~participant_list.isin(exclude_participants)].dropna().reset_index()

timepoints = ['t1', 't2']
minutes = '2.5minute'

phase_list = ['BaselineStart', 'BaselineB', 'PrepStart', 'PrepB', 'SpeechStart', 'SpeechB',
              'MathStart', 'MathB', 'RecoveryStart', 'RecoveryB', 'RecoveryC', 'RecoveryD']

# Process EDA data for each participant and timepoint
for timepoint in timepoints:
    print(timepoint)
    # Filenaming convention: data domain _ timepoint _ data type _ specific variable
    # (pp = PsychoPhysiology)
    prefix = f'pp_{timepoint}_tsstEDAtonic_'
    new_names = [prefix + str(x[0]+1).zfill(2) for x in enumerate(phase_list)]
    print(new_names)
    # Create an empty dataframe to append each participant's data to
    df_tp = pd.DataFrame(columns = ['id', *new_names])
    for participant in participants['ids']:
        participant_timepoint = f'{participant}_{timepoint}'
        print(participant_timepoint)
        participant_dir = os.path.join(physio_dir, participant_timepoint, subfolder)
        outfile_participant = os.path.join(participant_dir, f'{participant_timepoint}_edaTonic_{minutes}.csv')

        ledalab_file = os.path.join(participant_dir, f'{participant_timepoint}{filename_ending}_{minutes}.xls')
        try:
            df_eda = pd.read_excel(ledalab_file, sheet_name=1)[['Event.Name', 'CDA.Tonic [muS]']]
        except FileNotFoundError:
            print(f'File not found for {participant_timepoint}')
            continue
        if len(df_eda['Event.Name']) != len(phase_list):
            print(f'Error: missing phases for {participant_timepoint}')
            continue
        # Add ID column with participant number and column with properly formatted (soon to be column) names
        df_eda = df_eda.assign(id=participant).assign(event=new_names)
        # Pivot to wide format
        df_wide = df_eda.pivot(index = 'id', columns='event', values='CDA.Tonic [muS]').reset_index()
        # Write out participant file
        df_wide.to_csv(outfile_participant, index=False)
        # Concatenate participant row to the timepoint dataframe
        df_tp = pd.concat([df_tp, df_wide], ignore_index=True)
    outfile_group = os.path.join(physio_dir, 'eda_output_group', f'scim_{timepoint}_edaTonic_{minutes}.csv')
    print(df_tp)
    # Write out summary file with all participants for the timepoint
    df_tp.to_csv(outfile_group, index=False)

