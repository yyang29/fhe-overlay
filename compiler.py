import isa


class Compiler():

  def __init__(self, test_program: str, assembly_output: str):
    self._test_program = test_program
    self._assembly_output = assembly_output

  def run(self):
    print(self._test_program)
    print(f"Hello, World! {isa.OpCode.ModAdd}")
    print(self._assembly_output)

  def _build_dag(self):
    pass
