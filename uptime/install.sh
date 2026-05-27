#!/bin/dash

# persist a simple record of uptimes...

set -euo pipefail
set -x

exe=/opt/local/bin/uptimes.sh
service=/etc/systemd/system/uptimes.service
persist_dir=/var/local/uptimes

mkdir -p $(dirname $exe)
tee $exe <<"EOF"
#!/bin/dash

# persist a simple record of uptimes...

set -euo pipefail

get_now_sec() {
    date '+%s'
}

timestamp() {
    sec=${1:-$(get_now_sec)}
    date --date=@$sec '+%Y-%m-%d-%H%M-%S'
}


start_sec=$(get_now_sec)
start_timestamp=$(timestamp $start_sec)

now_filename=""
old_filename=""
persist() {
    now_sec=$(get_now_sec)
    now_timestamp=$(timestamp $now_sec)
    dur_sec=$((now_sec - start_sec))
    dur_sec0s=$(printf '%06d' $dur_sec)

    test -n "$old_filename" && rm $old_filename
    old_filename="$now_filename"
    now_filename=${start_timestamp}__${now_timestamp}__${dur_sec0s}
    echo $dur_sec > $now_filename
    sync
}

if false ; then
    echo start_sec: $start_sec
    echo start_timestamp: $start_timestamp
fi

while true ; do
    persist
    sleep 61
    #sleep 7
    #sleep 3
done

EOF

dash -n $exe
chmod +x $exe


mkdir -p $persist_dir
tee $service <<EOF
[Unit]
Description=Persist a simple record of uptimes
Documentation=file:${exe},file:${persist_dir}
After=time-set.target

[Service]
Type=simple
ExecStart=${exe}
Restart=on-failure
WorkingDirectory=${persist_dir}

[Install]
WantedBy=default.target

EOF


systemctl daemon-reload
systemctl disable --now uptimes.service || true
systemctl enable uptimes.service
systemctl start uptimes.service

set +x
echo
echo OK
