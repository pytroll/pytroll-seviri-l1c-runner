#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2019 Pytroll

# Author(s):

#   Erik Johansson <erik.johansson@smhi.se>
#   Adam Dybbroe <adam.dybbroe@smhi.se>

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

"""Setup for the pytroll runner to convert SEVIRI level 1.5 HRIT to PPS level-1c format
"""

from setuptools import find_packages, setup

try:
    # HACK: https://github.com/pypa/setuptools_scm/issues/190#issuecomment-351181286
    # Stop setuptools_scm from including all repository files
    import setuptools_scm.integration
    setuptools_scm.integration.find_files = lambda _: []
except ImportError:
    pass


# version = imp.load_source(
#    'nwcsafpps_runner.version', 'nwcsafpps_runner/version.py')

NAME = "seviri_l1c_runner"
README = open('README.md', 'r').read()

setup(name=NAME,
      # version=version.__version__,
      description='Pytroll runner for generating PPS level-1c format of SEVIRI',
      long_description=README,
      author='Erik Johansson',
      author_email='erik.johansson@smhi.se',
      classifiers=["Development Status :: 3 - Alpha",
                   "Intended Audience :: Science/Research",
                   "License :: OSI Approved :: GNU General Public License v3 " +
                   "or later (GPLv3+)",
                   "Operating System :: OS Independent",
                   "Programming Language :: Python",
                   "Topic :: Scientific/Engineering"],
      url="https://github.com/pytroll/pytroll-seviri-l1c-runner",
      packages=['seviri_l1c_runner', ],
      scripts=['bin/seviri_l1c_runner.py', ],
      data_files=[],
      zip_safe=False,
      use_scm_version=True,
      python_requires='>=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*',
      install_requires=['posttroll', ],
      )
