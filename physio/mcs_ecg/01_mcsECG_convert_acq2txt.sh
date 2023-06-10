#!/usr/bin/env bash
# Sasha Sommerfeldt
# Convert ECG channel signal from acqknowledge files (Biopac software) to simple txt files 
# Dependency: acq2txt comes from bioread https://github.com/uwmadison-chm/bioread

raw_data_dir=../../raw-data/interoception/psychophys
output_dir=../../processed-data/interoception/psychophys
raw_data_subfolders=`ls -d ${raw_data_dir}/[0-9][0-9][0-9][0-9]_t[12]`
# Specify channel for ECG
channel_number='0'

for dir in $raw_data_subfolders ; do
  subject_timepoint=`basename ${dir}`
  echo ${subject_timepoint}
  # Output directory path w/ subfolder
  subject_timepoint_output_dir=${output_dir}/${subject_timepoint}/raw_converted_to_txt
  # Make output subfolder
  mkdir -p ${subject_timepoint_output_dir}
  for input_file in ${dir}/*acq; do
    input_filename=$(basename ${input_file})
    # Output filename uses input filename with ending removed
    output_file=${subject_timepoint_output_dir}/${input_filename%.*}
        # If the output file doesn't already exist
      if [[ ! -f ${output_file}_ecg.txt ]]; then
        echo "Beginning ${output_file}"
        # Convert acqknowledge to text file
        acq2txt --channel-indexes=${channel_number} ${input_file} | tail -n +2 > ${output_file}_ecg.txt
        echo 'Completed.'
      else
        echo "${output_file}_ecg.txt already exists, skipping..."
      fi
  done
done
