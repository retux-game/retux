Copyright (C) 2014, 2015 Julian Marchant <onpon4@riseup.net>

Copying and distribution of this file, with or without modification,
are permitted in any medium without royalty provided the copyright
notice and this notice are preserved.  This file is offered as-is,
without any warranty.

========================================================================


HOW TO RUN

You will need the following dependencies:

- Python 2 (2.7 or later) or 3 (3.1 or later) <http://www.python.org>
- SGE Game Engine 0.21 or later <http://stellarengine.nongnu.org>

Once you have installed the dependencies, you can start ReTux by
running retux.py. By default, it will use Python 3. To run it with
Python 2 instead, you can either change the shebang on line 1 from
"python3" to "python2", or explicitly run the Python 2 executable, e.g.:

    python2 retux.py

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
