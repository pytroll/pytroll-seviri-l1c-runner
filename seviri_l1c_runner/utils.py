#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2019 Pytroll

# Author(s):

#   Adam Dybbroe <Firstname.Lastname@smhi.se>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Utility functions for the SEVIRI HRIT to PPS level-1c format generation

"""

import logging
import os
from glob import glob
from datetime import datetime, timedelta
import shutil
import stat

LOG = logging.getLogger(__name__)


def deliver_output_file(affile, base_dir, subdir=None):
    """Copy the Active Fire output files to the sub-directory under the *subdir* directory
    structure"""

    LOG.debug("base_dir: %s", base_dir)

    if subdir:
        path = os.path.join(base_dir, subdir)
    else:
        path = base_dir

    LOG.debug("Path: %s", str(path))

    if not os.path.exists(path):
        LOG.warning("Directory does not exist - create it: %s", path)
        os.mkdir(path)
    else:
        LOG.debug("Directory exists: %s", path)

    LOG.info("Number of 1c result files: 1")
    newfilename = os.path.join(path, os.path.basename(affile))
    LOG.info("Copy affile to destination: " + newfilename)
    if os.path.exists(affile):
        LOG.info("File to copy: {file} <> ST_MTIME={time}".format(file=str(affile),
                                                                  time=datetime.utcfromtimestamp(os.stat(affile)[stat.ST_MTIME]).strftime('%Y%m%d-%H%M%S')))
    if not os.path.isfile(newfilename):
        shutil.copy(affile, newfilename)
        if os.path.isfile(newfilename):
            LOG.info("File at destination: {file} <> ST_MTIME={time}".format(file=str(newfilename),
                                                                             time=datetime.utcfromtimestamp(os.stat(newfilename)[stat.ST_MTIME]).strftime('%Y%m%d-%H%M%S')))
    else:
        LOG.warning("File already exist. File: %s" % newfilename)
    retvl = newfilename

    return retvl


def cleanup_workdir(workdir):
    """Clean up the working dir after processing"""

    filelist = glob('%s/*' % workdir)
    dummy = [os.remove(s) for s in filelist if os.path.isfile(s)]
    filelist = glob('%s/*' % workdir)
    LOG.info(
        "Number of items left after cleaning working dir = " + str(len(filelist)))
#     shutil.rmtree(workdir)
    return

