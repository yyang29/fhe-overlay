#!/usr/bin/env python

import argparse
from copy import deepcopy
import csv

from compiler import he_parameters, ir, data_types
from performance_model import latency_estimator


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


def get_ir_ops(benchmark: str, he_params: he_parameters.HeParameters):
  ir_ops = []
  if benchmark == "CtCtAdd" or benchmark == "PtCttAdd":
    limb = data_types.Limb(N=he_params.N, q=he_params.q_i)
    limb_vector = data_types.LimbVector(limb=limb, num_limbs=he_params.L)
    elm = ir.LimbElementwise(opcode=ir.OpCode.LimbElementwise,
                             elementwise_opcode=ir.LimbElementwiseOpCode.Add,
                             operand1=limb_vector,
                             operand2=limb_vector,
                             result=limb_vector)
    ir_ops.append(elm)
    elm2 = deepcopy(elm)
    ir_ops.append(elm2)
  elif benchmark == "CtCtMul":
    pass
  elif benchmark == "PtCtMul":
    pass
  elif benchmark == "Rescale":
    pass
  elif benchmark == "Rotate":
    pass
  elif benchmark == "Bootstrap":
    pass
  elif benchmark == "MatMul0":
    pass
  elif benchmark == "MatMul1":
    pass
  elif benchmark == "MatMul2":
    pass
  elif benchmark == "MatMul3":
    pass
  elif benchmark == "Conv0":
    pass
  elif benchmark == "Conv1":
    pass
  elif benchmark == "Conv2":
    pass
  elif benchmark == "Conv3":
    pass
  elif benchmark == "Mnist":
    pass
  elif benchmark == "Cifar":
    pass
  elif benchmark == "Resnet20":
    pass
  else:
    raise ValueError(f"Invalid benchmark: {benchmark}.")


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

  ir_ops = get_ir_ops(args.benchmark)

  estimator = latency_estimator.LatencyEstimator(he_params)
  estimator.estimate_latency(ir_ops)


if __name__ == "__main__":
  main()
