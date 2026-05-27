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

sec() {
    date '+%s'
}

timestamp() {
    sec=${1:-$(date '+%s')}
    date --date=@$sec '+%Y-%m-%d-%H%M-%S'
}


start_sec=$(sec)
start_timestamp=$(timestamp $start_sec)
old_filename=""
persist() {
    now_sec=$(sec)
    now_timestamp=$(timestamp $now_sec)
    dur_sec=$((now_sec - start_sec))
    dur_sec0s=$(printf '%06d' $dur_sec)
    now_filename=${start_timestamp}__${now_timestamp}__${dur_sec0s}
    echo $dur_sec > $now_filename
    test -n "$old_filename" && rm $old_filename
    sync
    old_filename="$now_filename"
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


systemctl disable --now uptimes.service || true

systemctl daemon-reload
systemctl enable uptimes.service
systemctl start uptimes.service

set +x
echo
echo OK
