#!/bin/dash

# Fail loudly
set -euo pipefail
trap 'rc=$?;set +ex;trap - EXIT;[ $rc -eq 0 ] && echo "\nOK" && exit 0 || fail="\n*** fail *** : code $rc : $DIR/$SCRIPT $ARGS\n" && echo "$fail" 1>&2 && echo "$fail" && exit $rc' EXIT
SOURCE="$(lsof -p $$ -Fn0 | tail -1 | cut -c 2- | tr -d "\0")"
DIR="$(cd "$(dirname "${SOURCE}")" && pwd)"
SCRIPT="$(basename "${SOURCE}")"
ARGS="$*"

#echo DIR: $DIR
#echo SCRIPT: $SCRIPT
#echo ARGS: $ARGS

name="camera-setup"


logdir="${name}-logs"
mkdir -p "$logdir"

{
    set -x

    server_path=${DIR}/mjpeg_server.py
    server_unit=mjpeg_server.service

    #server_unit_path="~/.config/systemd/user/$server_unit"

    tee ~/.config/systemd/user/$server_unit <<EOF
[Unit]
Description=Serve MJPEG video from a camera
Documentation=file:$server_path
After=network-online.target

[Service]
Type=simple
#User=hugh
#Group=video
ExecStart=$server_path
Restart=always
RestartSec=21
KillMode=mixed
#StandardOutput=journal
#StandardError=journal

[Install]
WantedBy=default.target

EOF

    systemctl --user daemon-reload
    systemctl --user disable --now $server_unit || true
    systemctl --user enable $server_unit
    systemctl --user start  $server_unit

} 2>&1 | tee "${logdir}"/${name}_$(date '+%Y-%m-%d-%H%M-%S').log
