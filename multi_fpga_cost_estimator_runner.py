#!/usr/bin/env python

import argparse
import csv
import logging

from compiler import he_parameters
from performance_model import hw_parameters
from performance_model import multi_fpga_cost_estimator
from performance_model import multi_fpga_operator


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
  parser.add_argument("--num_fpgas",
                      "-f",
                      type=int,
                      default=1,
                      help="Number of FPGAs in the design.")
  args = parser.parse_args()

  # Parse the HE parameters
  params = parse_input_csv(args.he_parameters)
  he_params = he_parameters.HeParameters(params['N'], params['L'],
                                         params['log_P'], params['dnum'],
                                         params['log_q_i'])
  he_params.display_parameters()

  print(f"Number of FPGAs: {args.num_fpgas}")

  estimator = multi_fpga_cost_estimator.CostEstimator(
      he_params, hw_parameters.HwParameters(), layout_optimization=False)

  operator = multi_fpga_operator.Gemm(m=1024, n=1024, k=1024)

  estimator.predict_costs(operator)


if __name__ == "__main__":
  main()
