#!/bin/sh
for fn in `ls *.png`; do
    convert -resize "400x400" $fn $fn
done
