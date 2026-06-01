#!/bin/dash

# persist a simple record of uptimes...

set -euo pipefail
set -x

script=/opt/local/bin/uptimes.sh
mono_sec=/opt/local/bin/mono_sec
service=/etc/systemd/system/uptimes.service
persist_dir=/var/local/uptimes

mkdir -p $(dirname $script)
tee $script <<EOF
#!/bin/dash

# persist a simple record of uptimes...

set -euo pipefail

get_mono_sec() {
    ${mono_sec}
}

EOF

tee -a $script <<"EOF"
get_now_sec() {
    date '+%s'
}

timestamp() {
    local sec=${1}
    #sec=${1:-$(get_now_sec)}
    date --date=@$sec '+%Y-%m-%d-%H%M-%S'
}


start_mono_sec=$(get_mono_sec)
#start_sec=$(get_now_sec)
#start_timestamp=$(timestamp $start_sec)

#now_filename=""
old_filename=""
persist() {
    local now_sec=$(get_now_sec)
    local now_timestamp=$(timestamp $now_sec)

    local now_mono_sec=$(get_mono_sec)
    local dur_sec=$((now_mono_sec - start_mono_sec))
    #dur_sec=$((now_sec - start_sec))
    local dur_sec0s=$(printf '%06d' $dur_sec)

    local start_timestamp=$(timestamp $((now_sec - dur_sec)) )

    local now_filename=${start_timestamp}__${now_timestamp}__${dur_sec0s}
    echo $dur_sec > $now_filename
    sync
    test -n "$old_filename" && rm $old_filename
    old_filename="$now_filename"
}

#if false ; then
#    echo start_sec: $start_sec
#    echo start_timestamp: $start_timestamp
#fi

while true ; do
    persist
    sleep 61
    #sleep 7
    #sleep 3
done

EOF

dash -n $script
chmod +x $script


tee ${mono_sec}.cc <<"EOF"
#include <time.h>
#include <inttypes.h>
#include <stdio.h>

int main() {
  struct timespec time;
  const int res = clock_gettime(CLOCK_MONOTONIC_COARSE, &time);
  printf("%jd\n", (intmax_t)time.tv_sec);
  return 0;
}

EOF

gcc ${mono_sec}.cc -o ${mono_sec}
rm ${mono_sec}.cc


mkdir -p $persist_dir
tee $service <<EOF
[Unit]
Description=Persist a simple record of uptimes
Documentation=file:${script},file:${persist_dir}
After=time-set.target

[Service]
Type=simple
ExecStart=${script}
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
