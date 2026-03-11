import sys
import os

def _fix_frozen_tcl_env():
    """
    Work around broken bundled Tcl metadata on some Windows Python installs.
    Prefer a known-good system Tcl/Tk pair before importing tkinter consumers.
    """
    if not getattr(sys, "frozen", False):
        return

    local_appdata = os.environ.get("LOCALAPPDATA", "")
    candidates = [
        r"C:\Python311",
        r"C:\Python310",
        os.path.join(local_appdata, "Programs", "Python", "Python312"),
        os.path.join(local_appdata, "Programs", "Python", "Python311"),
        os.path.join(local_appdata, "Programs", "Python", "Python310"),
    ]

    for root in candidates:
        tcl_dir = os.path.join(root, "tcl", "tcl8.6")
        tk_dir = os.path.join(root, "tcl", "tk8.6")
        if os.path.isfile(os.path.join(tcl_dir, "init.tcl")) and os.path.isfile(os.path.join(tk_dir, "tk.tcl")):
            os.environ["TCL_LIBRARY"] = tcl_dir
            os.environ["TK_LIBRARY"] = tk_dir
            return


_fix_frozen_tcl_env()

from src.p4pp.gui.app import main

if __name__ == '__main__':
    main()
