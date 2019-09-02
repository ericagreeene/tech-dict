#!/bin/bash
set -e

echo 'freezing...'
python freeze.py

echo 'deploying...'
cd build
echo thetechbuzzwords.com > CNAME
echo | surge
