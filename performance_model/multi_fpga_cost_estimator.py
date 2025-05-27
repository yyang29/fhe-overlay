import logging
import math

from compiler import ir
from performance_model import utils


class CostEstimator:

  def __init__(self,
               he_params,
               hw_params,
               layout_optimization,
               memory_derating_factor=1.0,
               compute_derating_factor=1.0,
               io_derating_factor=1.0):
    self._he_params = he_params
    self._hw_params = hw_params
    self._time_us = 0
    self._layout_optimization = layout_optimization
    self._memory_derating_factor = memory_derating_factor
    self._compute_derating_factor = compute_derating_factor
    self._io_derating_factor = io_derating_factor

    logging.info("Multi-FPGA cost estimator initialized.")
    logging.info(f"HE parameters: {self._he_params}")
    logging.info(f"HW parameters: {self._hw_params}")

  def predict_costs(self, workload):
    print(f"Predicting costs for workload: {workload}")
