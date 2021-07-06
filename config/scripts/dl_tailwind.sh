#!/usr/bin/env bash

set -eu
set -o pipefail


get --type '.zip' "$URI" | unpack -
printf '%s\n\n' '#!/usr/bin/env node' > "$BIN_PATH"
cat -- './extension/dist/extension/index.js' >> "$BIN_PATH"
chmod +x -- "$BIN_PATH"
