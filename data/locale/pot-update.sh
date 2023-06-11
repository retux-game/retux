#!/bin/sh
rm retux.pot
cp datatext.pot retux.pot
xgettext -j -o retux.pot --foreign-user --keyword=pgettext:1c,2 --package-name="ReTux" --package-version="1.6.3" --msgid-bugs-address="diligentcircle@riseup.net" --add-comments="/" ../../retux.py
