# -*- mode: python -*-

block_cipher = None


def _get_data_files(path):
	rfiles = []
	len_path = len(path)
	for root, dirnames, files in os.walk(path):
		for file in files:
			ext = os.path.splitext(file)[1]
			if ext in ('.pem'):
				print 'adding ', file
				ffile = os.sep.join((root, file))
				target = file
				print target, ffile
				rfiles.append((target, ffile, 'DATA'))
				continue

	return rfiles

a = Analysis(['tx'],
			 pathex=['C:\\code\\transifex-client'],
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