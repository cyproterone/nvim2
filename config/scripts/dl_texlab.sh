#!/usr/bin/env bash

set -eu
set -o pipefail


if [[ "$OS" == 'Darwin' ]]
then
  URI="$MAC_URI"
else
  URI="$LINUX_URI"
fi

get -- "$URI" | unpack -
mv -- './texlab' "$BIN"
chmod +x -- "$BIN"

