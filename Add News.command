#!/bin/zsh
cd -- "${0:A:h}"
python3 tools/build_news.py --add
printf "\nPress Return to close."
read -r
