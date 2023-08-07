
# This script is for quality analysis of TSST events:
# Events were key-presses during the procedure.
# They may be missing or their timing off due to various factors
# So here we check to make sure all are accounted for and occur close enough to the expected timing

import pandas as pd
import sys
import glob
import os

# Set a 5 second threshold for how far forms can be off from protocol times
threshold_forms = 5.000

# Setting up the path to the processed data directory
processedDir = '../../../processed-data/tsst/psychophys'
dataDirs = sorted(glob.glob('%s/[4]???_t[12]' % processedDir))

# Phases of the TSST
phases = ["Baseline", "Prep", "Speech", "Math", "Recovery"]


exclude_ids = []
time_data = []
error_data = []
timing_error_data = []

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
	if subjID_timepoint not in exclude_ids :
		if os.path.isfile('%s/%s/%s/%s_tsst0000_simplifiedMarkers.txt' % (processedDir, subjID_timepoint, 'raw_converted_to_txt', subjID_timepoint)) :
			df_simplified_markers = pd.read_csv('%s/%s/%s/%s_tsst0000_simplifiedMarkers.txt' % (processedDir, subjID_timepoint, 'raw_converted_to_txt', subjID_timepoint), sep='\t')
			for phase in phases :
				n_Starts = len(df_simplified_markers[df_simplified_markers['name'] == "%sStart" %phase])
				if n_Starts == 1 :
					phaseThere = df_simplified_markers['name'].isin([("%sStart" %phase)]).any()
					if phaseThere :
						phaseStartTime = float(df_simplified_markers['time'][df_simplified_markers['name'] == '%sStart' %phase])
						phaseEndTime = phaseStartTime + 300 ## Most phases are 5 minutes long. 60 s * 5 min = 300
						n_expectedForms = 2
						if phase == "Recovery" :
							phaseEndTime = phaseStartTime + 600 ## Recovery is 10 minutes long. 60 s * 10 min = 600
							n_expectedForms = 4
						dfTemp = df_simplified_markers[df_simplified_markers['time'] >= phaseStartTime]
						dfPhase = dfTemp[dfTemp['time'] < phaseEndTime]
						# Between phaseStart and phaseEnd: count formStart and formEnds
						# Number of FormStarts
						n_FormStarts = len(dfPhase[dfPhase['name'] == "FormStart"])
						# Number of FormEnds
						n_FormEnds = len(dfPhase[dfPhase['name'] == "FormEnd"])
						#If it's not the expected number throw a warning, log in file
						if n_FormStarts != n_expectedForms:
							print('Error, found %s Form Starts for %s' %(n_FormStarts, phase))
							error_text = "%s FormStarts" %n_FormStarts
							error_data.append([subjID_timepoint, phase, error_text])
						if n_FormEnds != n_expectedForms:
							print('Error, found %s Form Ends for %s' %(n_FormEnds, phase))
							error_text = "%s FormEnds" %n_FormEnds
							error_data.append([subjID_timepoint, phase, error_text])

						# If all is well with number of presses, calculate timings
						if n_FormStarts == n_expectedForms and n_FormEnds == n_expectedForms:
							form_num = 1
							for f in dfPhase['nid'][dfPhase['name'] == "FormStart"] :
								s = float(dfPhase['time'][dfPhase['nid'] == f])
								e = float(dfPhase['time'][dfPhase['nid'] == f + 1])
								# Calculate time from phaseStart to each formStart press
								time_FormStart = (s - phaseStartTime)/60
								if form_num == 1:
									expected_FormStart = 2.00
								if form_num == 2:
									expected_FormStart = 4.50
								if form_num == 3:
									expected_FormStart = 7.00
								if form_num == 4:
									expected_FormStart = 9.50
								sec_off = (time_FormStart - expected_FormStart)*60.0
								# Calculate time between formStart and formEnd for each pair
								sec_btwnForms = (e - s)
								time_data.append([subjID_timepoint, phase, form_num, time_FormStart, sec_off, sec_btwnForms])
								# If formStart is more than threshold from expected time
								#if not (((time_FormStart > (2.000 - threshold_forms)) and (time_FormStart < (2.000 + threshold_forms))) or ((time_FormStart > (4.500 - threshold_forms)) and (time_FormStart < (4.500 + threshold_forms))) or ((time_FormStart > (7.000 - threshold_forms)) and (time_FormStart < (7.000 + threshold_forms))) or ((time_FormStart > (9.500 - threshold_forms)) and (time_FormStart < (9.500 + threshold_forms)))):
								if sec_off > threshold_forms:
									print("Bad form time %s" %phase)
									timing_error_data.append([subjID_timepoint, phase, form_num, time_FormStart, sec_off, sec_btwnForms])
								form_num += 1
				else:
					if n_Starts > 1 :
						print("Error, multiple button presses to start %s" %phase)
						error_data.append([subjID_timepoint, phase, "multiple phase starts"])
		else:
			print("Needs simplify marker script run.")

# convert time and error lists to data frames and write them out
df_time = pd.DataFrame(time_data, columns = ["id_tp", "phase", "form_number", "time_form_start_min", "sec_off_expected", "time_btwn_forms_sec"])
df_time.to_csv('%s/form_timing_data.csv' % (processedDir), index=False)

df_error = pd.DataFrame(error_data, columns = ["id_tp", "phase", "marker_error"])
df_error.to_csv('%s/marker_errors.csv' % (processedDir), index=False)

df_timing_error = pd.DataFrame(timing_error_data, columns = ["id_tp", "phase", "form_number", "time_form_start_min", "sec_off_expected", "time_btwn_forms_sec"])
df_timing_error.to_csv('%s/timing_errors.csv' % (processedDir), index=False)
