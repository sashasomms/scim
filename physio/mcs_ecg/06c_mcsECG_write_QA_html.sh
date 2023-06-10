#!/usr/bin/env bash
# Sasha Sommerfeldt 
# 2022

# Writes html pages for quality analysis (using plots and parsed text from 06a and 06b)

processedDir='../../processed-data/interoception/psychophys'
outDir="${processedDir}/ecgQA/html"
# HTML templates
participant_template='html_templates/mcsECG_participant_template.html'
chunk_template='html_templates/mcsECG_group_chunk_template.html'
group_template='html_templates/mcsECG_group_stub_template.html'


id_tp_dirs=`ls -d $processedDir/4???_t[12]`

# Start the top of the group template
cat $group_template > ${outDir}/all.html


for dir in $id_tp_dirs ; do
	echo
	id_tp=`basename $dir`
	echo $id_tp
	tp=`echo $id_tp | awk -F_ '{print $2}'`
	
	block_timing_labels=`cat $dir/raw_converted_to_txt/*_block_times.txt | awk '{print $2}' | tail -n-1`
	block_timing_labels_parsed=''
	for l in $block_timing_labels ; do
		block_timing_labels_parsed="${block_timing_labels_parsed} \n<th>${l}</th>"
	done
	block_timing_times=`cat $dir/raw_converted_to_txt/*_block_times.txt | awk '{print $1}' | tail -n-1`
	block_timing_times_parsed=''
	for t in $block_timing_times ; do
		block_timing_times_parsed="${block_timing_times_parsed} \n<td>${t}</td>"
	done

	people=`cat $processedDir/ecgQA/quality_notes/people.txt | grep $id_tp`
	people_parsed=''
	for p in $people ; do
		people_parsed="${people_parsed} \n<td>${p}</td>"
	done

	# Create the html page for this participant by replacing parts of participant_template
	cat $participant_template | sed s%ID_TP%${id_tp}%g | sed s%BLOCK_TIMING_TIMES%"${block_timing_times_parsed}"%g | sed s%BLOCK_TIMING_LABELS%"${block_timing_labels_parsed}"%g  | sed s%FOLKS%"${people_parsed}"%g > ${outDir}/${id_tp}.html
	echo "Created ${outDir}/${id_tp}.html"

	cat $chunk_template | sed s%ID_TP%${id_tp}%g | sed s%BLOCK_TIMING_TIMES%"${block_timing_times_parsed}"%g | sed s%BLOCK_TIMING_LABELS%"${block_timing_labels_parsed}"%g | sed s%FOLKS%"${people_parsed}"%g >> ${outDir}/all.html
	echo "Appended $id_tp to ${outDir}/all.html"


done
