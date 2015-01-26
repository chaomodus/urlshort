#!/bin/sh
echo "Starting urlshort."
cd /deploy
sleep 10s
python urlshort_app.py fig.ini
