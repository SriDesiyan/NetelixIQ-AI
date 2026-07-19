#!/bin/bash
# =============================================================================
# NetElixIQ AI — Hackathon Pipeline Entry Point
# AIgnition 3.0 Hackathon Submission
# =============================================================================
#
# Usage:
#   ./run.sh [DATA_DIR] [MODEL_PATH] [OUTPUT_PATH]
#
# Defaults:
#   DATA_DIR    = ./data
#   MODEL_PATH  = ./pickle/model.pkl
#   OUTPUT_PATH = ./output/predictions.csv
#
# What this script does:
#   1. Validates arguments and environment
#   2. Reads all CSVs from DATA_DIR (auto-detects channels)
#   3. Engineers time-series features
#   4. Loads the committed pre-trained model from MODEL_PATH
#   5. Generates 30/60/90-day probabilistic revenue forecasts (P10/P50/P90)
#   6. Writes predictions CSV to OUTPUT_PATH
#
# Requirements:
#   - Python 3.11+
#   - pip install -r requirements.txt
# =============================================================================

set -euo pipefail

# ── Resolve arguments with defaults ──────────────────────────────────────────
DATA_DIR="${1:-./data}"
MODEL_PATH="${2:-./pickle/model.pkl}"
OUTPUT_PATH="${3:-./output/predictions.csv}"

# ── Terminal colours ──────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Colour

echo -e "${CYAN}${BOLD}"
echo "============================================================"
echo "  NetElixIQ AI — Prediction Pipeline"
echo "  AIgnition 3.0 Hackathon"
echo "============================================================"
echo -e "${NC}"
echo -e "  ${YELLOW}DATA_DIR   :${NC} ${DATA_DIR}"
echo -e "  ${YELLOW}MODEL_PATH :${NC} ${MODEL_PATH}"
echo -e "  ${YELLOW}OUTPUT_PATH:${NC} ${OUTPUT_PATH}"
echo ""

# ── Validate DATA_DIR ─────────────────────────────────────────────────────────
if [ ! -d "${DATA_DIR}" ]; then
    echo -e "${RED}[ERROR] DATA_DIR not found: ${DATA_DIR}${NC}"
    echo "  Create it and add your marketing CSVs, or use the sample data:"
    echo "    cp -r data/sample/* data/"
    exit 1
fi

# Count CSVs recursively in a cross-platform way (avoids find/wc conflicts on Windows path)
CSV_COUNT=0
if command -v python &>/dev/null || command -v python3 &>/dev/null; then
    PY_CMD="python"
    command -v python &>/dev/null || PY_CMD="python3"
    CSV_COUNT=$(${PY_CMD} -c "
import glob, os
fs = glob.glob(os.path.join('${DATA_DIR}', '**', '*.csv'), recursive=True) + glob.glob(os.path.join('${DATA_DIR}', '**', '*.CSV'), recursive=True)
print(len(set([f for f in fs if os.path.isfile(f)])))
" 2>/dev/null || echo "0")
else
    # Simple shell glob fallback
    for f in "${DATA_DIR}"/*.csv "${DATA_DIR}"/*.CSV "${DATA_DIR}"/*/*.csv "${DATA_DIR}"/*/*.CSV; do
        [ -f "$f" ] && ((CSV_COUNT++))
    done
fi

if [ "${CSV_COUNT}" -eq 0 ]; then
    echo -e "${RED}[ERROR] No CSV files found in: ${DATA_DIR}${NC}"
    echo "  Expected: Google Ads, Meta Ads, Microsoft Ads, Shopify, or GA4 exports"
    exit 1
fi
echo -e "${GREEN}[OK]${NC} Found ${CSV_COUNT} CSV file(s) in ${DATA_DIR}"

# ── Validate MODEL_PATH ───────────────────────────────────────────────────────
if [ ! -f "${MODEL_PATH}" ]; then
    echo -e "${RED}[ERROR] Model file not found: ${MODEL_PATH}${NC}"
    echo "  Expected: pickle/model.pkl (committed to repo)"
    echo "  To regenerate: python scripts/train_model.py"
    exit 1
fi
echo -e "${GREEN}[OK]${NC} Model found: ${MODEL_PATH}"

# ── Check Python ──────────────────────────────────────────────────────────────
if ! command -v python &>/dev/null && ! command -v python3 &>/dev/null; then
    echo -e "${RED}[ERROR] Python not found. Install Python 3.11+${NC}"
    exit 1
fi

PYTHON_CMD="python"
if ! command -v python &>/dev/null; then
    PYTHON_CMD="python3"
fi

PYTHON_VERSION=$(${PYTHON_CMD} -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo -e "${GREEN}[OK]${NC} Python ${PYTHON_VERSION}"

# ── Check dependencies ────────────────────────────────────────────────────────
echo -e "\n${YELLOW}Checking dependencies...${NC}"
${PYTHON_CMD} -c "import pandas, numpy, sklearn, lightgbm, pickle" 2>/dev/null || {
    echo -e "${YELLOW}[WARN] Some dependencies missing. Installing...${NC}"
    pip install -r requirements.txt --quiet
}
echo -e "${GREEN}[OK]${NC} Dependencies ready"

# ── Create output directory ───────────────────────────────────────────────────
OUTPUT_DIR=$(dirname "${OUTPUT_PATH}")
mkdir -p "${OUTPUT_DIR}"
echo -e "${GREEN}[OK]${NC} Output directory: ${OUTPUT_DIR}"

# ── Run prediction pipeline ───────────────────────────────────────────────────
echo -e "\n${CYAN}${BOLD}Running prediction pipeline...${NC}"
echo "------------------------------------------------------------"

${PYTHON_CMD} scripts/predict.py \
    "${DATA_DIR}" \
    "${MODEL_PATH}" \
    "${OUTPUT_PATH}"

EXIT_CODE=$?

# ── Result ────────────────────────────────────────────────────────────────────
echo "------------------------------------------------------------"
if [ ${EXIT_CODE} -eq 0 ]; then
    echo -e "\n${GREEN}${BOLD}[SUCCESS] Predictions written to: ${OUTPUT_PATH}${NC}"
    if command -v wc &>/dev/null; then
        PRED_ROWS=$(tail -n +2 "${OUTPUT_PATH}" 2>/dev/null | wc -l)
        echo -e "  ${GREEN}Forecast rows: ${PRED_ROWS}${NC}"
    fi
    echo -e "\n  Preview (first 3 rows):"
    ${PYTHON_CMD} -c "
import pandas as pd, sys
df = pd.read_csv('${OUTPUT_PATH}')
print(df[['horizon_days','date','revenue_p10','revenue_p50','revenue_p90','confidence']].head(3).to_string(index=False))
" 2>/dev/null || head -4 "${OUTPUT_PATH}"
    echo ""
else
    echo -e "\n${RED}${BOLD}[FAILED] Prediction pipeline exited with code ${EXIT_CODE}${NC}"
    exit ${EXIT_CODE}
fi
