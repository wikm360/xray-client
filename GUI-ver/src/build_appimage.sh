#!/bin/bash

# دریافت appimagetool در صورت نیاز
if [ ! -f appimagetool ]; then
    wget https://github.com/AppImage/AppImageKit/releases/latest/download/appimagetool-x86_64.AppImage -O appimagetool
    chmod +x appimagetool
fi

# ساخت AppImage
./appimagetool AppDir
