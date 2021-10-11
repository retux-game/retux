This file has been dedicated to the public domain, to the extent
possible under applicable law, via CC0. See
http://creativecommons.org/publicdomain/zero/1.0/ for more
information. This file is offered as-is, without any warranty.

========================================================================


HOW TO RUN

If you have downloaded a version of the game designated for a particular
system, simply run the executable.

To run the source code, you will need Python 3.6 or later
<https://www.python.org>. You will also need the dependencies listed in
requirements.txt, which you can install automatically by using the
following command:

    python3 -m pip install -r requirements.txt

Once you have installed the dependencies, you can start the game by
running "retux.py". On most systems, this should be done by
double-clicking on it; if you are shown a dialog asking you if you want
to display or run the file, choose to run it.

There are some command-line options that can be passed. Run the game in
a terminal with the "-h" command-line option for more information.


BUILDING LOCALES (FOR DEVELOPERS AND PACKAGERS)

If you have cloned the source code directly from Git, locales will need
to be built for languages other than English to work.  This step is only
necessary if you are a developer, translator, or packager running the
source code taken directly from the Git repository.

To build locales, ensure your system has the msgfmt command (which is a
part of gettext), then do the following from the data/locale directory:

    ./build.py


CREATING FROZEN EXECUTABLES (FOR DEVELOPERS AND PACKAGERS)

This game is written in Python, so it is run directly as a script with
the Python interpreter. However, it can be and is "frozen" with certain
tools to make it possible to run on systems which don't have Python
installed, or which are missing one or more of the game's dependencies.
Of course, all dependencies required to run ReTux from source code are
also required to freeze an executable.

This game supports two methods of freezing: PyInstaller and cx_Freeze.
In general, PyInstaller is preferred since it is easier to use and
generally better in our experience. However, cx_Freeze can also be used
as a fallback if you can't get PyInstaller to work.

To build with PyInstaller on Linux, we use the following command within
the game's root directory:

    pyinstaller -F retux.py

For Windows, we instead use the following command (utilizing -w and -i):

    pyinstaller -Fw -i data/images/misc/icon.ico retux.py

A binary will be produced and placed in the dist directory. You can then
move the binary out to the game's root directory and it should run just
as retux.py runs. The left-over build and dist directories, as well as
the retux.spec file, can then be deleted.

If the -F option does not work or a single executable file is
undesirable, the -F option can be omitted, in which case a binary and
several other files (including shared object files) will be produced,
all of which must be moved to the game's root directory.

To build with cx_Freeze, the command used is the same regardless of
the system:

    python3 setup.py build

This will produce a usable binary along with several other files needed
by the binary within a subdirectory named based on your architecture
under the build directory. Move all of these files to the game's root
directory and the binary produced should run the same as the source code
does.

