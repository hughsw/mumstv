#!/bin/dash

set -euo pipefail

set -x

dir=~/work/camera
size=" --width 4608 --height 2592 "
#size=" --width 3280 --height 2464 "
#size=" --width 1536 --height 864 "

rm -f ${dir}/latest.jpeg

while true ; do

    tag=${dir}/stills-12_$(date '+%Y-%m-%d-%H%M-%S')

    rpicam-still \
        --nopreview \
        --quality 93 \
        --flicker-period 8333us \
        --lens-position 0.05 \
        --shutter 800ms \
        --gain 16.0 \
        ${size} \
        --thumb 320:240:70 \
        --timelapse 3000ms \
        --timeout 0 \
        --encoding jpg \
        --output "${tag}_%04d.jpeg" \
        --metadata "${tag}.json" \
        --latest ${dir}/latest.jpeg


    #  --raw
    #  --rotation 180
    #        --autofocus-mode continuous \
    #        --autofocus-window 0.33,0.33,0.67,0.67 \
    #        --autofocus-on-capture \
    #        --output ${tag}.jpeg \
    #        --datetime 1 \
    #         --timeout 20sec \
    #         --immediate \


    exiftool -b -ThumbnailImage  ${tag}.jpeg > ${tag}_thumb.jpeg
    ln -f -s ${tag}_thumb.jpeg ${dir}/latest_thumbnail.jpeg

    #sleep 1
done
