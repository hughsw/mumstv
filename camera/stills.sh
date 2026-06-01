#!/bin/dash

set -euo pipefail

set -x

dir=~/work/camera
size=" --width 4608 --height 2592 "
#size=" --width 3280 --height 2464 "
#size=" --width 1536 --height 864 "

while true ; do

    tag=${dir}/stills-01_$(date '+%Y-%m-%d-%H%M-%S')
    #  --raw
    #  --rotation 180
    sudo rpicam-still  --nopreview  --immediate  --quality 85  ${size}  --thumb 320:240:70 --metadata ${tag}.txt  --output ${tag}.jpeg  --latest ${dir}/latest.jpeg
    exiftool -b -ThumbnailImage  ${tag}.jpeg > ${tag}_thumb.jpeg
    ln -f -s ${tag}_thumb.jpeg ${dir}/latest_thumbnail.jpeg

    #sleep 1
done
