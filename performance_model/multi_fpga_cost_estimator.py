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
               compute_derating_factor=1.0):
    self._he_params = he_params
    self._hw_params = hw_params
    self._time_us = 0
    self._layout_optimization = layout_optimization
    self._memory_derating_factor = memory_derating_factor
    self._compute_derating_factor = compute_derating_factor
    self._ir_time_breakdown = {
        ir.OpCode.LimbElementwise: 0,
        ir.OpCode.Ntt: 0,
        ir.OpCode.KskInnerProduct: 0,
        ir.OpCode.Automorph: 0,
        ir.OpCode.Decompose: 0,
        ir.OpCode.BaseConv: 0,
        ir.OpCode.Merge: 0,
        ir.OpCode.Split: 0,
        ir.OpCode.NoOp: 0,
    }

    logging.info("Cost Estimator initialized.")
    logging.info(f"HE parameters: {self._he_params}")
    logging.info(f"HW parameters: {self._hw_params}")
