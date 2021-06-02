#!/bin/env python3
"""
This script creates a canonicalized version of KG2 stored in various file formats, including TSVs ready for import
into Neo4j. Files are created in the directory this script is in. It relies on the options you specify in
kg2c_config.json; in particular, the KG2c will be built off of the KG2 endpoint you specify in that config file.
Usage: python3 build_kg2c.py [--test]
"""
import argparse
import logging
import pathlib
from datetime import datetime
import json
import os
import subprocess
import sys
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from create_kg2c_files import create_kg2c_files
from record_kg2c_meta_info import record_meta_kg_info
sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/../../")  # code directory
from RTXConfiguration import RTXConfiguration

KG2C_DIR = f"{os.path.dirname(os.path.abspath(__file__))}"
CODE_DIR = f"{KG2C_DIR}/../.."


def _setup_rtx_config_local(kg2_version: str):
    # Create a config_local.json file based off of configv2.json, but modified for our needs
    logging.info("Creating a config_local.json file pointed to the right KG2 Neo4j and synonymizer..")
    RTXConfiguration()  # Ensures we have a reasonably up-to-date configv2.json
    with open(f"{CODE_DIR}/configv2.json") as configv2_file:
        rtx_config_dict = json.load(configv2_file)
    # Point to the 'right' KG2 (the one specified in the KG2c config) and synonymizer (we always use simple name)
    logging.info(f"Deducing the neo4j bolt url from the KG2 version specified in kg2c_config.json ({kg2_version})")
    kg2_neo4j_endpoint = f"kg2endpoint-kg{kg2_version.replace('.', '-')}.rtx.ai"
    rtx_config_dict["Contextual"]["KG2"]["neo4j"]["bolt"] = f"bolt://{kg2_neo4j_endpoint}:7687"
    for mode, path_info in rtx_config_dict["Contextual"].items():
        path_info["node_synonymizer"]["path"] = "/something/node_synonymizer.sqlite"  # Only need name, not full path
    # Save a copy of any pre-existing config_local.json so we don't overwrite it
    original_config_local_file = pathlib.Path(f"{CODE_DIR}/config_local.json")
    if original_config_local_file.exists():
        subprocess.check_call(["cp", f"{CODE_DIR}/config_local.json", f"{CODE_DIR}/config_local.json_KG2CBUILDTEMP"])
    # Save our new config_local.json file
    with open(f"{CODE_DIR}/config_local.json", "w+") as config_local_file:
        json.dump(rtx_config_dict, config_local_file)


def _upload_output_files_to_s3():
    logging.info("Uploading KG2c json and TSV files to S3..")
    tarball_path = f"{KG2C_DIR}/kg2c-tsv.tar.gz"
    json_file_path = f"{KG2C_DIR}/kg2c.json"
    json_lite_file_path = f"{KG2C_DIR}/kg2c_lite.json"
    subprocess.check_call(["tar", "-czvf", tarball_path, "nodes_c.tsv", "nodes_c_header.tsv", "edges_c.tsv", "edges_c_header.tsv"])
    subprocess.check_call(["aws", "s3", "cp", "--no-progress", "--region", "us-west-2", tarball_path, "s3://rtx-kg2/"])
    subprocess.check_call(["gzip", "-f", json_file_path])
    subprocess.check_call(["gzip", "-f", json_lite_file_path])
    subprocess.check_call(["aws", "s3", "cp", "--no-progress", "--region", "us-west-2", f"{json_file_path}.gz", "s3://rtx-kg2/"])
    subprocess.check_call(["aws", "s3", "cp", "--no-progress", "--region", "us-west-2", f"{json_lite_file_path}.gz", "s3://rtx-kg2/"])


def main():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s: %(message)s',
                        handlers=[logging.FileHandler("build.log"),
                                  logging.StreamHandler()])
    logging.info("STARTING KG2c BUILD")
    start = time.time()
    # Grab any parameters passed to this script
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--test", dest="test", action='store_true', default=False)
    args = arg_parser.parse_args()

    # Load the KG2c config file
    with open(f"{KG2C_DIR}/kg2c_config.json") as config_file:
        kg2c_config_info = json.load(config_file)
    kg2_version = kg2c_config_info["kg2_version"]
    biolink_version = kg2c_config_info["biolink_version"]
    upload_to_s3 = kg2c_config_info["upload_to_s3"]
    build_synonymizer = kg2c_config_info["build_synonymizer"]
    logging.info(f"KG2 version to use is {kg2_version}")
    logging.info(f"Biolink model version to use is {biolink_version}")

    # Set up an RTX config_local.json file that points to the right KG2 and synonymizer
    _setup_rtx_config_local(kg2_version)

    # Build a new node synonymizer, if we're supposed to
    if build_synonymizer and not args.test:
        logging.info("Building node synonymizer off of specified KG2..")
        subprocess.check_call(["bash", "-x", f"{KG2C_DIR}/build-synonymizer.sh"])

    # Actually build KG2c
    logging.info("Creating KG2c files..")
    create_kg2c_files(args.test)
    logging.info("Recording meta KG info..")
    record_meta_kg_info(biolink_version, args.test)
    if upload_to_s3 and not args.test:
        _upload_output_files_to_s3()

    # Remove the config_local file we created and put original config_local back in place (if there was one)
    subprocess.call(["rm", f"{CODE_DIR}/config_local.json"])
    original_config_local_file = pathlib.Path(f"{CODE_DIR}/config_local.json_KG2CBUILDTEMP")
    if original_config_local_file.exists():
        subprocess.check_call(["mv", f"{CODE_DIR}/config_local.json_KG2CBUILDTEMP", f"{CODE_DIR}/config_local.json"])

    logging.info(f"DONE WITH KG2c BUILD! Took {round(((time.time() - start) / 60) / 60, 1)} hours")


if __name__ == "__main__":
    main()