#!/bin/bash
set -e

echo 'freezing...'
python freeze.py

echo 'deploying...'
cd build
echo https://tech-dict.surge.sh > CNAME
surge
