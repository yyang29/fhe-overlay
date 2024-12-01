import logging

from compiler import ir


class CostEstimator:

  def __init__(self, he_params, hw_params):
    self._he_params = he_params
    self._hw_params = hw_params
    self._time_cycles = 0

    logging.info("Cost Estimator initialized.")
    logging.info(f"HE parameters: {self._he_params}")
    logging.info(f"HW parameters: {self._hw_params}")

  def predict_costs(self, instructions):
    for instruction in instructions:
      logging.info(f"Instruction: {instruction}")
      self._time_cycles += self._predict_cost(instruction)

    logging.info(f"Predicted time (cycles): {self._time_cycles}")
    logging.info(
        f"Predicted time (us): {self._time_cycles * self._hw_params.cycle_time_us}"
    )

  def _predict_cost(self, instruction):
    if instruction["ir_op"].opcode == ir.OpCode.LimbElementwise:
      return self._predict_elementwise_cost()
    else:
      return 0
      # raise ValueError(f"Unknown instruction type: {instruction.opcode}")

  def _predict_elementwise_cost(self):
    return 1
