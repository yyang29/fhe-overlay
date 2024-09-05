#!/usr/bin/env python

import isa
import argparse
import compiler


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

  args = parser.parse_args()
  with open(args.test_program, 'r') as file:
    test_program_content = file.read()

  c = compiler.Compiler(test_program_content, args.assembly)
  c.run()


if __name__ == "__main__":
  main()
