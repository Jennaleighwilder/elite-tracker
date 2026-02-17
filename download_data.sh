#!/bin/bash
# Download data files for the elite tracker
# Run from project root: ./download_data.sh

set -e
mkdir -p data
cd data

echo "Downloading Skull and Bones (Wikipedia)..."
curl -sL -o skull_bones.html "https://en.wikipedia.org/wiki/List_of_Skull_and_Bones_members" || true

echo "Downloading Bilderberg (German - most comprehensive)..."
curl -sL -o bilderberg.html "https://www.feuerwehr-sasbach.de/wiki/Liste_von_Teilnehmern_an_Bilderberg-Konferenzen" || true

# Fallback: English Wikipedia if German fails
if [ ! -s bilderberg.html ]; then
  echo "Falling back to English Wikipedia for Bilderberg..."
  curl -sL -o bilderberg.html "https://en.wikipedia.org/wiki/List_of_Bilderberg_participants" || true
fi

echo "Downloading CFR Finding Aid..."
curl -sL -o cfr_finding_aid.pdf "http://arks.princeton.edu/ark:/88435/dsp011c18dj67m" || true

echo "Downloading Trilateral Commission finding aid..."
curl -sL -o trilateral_finding_aid.html "https://dimes.rockarch.org/collections/FVYj2u2ReLkppp2DZLYVs7" || true

echo ""
echo "Manual downloads required:"
echo "  1. Senate Report 1978: http://babel.hathitrust.org/cgi/pt?id=mdp.39015077914680"
echo "     -> Click Download -> Full PDF, save as data/senate_report_1978.pdf"
echo "  2. DUNL.org sample: https://DUNL.org/sample/ (if available)"
echo ""
echo "Done. Files in ./data/"
