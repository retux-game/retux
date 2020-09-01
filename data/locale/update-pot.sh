#!/bin/sh
rm retux.pot
cp timeline.pot retux.pot
xgettext -j -o retux.pot --msgid-bugs-address="diligentcircle@riseup.net" ../../retux.py
