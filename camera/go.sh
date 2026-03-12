#!/bin/bash


# 0 : ov5647 [2592x1944 10-bit GBRG] (/base/soc/i2c0mux/i2c@1/ov5647@36)
#     Modes: 'SGBRG10_CSI2P' : 640x480 [58.92 fps - (16, 0)/2560x1920 crop]
#                              1296x972 [46.34 fps - (0, 0)/2592x1944 crop]
#                              1920x1080 [32.81 fps - (348, 434)/1928x1080 crop]
#                              2592x1944 [15.63 fps - (0, 0)/2592x1944 crop]

# IMX708
size=" --width 1536 --height 864 "

#size=" --width 640 --height 480"
#size=" --width 1920 --height 1080"

thumb=""
#thumb=" --thumb=320:240:70 "

while true ; do
    echo
    dir=~/work/camera
    tag=${dir}/test5_$(date '+%Y-%m-%d-%H%M-%S')
    echo tag: $tag
    sudo rpicam-still --nopreview  --immediate  --quality 75  --rotation 180  $size  $thumb  --flicker-period 8333us --metadata ${tag}.txt  --output ${tag}.jpeg  --latest ${dir}/latest.jpeg
    #exiftool -b -ThumbnailImage  ${dir}/latest.jpeg > ${dir}/latest_thumbnail.jpeg
    sleep 1
    #sleep 2
done
