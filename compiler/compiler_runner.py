#!/usr/bin/env python

import argparse
import compiler
import csv

import isa
import he_parameters


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


def main():
  parser = argparse.ArgumentParser(
      description="FHE Overlay Accelerator Compiler Runner.")

  parser.add_argument("--test_program",
                      "-t",
                      type=str,
                      help='Path to the test program file')
  parser.add_argument("--assembly",
                      "-a",
                      type=str,
                      default="/tmp/output.s",
                      help='Path to the assembly output file')
  parser.add_argument("--he_parameters",
                      "-p",
                      required=True,
                      help="HE parameter of the test program.")

  args = parser.parse_args()

  # Parse the HE parameters
  params = parse_input_csv(args.he_parameters)
  he_params = he_parameters.HeParameters(params['N'], params['L'],
                                         params['log_P'], params['dnum'],
                                         params['log_q_i'])
  he_params.display_parameters()

  with open(args.test_program, 'r') as file:
    test_program_content = file.read()

  c = compiler.Compiler(test_program_content, args.assembly, he_params.L)
  c.run()


if __name__ == "__main__":
  main()
