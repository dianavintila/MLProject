#!/usr/bin/env python

from acid_detectors.utils import get_all_directrories_in_dir
import argparse
import logging
import os


VERSION_NUMBER = "1.1"


def append_file_to_file(opened_output_file, input_filename):
    with open(input_filename, 'r') as input_file:
        for line in input_file:
           opened_output_file.write(line)


def produce_prolog_program(collusion_fact_directories, output_file_name, prolog_rules_filename, external_storage_enabled):
    with open(output_file_name, 'w') as output_file:
        output_file.write("% DO NOT EDIT THIS FILE\n");
        output_file.write("% =====================\n");
        output_file.write("% This file was automatically generated by the generate_facts program.\n");
        output_file.write("\n");

        # write facts: packages
        logging.info("Writing packages")
        for directory in collusion_fact_directories:
            input_filename = os.path.join(directory, "packages.pl.partial")
            append_file_to_file(output_file, input_filename)

        # write fact: permissions
        logging.info("Writing uses")
        for directory in collusion_fact_directories:
            input_filename = os.path.join(directory, "uses.pl.partial")
            append_file_to_file(output_file, input_filename)

        # write facts: sends
        logging.info("Writing sends")
        for directory in collusion_fact_directories:
            input_filename = os.path.join(directory, "sends.pl.partial")
            append_file_to_file(output_file, input_filename)

        # write facts: sends - external storage
        if external_storage_enabled:
            logging.info("Writing sends - external storage")
            output_file.write("trans(A,'external_storage'):- uses(A,'android.permission.WRITE_EXTERNAL_STORAGE').\n")

        # write facts: receivers
        logging.info("Writing receivers")
        for directory in collusion_fact_directories:
            input_filename = os.path.join(directory, "receives.pl.partial")
            append_file_to_file(output_file, input_filename)

        # write facts: receivers - external storage
        if external_storage_enabled:
            logging.info("Writing receivers - external storage")
            output_file.write("recv(A,'external_storage'):- uses(A,'android.permission.WRITE_EXTERNAL_STORAGE').\n")
            output_file.write("recv(A,'external_storage'):- uses(A,'android.permission.READ_EXTERNAL_STORAGE').\n")

        # write prolog rules
        logging.info("Writing prolog rules")
        append_file_to_file(output_file, prolog_rules_filename)

        logging.info("Done")


def main():
    default_prolog_rules = os.path.join(os.path.dirname(os.path.realpath(__file__)), "default_prolog_collusion_rules.pl")

    parser = argparse.ArgumentParser(description="Collusion prolog generator, version %s. Produce the prolog filter program from the previously generated collusion fact directories. Combines the generated collusion fact directories (produced by the generate_facts program) into a prolog program (which the detect_collusion program will use)." % VERSION_NUMBER)
    parser.add_argument("-v", "--verbose",
                        action="store_true", dest="verbose", default=False,
                        help="increase output verbosity")
    parser.add_argument("-o", "--output_file",
                        action="store", dest="output_file", default="prolog_program.pl",
                        help="set the output file to which the prolog program will be written to. Any existing file will be overwritten. Default is 'prolog_program.pl'")
    parser.add_argument("-d", "--input_dir",
                        action="store", dest="input_dir", default=".",
                        help="set the input directory in which the previously generated collusion facts directories are located. All directories within this input directory (which start with the specified prefix) will be considered as being collusion fact directories (generated by the generate_facts program). Default is '.'")
    parser.add_argument("-p", "--prefix",
                        action="store", dest="dir_prefix", default="collusion_facts_",
                        help="set directory prefix used to discover the previously generated generated collusion fact directtories. All directories with this prefix (located in the input directory) will be considered as being collusion fact directories (generated by the generate_facts program). This should match the prefix that was used when running the generate_facts program. Default is 'collusion_facts_'. Note, this can be set to the empty string ''")
    parser.add_argument("-r", "--rules",
                        action="store", dest="prolog_rules_filename", default=default_prolog_rules,
                        help="set the prolog rule file that contains the collusion rules that will be used. The default will be the rules that come packaged as default. Only change this if you know what you are doing.")
    parser.add_argument("-s", "--storage",
                        action="store_true", dest="external_storage_enabled", default=False,
                        help="Adds rules to consider external storage as a potential communication channel")

    args = parser.parse_args()

    logging_level = logging.WARNING
    if args.verbose:
        logging_level = logging.INFO

    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging_level)

    # Discover the collusion fact directories
    collusion_fact_directories = get_all_directrories_in_dir(args.input_dir, args.dir_prefix)
    
    logging.info("Version " + VERSION_NUMBER)
    logging.info("Collusion fact directories to process: \n\t%s" % str.join("\n\t", collusion_fact_directories))
    logging.info("Prolog collusion rules file: " + args.prolog_rules_filename)
    logging.info("Add rules external storage rules: " + str(args.external_storage_enabled))

    if len(collusion_fact_directories) <= 0:
        logging.warning("No collusion fact directories found")
        exit(-1);
    
    produce_prolog_program(collusion_fact_directories, args.output_file, args.prolog_rules_filename, args.external_storage_enabled)


if __name__ == "__main__":
    main()