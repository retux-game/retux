Copyright (C) 2014-2016 onpon4 <onpon4@riseup.net>

Copying and distribution of this file, with or without modification,
are permitted in any medium without royalty provided the copyright
notice and this notice are preserved.  This file is offered as-is,
without any warranty.

========================================================================


HOW TO RUN

To run ReTux, you will need the following dependencies:

- Python 2 (2.7 or later) or 3 (3.1 or later) <http://www.python.org>
- Pygame 1.9.1 or later <http://pygame.org/download.shtml>

If you have downloaded a version of ReTux designated for a particular
system, these dependencies can be found under the "deps" folder.  Please
see any "README" files in that folder for instructions and tips.

Once you have installed the dependencies, you can start ReTux by
running retux.py. On most systems, this should be done by
double-clicking on it; if you are shown a dialog asking you if you want
to display or run the file, choose to run it.

Python 2 will be used by default. To run ReTux with Python 3 instead,
you can either change the shebang on line 1 from "python2" to "python3",
or explicitly run the Python 3 executable, e.g. with
"python3 retux.py" (the exact command may be different depending on
your system).

There are some command-line options that can be passed. Run ReTux in a
terminal with the "-h" command-line option for more information.


HOW TO PLAY

Use the arrow keys and Enter to navigate the menus. By default, Tux is
is controlled by the arrow keys, Space, Left Ctrl, and Left Shift. You
can change the controls in the Options menu.

Other controls:
- F11: Toggle fullscreen.
- Escape: Return to the title screen.
- Middle mouse button: Quit the game.

The middle mouse button quitting the game is meant to work around a bug
in Pygame which sometimes locks up the keyboard when toggling fullscreen
or changing the window size. See this post on the SGE blog for more
information:

https://savannah.nongnu.org/forum/forum.php?forum_id=8113
