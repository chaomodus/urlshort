#!/bin/bash
echo "URLshort DB setups."
echo "CREATE DATABASE urlshort;" | gosu postgres postgres --single
gosu postgres postgres --single urlshort < /deploy/urlshort.sql
