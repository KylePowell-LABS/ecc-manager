#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT_DIR_QUOTED="$(printf "%q" "${ROOT_DIR}")"
BIN_DIR="${HOME}/.local/bin"

mkdir -p "${BIN_DIR}"

cat > "${BIN_DIR}/ecc-use" <<EOF
#!/usr/bin/env bash
cd ${ROOT_DIR_QUOTED}
exec python3 -m ecc_manager.cli "\$@"
EOF

cat > "${BIN_DIR}/ecc-manager" <<EOF
#!/usr/bin/env bash
cd ${ROOT_DIR_QUOTED}
exec python3 -m ecc_manager.server "\$@"
EOF

chmod +x "${BIN_DIR}/ecc-use" "${BIN_DIR}/ecc-manager"

echo "Installed:"
echo "  ${BIN_DIR}/ecc-use"
echo "  ${BIN_DIR}/ecc-manager"
echo
echo "Make sure ${BIN_DIR} is on PATH."
