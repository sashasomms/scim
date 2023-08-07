#!/usr/bin/env bash

# Dependency: pip install bioread (https://pypi.org/project/bioread/)
# Converts biopac (.acq) format data to .txt and .mat files

raw_data_dir=../../../raw-data/tsst/psychophys
output_dir=../../../processed-data/tsst/psychophys
raw_data_subfolders=`ls -d ${raw_data_dir}/[348][0-9][0-9][0-9]_t[12]`

for dir in $raw_data_subfolders ; do
  subject_timepoint=`basename ${dir}`
  echo ${subject_timepoint}
  subject_timepoint_output_dir=${output_dir}/${subject_timepoint}/raw_converted_to_txt
  mkdir -p ${subject_timepoint_output_dir}
  for input_file in ${dir}/*acq ; do
    input_filename=$(basename ${input_file})
    output_file=${subject_timepoint_output_dir}/${input_filename%.*}
    echo ${output_file}
    if [[ ! -f ${output_file}_eda.txt ]]; then
      acq2txt --channel-indexes=1 ${input_file} | tail -n +2 > ${output_file}_rsp.txt # respiration
      acq2txt --channel-indexes=2 ${input_file} | tail -n +2 > ${output_file}_eda.txt # eda
      acq2txt --channel-indexes=3 ${input_file} | tail -n +2 > ${output_file}_ecg.txt # ecg
    else
      echo "Data txt output file already exists, skipping..."
    fi
    if [[ ! -f ${output_file}.mat ]]; then
      acq2mat ${input_file} ${output_file}.mat
    else
      echo "Data mat output file already exists, skipping..."
    fi
    if [[ ! -f ${output_file}_markers.txt ]]; then
      acq_markers -o ${output_file}_markers.txt ${input_file}
    else
      echo "Event markers output file already exists, skipping..."
    fi
  done
done
