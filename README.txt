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

