#!/usr/bin/env python

import acid_detectors.collusion as collusion
import argparse
import logging
import os
from sets import Set


VERSION_NUMBER = "1.1"
COLLUSION_KINDS = ['colluding_info', 'colluding_money1', 'colluding_money2', 'colluding_service', 'colluding_camera', 'colluding_accounts', 'colluding_sms']


def collusion_sets(prolog_program_filename, collusion_kind, filter_dir, communication_length, app_package):
    sets = Set()
    base_file = prolog_program_filename
    if filter_dir is not None and os.path.isdir(filter_dir):
        logging.info("Filtering intents")
        filtered_file_name = collusion.filter_intents_by_folder(prolog_program_filename, filter_dir)
        base_file = filtered_file_name

    numbered_channels_file = collusion.replace_channels_strings_file(base_file)
    mapping_channels = collusion.read_mapping_file(base_file + collusion.channel_numbering_mapping_suffix)
    numbered_packages_file = collusion.replace_packages_strings_file(numbered_channels_file)
    mapping_packages = collusion.read_mapping_file(numbered_channels_file + collusion.package_numbering_mapping_suffix)
    
    logging.info("Finding colluding apps")

    if communication_length is None:
        if app_package is None:
            logging.info("Searching for all")
            app_sets_list = collusion.find_all_colluding(numbered_packages_file, collusion_kind)
        else:
            app_value = mapping_packages.index("'" + app_package + "'")
            logging.info("Specific app")
            app_sets_list = collusion.find_package_colluding(numbered_packages_file, app_value, collusion_kind)
    else:
        if app_package is None:
            logging.info("Specific length ")
            app_sets_list = collusion.find_all_colluding_length(numbered_packages_file, collusion_kind, communication_length)
        else:
            app_value = mapping_packages.index("'" + app_package + "'")
            logging.info("Specific length and app")
            app_sets_list = collusion.find_package_colluding_length(numbered_packages_file, collusion_kind, app_value, communication_length)
    
    logging.info("Finding communication channels")

    for app_set in app_sets_list:
        channels = collusion.communication_channels(numbered_packages_file, app_set)
        c_set = collusion.CollusionSet(collusion_kind, app_set, channels, mapping_packages, mapping_channels)
        sets.add(c_set)
    return sets


def main():
    default_intent_data_to_filter = os.path.join(os.path.dirname(os.path.realpath(__file__)), "default_intent_data_to_filter")

    parser = argparse.ArgumentParser(description="Collusion detection program, version %s. Runs the prolog program to detect collusion. This tool outputs a list of all collusion app sets found in the speficied prolog program (which was previously produced by the generate_prolog program). It includes the apps in the set, and the channels used to communicate." % VERSION_NUMBER)
    parser.add_argument("prolog_program_filename",
                        metavar='prolog_program_filename',
                        help="the prolog program previously generated by the generate_prolog program")
    parser.add_argument("collusion_kind",
                        metavar='collusion_kind',
                        help="the kind of collusion that should be detected. Possible values are: %s" % str.join(", ", COLLUSION_KINDS),
                        choices=COLLUSION_KINDS)
    parser.add_argument("-v", "--verbose",
                        action="store_true", dest="verbose", default=False,
                        help="increase output verbosity")
    parser.add_argument("-l", "--length", type=int,
                        action="store", dest="communication_length", default=None,
                        help="only detect collusion based on communication paths of a specified length (i.e., app sets of a given size). This is useful to reduce the search space")
    parser.add_argument("-a", "--app_package",
                        action="store", dest="app_package", default=None,
                        help="detect collusion only for app sets that start with the app with specified pacakge name")
    parser.add_argument("-f", "--filter",
                        action="store", dest="filter_dir", default=None,
                        help="use specified folder with intent data that is considered safe. Apps that communciate with these intents will not be flagged as colluding. A default directory of common intent data to use for this is located at " + default_intent_data_to_filter + ". Intent actions should be organized inside different files inside the folder (one intent action per line)")


    args = parser.parse_args()

    logging_level = logging.WARNING
    if args.verbose:
        logging_level = logging.INFO

    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging_level)

    logging.info("Version " + VERSION_NUMBER)
    
    colluding_app_sets = collusion_sets(args.prolog_program_filename, args.collusion_kind, args.filter_dir, args.communication_length, args.app_package)
    
    if len(colluding_app_sets) == 0:
        print("No collusion detected")
    else:
        for colluding_app_set in colluding_app_sets:
            colluding_app_set.description()


if __name__ == "__main__":
    main()