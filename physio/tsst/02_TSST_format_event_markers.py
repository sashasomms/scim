
# This script is designed to 
# Pull out only the columns we want from the markers.txt file
# Translate key presses to meaningful labels

import pandas as pd
import sys
import glob
import os

# Set a 5 second threshold for how far forms can be off from protocol times
threshold_forms = 5.000
print(threshold_forms)

# Setting up the path to the processed data directory
processedDir = '../../processed-data/tsst/psychophys'
dataDirs = sorted(glob.glob('%s/[4]???_t[12]' % processedDir))

# Phases of the TSST
phases = ["Baseline", "Prep", "Speech", "Math", "Recovery"]

exclude_ids = []
error_data = []

# Set up a dictionary with meaningful names for type_codes
type_dictionary = {'usr1':'BaselineStart',
					'usr2':'PrepStart',
					'usr3':'SpeechStart',
					'usr4':'MathStart',
					'usr5':'RecoveryStart',
					'usr7':'ERROR',
					'usr8':'FormStart',
					'usr9':'FormEnd'}

for each_dataDir in dataDirs :
	print('')
	print(each_dataDir)
	subjID_timepoint = os.path.basename(each_dataDir)
	print(subjID_timepoint)
	### Pare the markers file down to only what we need in a clean format
	if subjID_timepoint not in exclude_ids :
		if os.path.isfile('%s/%s/%s/%s_tsst0000_simplifiedMarkers.txt' % (processedDir, subjID_timepoint, 'raw_converted_to_txt', subjID_timepoint)) :
			print('%s already completed marker simplification, skipping' %subjID_timepoint)
		else :
			# Read in the markers dataframe
			df_markers = pd.read_csv('%s/%s/%s/%s_tsst0000_markers.txt' % (processedDir, subjID_timepoint, 'raw_converted_to_txt', subjID_timepoint), sep='\t')
			# Check for missing phase starts
			for phase in phases :
				print(phase)
				phaseThere = df_markers['label'].str.contains(phase).any()
				if phaseThere :
					print("Has %s start marker" %phase)
				else:
					print("Error, missed button press to start %s" %phase)
					error_data.append([subjID_timepoint, phase, "no phase start"])

			# Make a new 'event' variable/column with the meaningful names using that dictionary
			df_markers['event'] = df_markers['type_code'].map(type_dictionary)
			df_markers['nid'] = df_markers.index
			columnsToTake = ['nid', 'time (s)', 'event']
			# Subset out only the nid, time and event columns, that's all we need
			df_simplified_markers = df_markers[columnsToTake][1:]
			# Remove the space and (s) part from the time column, programs don't like that
			df_simplified_markers.rename(columns = {'time (s)':'time', 'event':'name'}, inplace = True)

			# Write out the simplified file to the participant's folder
			df_simplified_markers.to_csv('%s/%s/%s/%s_tsst0000_simplifiedMarkers.txt' % (processedDir, subjID_timepoint, 'raw_converted_to_txt', subjID_timepoint), sep='\t', index=False)
