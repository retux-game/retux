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

To run ReTux with a particular Python version, open retux.py and change
the shebang on line one to indicate the version you want to use, e.g.
"python2" or "python3" instead of just "python".

There are some command-line options that can be passed. Run ReTux in a
terminal with the "-h" command-line option for more information.


SPECIAL CONTROLS

You can exit the game by pressing the middle mouse button. This is a
workaround for a rare bug in Pygame which can lock up the keyboard
controls, explained in detail here:

https://savannah.nongnu.org/forum/forum.php?forum_id=8113
