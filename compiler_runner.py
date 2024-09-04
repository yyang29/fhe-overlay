#!/usr/bin/env python

import isa
import argparse

def parse_arguments():
  parser = argparse.ArgumentParser(description='Test program argument parser')
  parser.add_argument('test_program', type=str, help='Path to the test program file')
  args = parser.parse_args()
  with open(args.test_program, 'r') as file:
    test_program_content = file.read()
  return test_program_content

test_program_content = parse_arguments()



def main():
  print(f"Hello, World! {isa.OpCode.ModAdd}")


if __name__ == "__main__":
  main()
