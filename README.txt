This file has been dedicated to the public domain, to the extent
possible under applicable law, via CC0. See
http://creativecommons.org/publicdomain/zero/1.0/ for more
information. This file is offered as-is, without any warranty.

========================================================================


HOW TO RUN

If you have downloaded a version of ReTux designated for a particular
system, simply run the executable.

To run the ReTux source code, you will need the following dependencies:

- Python 2 (2.7 or later) or 3 (3.1 or later) <http://www.python.org>
- Pygame 1.9.1 or later <http://pygame.org>

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

Use the directional controls and pause or jump key to navigate the
menus. By default, Tux is is controlled by the arrow keys, Space,
Left Ctrl, and Left Shift. You can change the controls in the Options
menu.

If, after entering fullscreen mode, the keyboard becomes unresponsive,
you can exit the game by pressing the middle mouse button. This is a
result of a rare bug in Pygame, explained in detail here:

https://savannah.nongnu.org/forum/forum.php?forum_id=8113
