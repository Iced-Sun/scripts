#!/bin/sh

cd /root

cave show installed-slots::installed | grep '/' |xargs -I '{}' cave contents '{}' | awk '{print $1}' |sort -u >managed_file.list

find / -mount -regextype posix-awk -regex '/run|/home|/root|/usr/src|/var/db/paludis|/var' -prune -o -print |sort -u >all_file.list

diff all_file.list managed_file.list | grep '<' > unmanaged.list
diff all_file.list managed_file.list | grep '>' > missing.list

