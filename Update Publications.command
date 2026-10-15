#!/bin/zsh
cd -- "${0:A:h}"
python3 tools/update_publications.py
printf "\nPress Return to close."
read -r
