#!/bin/bash

if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

/etc/init.d/apache2 restart

pushd src &>/dev/null
last_pid=$(ps auxwww | grep 'python daemon.py' | grep -v grep | perl -lane'print $F[1]')
if [[ ! -z "$last_pid" ]] ; then
    kill $last_pid
fi

python daemon.py &>/tmp/snatch.log &
disown $!
popd &>/dev/null
