#!/usr/bin/env bash
# Sasha Sommerfeldt 
# November 2022
# Write lines to paste into a windows command prompt (CMETX only on Windows)
# Ew Windows

# Change these as needed
outfile="07b_mcsECG_run_cmetx_batch_submit_to_windowsCMD.bat"

ddir="../../processed-data/interoception/psychophys"
# Data directory on Windows
wddir="..\..\processed-data\interoception\psychophys"
pfiles=`ls -f ${ddir}/4[0-9][0-9][0-9]_t[12]/cmetx_output_ibis/*Block*R1.txt`

# Start a blank outfile
cat "" > ${outfile}
for pfile in $pfiles ; do
    echo
    echo "$pfile"
    pfile_notxt=`echo $pfile | sed s:.txt::g`
    pfile_clean="${pfile_notxt}_clean.txt"
    if [ -f "$pfile_clean" ] ; then
      echo "Cleaned version exists: $pfile_clean"
      # If there's a clean version use that instead
      pfile=${pfile_clean}
    fi
    # Convert to have Windows line endings
    unix2dos ${pfile}
    # Remove the .txt from the end of the file name bc its what cmetx wants
    pfile_notxt_windows=`echo $pfile | sed s:.txt::g | sed s%/study%Y:%g | sed 's:/:\\\:g' `
    echo $pfile_notxt_windows
    # append to the .bat outfile
    echo "CMetX ${pfile_notxt_windows} -o ${wddir}\cmetx_output_group\INTEROCEPTION_ECG_OUTPUT_R1" >> ${outfile}
done
