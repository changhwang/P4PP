import sys
import os

# Instead of sys.path hacks, just run it straight. PyInstaller handles this better.
from src.p4pp.gui.app import main

if __name__ == '__main__':
    main()
