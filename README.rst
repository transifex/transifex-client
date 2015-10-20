
=============================
 Transifex Command-Line Tool
=============================

The Transifex Command-line Client is a command line tool that enables
you to easily manage your translations within a project without the need
of an elaborate UI system.

You can use the command line client to easily create new resources, map
locale files to translations and synchronize your Transifex project with
your local repository and vice verca. Translators and localization
managers can also use it to handle large volumes of translation files
easily and without much hassle.

Check the full documentation at
http://docs.transifex.com/client/


Installing
==========

You can install the latest version of transifex-client running ``pip
install transifex-client`` or ``easy_install transifex-client``
You can also install the `in-development version`_ of transifex-client
with ``pip install transifex-client==dev`` or ``easy_install
transifex-client==dev``.


Windows Machine Configuration
==========

In Windows installation, we copy the prebuilt Windows binary from ``win`` folder into ``Python\Scripts``.
For this to work, you'll have to built the binary using either ``build27.bat`` or ``build3.bat`` to create the binary for Python27/Python3
respectively.

For Windows machine that need to build the binary, simply install either Python27/Python3: make sure to check add Python.exe to path.
Also you will need to add ``Python\Scripts`` into PATH. This will make sure that you'll be able to call ``pip`` command to install other required Python packages.

Finally, you will also need to install PyInstaller using ``pip install pyinstaller``. Once that done, use ``build27.bat`` or ``build3.bat`` to create the binary for Python27/Python3
respectively.

.. _in-development version: http://github.com/transifex/transifex-client/tarball/master#egg=transifex-client-dev
