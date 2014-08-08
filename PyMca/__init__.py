import os
if os.path.exists(os.path.join(\
    os.path.dirname(os.path.dirname(__file__)), 'py2app_setup.py')):
    raise ImportError('PyMca cannot be imported from source directory')

try:
    from .PyMcaIO import *
except:
    print("WARNING importing IO directly")
    from PyMcaIO import *