Copyright (C) 2015, 2016 onpon4 <onpon4@riseup.net>

Copying and distribution of this file, with or without modification,
are permitted in any medium without royalty provided the copyright
notice and this notice are preserved.  This file is offered as-is,
without any warranty.

========================================================================


Here you will find installers for Python 2.7 and Pygame 1.9.2a0.  First
double-click on the Python installer and follow the instructions given,
then double-click on the Pygame installer and follow the instructions
given.  If you update the game in the future, you can just download the
plain source code distribution; reinstalling Python and Pygame will not
be necessary.

Please note that this 32-bit version of Pygame MUST be used with a
32-bit version of Python 2.7.  It is not compatible with the 64-bit
version of Python.  If your system already has the 64-bit version of
Python 2.7 installed, there are a few options:

1. Remove your 64-bit Python 2.7 installation and replace it with the
   32-bit version.  This is the easiest way, but if your 64-bit Python
   2.7 installation was being used for something else, you may have to
   reinstall some libraries.

2. Install the 32-bit version of Python 2.7 alongside your existing
   64-bit Python 2.7 installation, leaving the 64-bit Python associated
   with Python scripts, and create a shortcut which runs the game with
   the 32-bit Python.  This option avoids touching the existing Python
   installation, but it's a little dirty and has the potential to
   unnecessarily complicate things in the future.

3. Download and install Pygame for the 64-bit version of Python 2.7.
   Such a build of Pygame can be found here:

   http://www.lfd.uci.edu/~gohlke/pythonlibs/#pygame

   This is the cleanest way.  Unfortunately, this build of Pygame is
   only available as a wheel, so you will need to install it with pip
   from the Command Prompt.  This may be difficult if you don't know
   what you're doing.  The appropriate documentation for doing so can be
   found here:

   https://wheel.readthedocs.org
