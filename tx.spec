# -*- mode: python -*-

block_cipher = None


a = Analysis(['tx'],
             pathex=['C:\\code\\transifex\\transifex-client'],
             binaries=None,
             datas=None,
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None,
             excludes=None,
             win_no_prefer_redirects=None,
             win_private_assemblies=None,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
		  a.scripts,
		  a.binaries + [('txclib\cacert.pem', 'txclib\cacert.pem', 'DATA')],
		  a.zipfiles,
		  a.datas,
		  name='tx',
		  debug=False,
		  strip=None,
		  upx=True,
		  console=True,
		  icon='tx-logo.ico')
coll = COLLECT(exe,
           a.binaries,
           a.zipfiles,
           a.datas,
           strip=None,
           upx=True,
           name='tx')
