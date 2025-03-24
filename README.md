# 打包命令
'''
nuitka --standalone --onefile \
       --macos-create-app-bundle \
       --macos-app-icon=icon.icns \
       --macos-app-name="MyApp" \
       --enable-plugin=pyqt5 \
       --include-qt-plugins=iconengines,imageformats,platforms,styles \
       --include-package=cv2 \
       --lto=no \
       --remove-output \
       main.py
'''
