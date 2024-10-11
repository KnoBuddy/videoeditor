# -*- mode: python ; coding: utf-8 -*-
import sys
import platform

system = platform.system()

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],    
    datas=[
        ('gui.ui', '.'),
        ('fonts/digital-7 (mono).ttf', 'fonts'),
        ('icons/videoeditor_icon.ico', 'icons'),
        ('icons/videoeditor_icon.png', 'icons'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

# Set the icon parameter conditionally based on the OS
if system == 'Windows':
    icon_file = 'icons/videoeditor_icon.ico'
else:
    icon_file = None

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='VideoEditor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)
