# Copyright (C) 2016 William Hicks
#
# This file is part of Writing3D.
#
# Writing3D is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

"""Tools for exporting W3D projects in various formats
"""

import site
import os
import sys
import platform
import pickle
import subprocess
import argparse
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from pyw3d import BLENDER_EXEC, BLENDER_PLAY
    from pyw3d import project


def get_scripts_directory():
    """Return directory where W3D scripts have been installed

    :warn: This assumes a default installation with user scheme

    :todo: Add fallbacks for alternate installations"""

    if platform.system() in ("Windows",):
        scripts_dir = "Scripts"
    else:
        scripts_dir = "bin"
    scripts_dir = os.path.join(site.getuserbase(), scripts_dir)
    return scripts_dir


EXPORT_SCRIPT = os.path.join(get_scripts_directory(), "w3d_export_tools.py")


def pickle_w3dproject(input_project, filename="run.p"):
    """Dump W3DProject to pickle file"""
    pickle.dump(input_project, open(filename, "wb"))


def unpickle_w3dproject(filename="run.p"):
    """Create w3dproject from pickle file"""
    return pickle.load(open(filename, "rb"))


def export_to_blender(input_project, filename="run.blend", display=True):
    """Save project as .blend file

    :param str filename: Name of .blend file to export to
    :param bool display: Display project in standalone player after export?
    """
    try:
        import bpy  # Check if we're in Blender environment
        input_project.blend()
        if os.path.exists(filename):
            os.remove(filename)
        bpy.ops.wm.save_as_mainfile(filepath=filename)
    except ImportError:
        pickle_w3dproject(input_project)
        subprocess.call([
            BLENDER_EXEC, "--background", "--python", EXPORT_SCRIPT, "--", "-f"
            "pickle", "run.p", "-o", filename]
        )
    if display:
        subprocess.call([BLENDER_PLAY, filename])

if __name__ == "__main__":
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = argv[1:]
    parser = argparse.ArgumentParser()
    parser.add_argument("project_file")
    parser.add_argument(
        "-f", "--filetype", default="xml", choices=["xml", "pickle"],
        help="input filetype")
    parser.add_argument(
        "-o", "--output", default="run.blend",
        help="filename for output blend file")
    parser.add_argument(
        "-d", "--display", default=False, action="store_true")
    args = parser.parse_args(argv)

    if args.filetype == "xml":
        input_project = project.W3DProject.fromXML_file(args.project_file)
    elif args.filetype == "pickle":
        input_project = unpickle_w3dproject(args.project_file)
    export_to_blender(
        input_project, filename=args.output, display=args.display)
