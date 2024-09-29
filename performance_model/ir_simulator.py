#!/usr/bin/env python

import argparse
import csv

from .. import he_parameters


def parse_input_csv(input_file):
  with open(input_file, newline='') as csvfile:
    reader = csv.DictReader(csvfile)

    headers = reader.fieldnames

    data_dict = {}

    # Read the next row (data row) and populate the dictionary
    for row in reader:
      for header in headers:
        data_dict[header] = int(row[header])
      break  # Stop after the first data row

    return data_dict


def get_ir_ops(test_program_content):
  pass


def main():
  parser = argparse.ArgumentParser(
      description="FHE Overlay Accelerator Performance Simulator.")

  parser.add_argument("--benchmark",
                      "-b",
                      type=str,
                      help='Benchmark to run the simulation')
  parser.add_argument("--he_parameters",
                      "-p",
                      required=True,
                      help="HE parameter of the test program.")
  parser.add_argument("--fusion",
                      "-f",
                      action='store_true',
                      help="Enable fusion of operations.")
  parser.add_argument("--scheduling",
                      "-s",
                      action='store_true',
                      help="Enable scheduling of operations.")

  args = parser.parse_args()

  # Parse the HE parameters
  params = parse_input_csv(args.he_parameters)
  he_params = he_parameters.HeParameters(params['N'], params['L'],
                                         params['log_P'], params['dnum'],
                                         params['log_q_i'])
  he_params.display_parameters()

  ir_ops = []


if __name__ == "__main__":
  main()
