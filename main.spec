# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(['main.py'],
             pathex=["/Users/eremin/Yandex.Disk.localized/Project_pyqt5"],
             binaries=[],
             datas=[("/Users/eremin/Yandex.Disk.localized/Project_pyqt5/splash.png", "."), 
             ("/Users/eremin/Yandex.Disk.localized/Project_pyqt5/vector_1.jpeg", "."), 
             ("/Users/eremin/Yandex.Disk.localized/Project_pyqt5/vector_2.jpeg", "."), 
             ("/Users/eremin/Yandex.Disk.localized/Project_pyqt5/vector_3.jpeg", "."), 
             ("/Users/eremin/Yandex.Disk.localized/Project_pyqt5/vector_4.jpeg", "."), 
             ("/Users/eremin/Yandex.Disk.localized/Project_pyqt5/vector_5.jpeg", "."), 
             ("/Users/eremin/Yandex.Disk.localized/Project_pyqt5/vector_6.jpeg", "."), 
             ("/Users/eremin/Yandex.Disk.localized/Project_pyqt5/vector_7.jpeg", "."), 
             ("/Users/eremin/Yandex.Disk.localized/Project_pyqt5/cash_data.db", "."), 
             ("/Users/eremin/Yandex.Disk.localized/Project_pyqt5/Watch_cash.ui", "."), 
             ("/Users/eremin/Yandex.Disk.localized/Project_pyqt5/lang.txt", "."), 
             ("/Users/eremin/Yandex.Disk.localized/Project_pyqt5/currencies_ru.csv", "."), 
             ("/Users/eremin/Yandex.Disk.localized/Project_pyqt5/currencies_en.csv", ".")],
             hiddenimports=[],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,  
          [],
          name='Watch_cash',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None,
          icon="/Users/eremin/Yandex.Disk.localized/Project_pyqt5/icon.png")
