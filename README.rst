.. warning::

   Use this at your own risk! It's a tool I wrote out of annoyance, not a
   recommended solution.

If you install things with setuptools, you might have found yourself cursing
the *damn pth files* it creates that reorder ``sys.path``.

``damnpth`` finds the ``.pth`` files and removes the crazy path-reordering parts
from them. If it can, it then patches the setuptools code to stop adding this
path-reordering stuff.

Usage::

    pip install damnpth
    damnpth

In principle, this shouldn't break your environment, but all the same,
it's probably not something to run on your production systems.
