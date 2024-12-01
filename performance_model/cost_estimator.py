import logging

from compiler import ir


class CostEstimator:

  def __init__(self, he_params, hw_params):
    self._he_params = he_params
    self._hw_params = hw_params

    logging.info("Cost Estimator initialized.")
    logging.info(f"HE parameters: {self._he_params}")
    logging.info(f"HW parameters: {self._hw_params}")

  def predict_costs(self, instructions):
    operation = instructions[0]
    logging.info(f"Operation: {operation}")
