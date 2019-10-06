#!/bin/bash
set -e

echo 'freezing...'
python freeze.py

echo 'generating twitter cards'
python cards.py

echo 'deploying...'
firebase deploy
