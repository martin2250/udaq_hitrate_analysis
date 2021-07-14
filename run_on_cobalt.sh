#!/bin/bash

COBALT=cobalt08
ROOTDIR=/home/mpittermann/analyze_hitbuffer/
SCRATCHDIR=/scratch/mpittermann/analyze_hitbuffer/

# sync code
rsync -av --delete --filter=':- .gitignore' $PWD/ $COBALT:$ROOTDIR

# run analysis
ssh $COBALT "source ~/source_python37.sh && cd $ROOTDIR && cat files_2021.txt | parallel -j 16 python3 read_data.py | gzip > $SCRATCHDIR/result.json.gz"
