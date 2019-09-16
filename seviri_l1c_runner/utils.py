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
import netifaces
import six
import time
from datetime import datetime, timedelta
import shutil
import stat

if six.PY2:
    from urlparse import urlparse
    from urlparse import urlunsplit
elif six.PY3:
    from urllib.parse import urlparse
    from urllib.parse import urlunsplit

if six.PY2:
    ptimer = time.clock
elif six.PY3:
    ptimer = time.perf_counter

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


def get_local_ips():
    inet_addrs = [netifaces.ifaddresses(iface).get(netifaces.AF_INET)
                  for iface in netifaces.interfaces()]
    ips = []
    for addr in inet_addrs:
        if addr is not None:
            for add in addr:
                ips.append(add['addr'])
    return ips


def cleanup_cspp_workdir(workdir):
    """Clean up the CSPP working dir after processing"""

    filelist = glob('%s/*' % workdir)
    dummy = [os.remove(s) for s in filelist if os.path.isfile(s)]
    filelist = glob('%s/*' % workdir)
    LOG.info(
        "Number of items left after cleaning working dir = " + str(len(filelist)))
#     shutil.rmtree(workdir)
    return


def get_edr_times(filename):
    """Get the start and end times from the SDR file name
    """
    bname = os.path.basename(filename)
    sll = bname.split('_')
    start_time = datetime.strptime(sll[2] + sll[3][:-1],
                                   "d%Y%m%dt%H%M%S")
    end_time = datetime.strptime(sll[2] + sll[4][:-1],
                                 "d%Y%m%de%H%M%S")
    if end_time < start_time:
        end_time += timedelta(days=1)

    return start_time, end_time


def get_active_fire_result_files(res_dir):
    """
    Make alist of all result files that should be captured from the CSPP
    work-dir for delivery
    """

    result_files = (glob(os.path.join(res_dir, 'AF*.nc')) +
                    glob(os.path.join(res_dir, 'AF*.txt')))

    return sorted(result_files)
