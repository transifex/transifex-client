.. image:: https://circleci.com/gh/transifex/transifex-client/tree/master.svg?style=shield&circle-token=33aafd984726261eff1b73278a0cf761382c478a
    :target: https://circleci.com/gh/transifex/transifex-client/tree/master
.. image:: https://ci.appveyor.com/api/projects/status/github/transifex/transifex-client?branch=master&svg=true
    :target: https://ci.appveyor.com/project/transifex/transifex-client/branch/master
.. image:: https://codecov.io/gh/transifex/transifex-client/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/transifex/transifex-client



=============================
 Transifex Command-Line Tool
=============================

The Transifex Command-line Tool enables you to manage your translations within a project without the need of an elaborate UI system.

You can use the command line tool to create new resources, map locale files to translations, and synchronize your Transifex project with your local repository. Translators and localization managers can use it to handle large volumes of translation files. The Transifex Command-line Tool can help to enable continuous integration workflows and can be run from CI servers like Jenkins and Bamboo.

Check the full documentation at http://docs.transifex.com/client/

Installing
==========

You can install the latest version of transifex-client running ``pip
install transifex-client`` or ``easy_install transifex-client``.


Build transifex-client for Windows
==================================

1. Download transifex-client sources via git or github archive.

   a. ``git clone https://github.com/transifex/transifex-client.git``
   b. Download and unpack https://github.com/transifex/transifex-client/archive/master.zip

2. Download and install Python_.

   At this step choose right version of python: 2 or 3 and x86 or x86-64 instruction set.

   Make sure pip marked for installation(default for latest installers).

3. Install PyInstaller_.

   Suppose that Python installed to ``C:\\Program Files\\Python35-32``

   Make ``python.exe`` accessible via PATH environment variable or cd to directory containing python.exe.

   ::

     python -m pip install pyinstaller

   This command will install ``PyInstaller`` package and its dependencies.

4. Build ``transifex-client`` distribution.

   Change directory to transifex-client folder and run command:

   ::

     python -m PyInstaller contrib/tx.spec
     # or
     pyinstaller contrib/tx.spec

5. ``tx.exe``

   ``dist/tx.exe`` will be created as the result of build process.


.. _Python: https://www.python.org/downloads/windows/
.. _PyInstaller: http://www.pyinstaller.org
