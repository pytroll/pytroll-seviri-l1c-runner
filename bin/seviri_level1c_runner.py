#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2019 Pytroll

# Author(s):

#   Erik Johansson <Firstname.Lastname@smhi.se>

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


from seviri_l1c_runner import get_config

from seviri2pps import process_one_scan  # @UnresolvedImport
from posttroll.publisher import Publish  # @UnresolvedImport
from posttroll.message import Message  # @UnresolvedImport

import logging
import sys
import os
import six
from posttroll.subscriber import Subscribe  # @UnresolvedImport
from multiprocessing import cpu_count
if six.PY2:
    from urlparse import urlunsplit
elif six.PY3:
    from urllib.parse import urlunsplit  # @UnresolvedImport
import socket

from seviri_l1c_runner.utils import (deliver_output_file, cleanup_cspp_workdir)


SUPPORTED_METEOSAT_SATELLITES = ['meteosat-09', 'meteosat-10', 'meteosat-11']

#: Default time format
_DEFAULT_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

#: Default log format
_DEFAULT_LOG_FORMAT = '[%(levelname)s: %(asctime)s : %(name)s] %(message)s'


class ActiveL1cProcessor(object):

    """
    Container for the SEVIRI HRET processing

    """

    def __init__(self, ncpus):
        from multiprocessing.pool import ThreadPool
        self.pool = ThreadPool(ncpus)
        self.ncpus = ncpus

        self.orbit_number = 99999  # Initialised orbit number
        self.platform_name = 'unknown'  # Ex.: Suomi-NPP
        self.cspp_results = []
        self.pass_start_time = None
        self.result_files = []
        self.sdr_files = []

        self.result_home = OPTIONS.get('output_dir', '/tmp')
        self.working_home = OPTIONS.get('working_dir', '/tmp')
        self.publish_topic = OPTIONS.get('publish_topic')
        self.site = OPTIONS.get('site', 'unknown')
        self.environment = OPTIONS.get('environment')
        self.message_data = None
        self.service = None

    def initialise(self, service):
        """Initialise the processor"""
        self.cspp_results = []
        self.pass_start_time = None
        self.result_files = []
        self.sdr_files = []
        self.service = service

    def deliver_output_file(self, subd=None):
        LOG.debug("Result file: %s", str(self.result_file))
        LOG.debug("Result home dir: %s", str(self.result_home))
        LOG.debug("Sub directory: %s", subd)
        return deliver_output_file(self.result_file, self.result_home, subd)

    def run(self, msg):
        """Start the L1c processing using process_one_scan"""

        if not msg:
            return False

        if msg.type != 'dataset':
            LOG.info("Not a dataset, don't do anything...")
            return False

        if ('platform_name' not in msg.data or
                'start_time' not in msg.data):
            #                 'orbit_number' not in msg.data or
            LOG.warning("Message is lacking crucial fields...")
            return False

        if (msg.data['platform_name'].lower() not in SUPPORTED_METEOSAT_SATELLITES):
            LOG.info(str(msg.data['platform_name']) + ": " +
                     "Not a valid Meteosat scene. Continue...")
            return False

        self.platform_name = str(msg.data['platform_name'])
        self.sensor = str(msg.data['sensor'])
        self.message_data = msg.data

        sdr_dataset = msg.data['dataset']

        if len(sdr_dataset) < 1:
            return False

        sdr_files = []
        for sdr in sdr_dataset:
            sdr_filename = sdr['uri']
            sdr_files.append(sdr_filename)

        self.sdr_files = sdr_files
        self.cspp_results.append(self.pool.apply_async(process_one_scan, (self.sdr_files, self.working_home)))
        return True


def publish_l1c(publisher, result_file, mda, **kwargs):
    """Publish the messages that l1c files are ready
    """
    if not result_file:
        return

    # Now publish:
    to_send = mda.copy()
    # Delete the SDR dataset from the message:
    try:
        del(to_send['dataset'])
    except KeyError:
        LOG.warning("Couldn't remove dataset from message")

    if ('orbit' in kwargs) and ('orbit_number' in to_send.keys()):
        to_send["orig_orbit_number"] = to_send["orbit_number"]
        to_send["orbit_number"] = kwargs['orbit']

    to_send["uri"] = urlunsplit(('ssh', socket.gethostname(), result_file, '', ''))
    filename = os.path.basename(result_file)
    to_send["uid"] = filename

    publish_topic = kwargs.get('publish_topic', 'Unknown')
    site = kwargs.get('site', 'unknown')
#     environment = kwargs.get('environment', 'unknown')

    to_send['format'] = 'PPS-L1C'
    to_send['type'] = 'NETCDF'
    to_send['data_processing_level'] = '1c'
    to_send['site'] = site
    #: What is this
#     to_send['start_time'], to_send['end_time'] = get_edr_times(filename)
    #
    LOG.debug('Site = %s', site)
    LOG.debug('Publish topic = %s', publish_topic)
    for topic in publish_topic:
        msg = Message('/'.join(('', topic)),
                      "file", to_send).encode()

    LOG.debug("sending: " + str(msg))
    publisher.send(msg)


def seviri_l1c_runner(options, service_name="unknown"):
    """The live runner for the SEVIRI  l1c product generation"""

    LOG.info("Start the SEVIRI l1C runner...")
    LOG.debug("Listens for messages of type: %s", str(options['message_types']))

    ncpus_available = cpu_count()
    LOG.info("Number of CPUs available = " + str(ncpus_available))
    ncpus = int(options.get('num_of_cpus', 1))
    LOG.info("Will use %d CPUs when running the CSPP SEVIRI instances", ncpus)

    af_proc = ActiveL1cProcessor(ncpus)
    with Subscribe('', options['message_types'], True) as sub:
        with Publish('seviri_l1c_runner', 0) as publisher:
            while True:
                count = 0
                af_proc.initialise(service_name)
                for msg in sub.recv():
                    count = count + 1
                    status = af_proc.run(msg)
                    if not status:
                        break  # end the loop and reinitialize !
                    LOG.debug(
                        "Received message data = %s", str(af_proc.message_data))
                    LOG.info("Get the results from the multiptocessing pool-run")
                    for res in af_proc.cspp_results:
                        tmp_result_file = res.get()
                        af_proc.result_file = tmp_result_file
                        af_files = af_proc.deliver_output_file()
                        if af_proc.result_home == af_proc.working_home:
                            LOG.info("home_dir = working_dir no cleaning necessary")
                        else:
                            LOG.info("Cleaning up directory %s", af_proc.working_home)
                            cleanup_cspp_workdir(af_proc.working_home + '/')

                        publish_l1c(publisher, af_files,
                                    af_proc.message_data,
                                    orbit=af_proc.orbit_number,
                                    publish_topic=af_proc.publish_topic,
                                    environment=af_proc.environment,
                                    site=af_proc.site)
                        LOG.info("L1C processing has completed.")


def get_arguments():
    """
    Get command line arguments
    Return
    name of the service and the config filepath
    """
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument('-c', '--config_file',
                        type=str,
                        dest='config_file',
                        required=True,
                        help="The file containing " +
                        "configuration parameters e.g. product_filter_config.yaml")
    parser.add_argument("-s", "--service",
                        help="Name of the service (e.g. iasi-lvl2)",
                        dest="service",
                        type=str,
                        required=True)
    parser.add_argument("-l", "--logging",
                        help="The path to the log-configuration file (e.g. './logging.ini')",
                        dest="logging_conf_file",
                        type=str,
                        required=False)

    args = parser.parse_args()

    service = args.service.lower()

    if 'template' in args.config_file:
        print("Template file given as master config, aborting!")
        sys.exit()

    return args.logging_conf_file, service, args.config_file

if __name__ == '__main__':
    
    (logfile, service_name, config_filename) = get_arguments()
    
    if logfile:
        logging.config.fileConfig(logfile)
    
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(fmt=_DEFAULT_LOG_FORMAT,
                                  datefmt=_DEFAULT_TIME_FORMAT)
    handler.setFormatter(formatter)
    logging.getLogger('').addHandler(handler)
    logging.getLogger('').setLevel(logging.DEBUG)
    logging.getLogger('posttroll').setLevel(logging.INFO)

    environ = "utv"

    OPTIONS = get_config(config_filename, service_name, environ)

    OPTIONS['environment'] = environ
    OPTIONS['nagios_config_file'] = None

    LOG = logging.getLogger('seviri-l1c-runner')

    seviri_l1c_runner(OPTIONS, service_name)
