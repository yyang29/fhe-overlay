import logging

from compiler import ir
from performance_model import utils


class CostEstimator:

  def __init__(self, he_params, hw_params, derating_factor=1.0):
    self._he_params = he_params
    self._hw_params = hw_params
    self._time_us = 0
    self._derating_factor = derating_factor

    logging.info("Cost Estimator initialized.")
    logging.info(f"HE parameters: {self._he_params}")
    logging.info(f"HW parameters: {self._hw_params}")

  def predict_costs(self, instructions):
    for instruction in instructions:
      # logging.info(f"Instruction: {instruction}")
      self._time_us += self._predict_cost(instruction)

    logging.info(f"Predicted time (us): {self._time_us}")

  def _predict_cost(self, instruction):
    if instruction["ir_op"].opcode == ir.OpCode.LimbElementwise:
      return self._predict_elementwise_cost(instruction)
    elif instruction["ir_op"].opcode == ir.OpCode.Ntt:
      return self._predict_ntt_cost(instruction)
    elif instruction["ir_op"].opcode == ir.OpCode.KskInnerProduct:
      return self._predict_ksk_inner_product_cost(instruction)
    elif instruction["ir_op"].opcode == ir.OpCode.Automorph:
      return self._predict_automorph_cost(instruction)
    elif instruction["ir_op"].opcode == ir.OpCode.Decompose:
      return self._predict_decompose_cost(instruction)
    elif instruction["ir_op"].opcode == ir.OpCode.BaseConv:
      return self._predict_base_conv_cost(instruction)
    else:
      # For nodes that are not materialized in the IR.
      return 0

  def _predict_elementwise_cost(self, instruction):
    logging.info(f"Predicting cost for operation: {instruction}")
    ir_op = instruction["ir_op"]
    logging.info(f"num_limbs: {ir_op.result.num_limbs}")
    logging.info(
        f"limb_size_bytes: {utils.get_limb_size_bytes(self._he_params)}")
    logging.info(f"input memory location: {ir_op.input_location}")
    num_limbs_read = ir_op.operand1.num_limbs
    num_limbs_write = ir_op.result.num_limbs
    if ir_op.input_location == ir.MemoryLocation.Dram:
      memory_read_time_us = utils.get_limb_size_bytes(
          self._he_params
      ) * num_limbs_read / self._hw_params.hbm_bandwidth_gbps / 1e3
    else:
      memory_read_time_us = 0

    if ir_op.output_location == ir.MemoryLocation.Dram:
      memory_write_time_us = utils.get_limb_size_bytes(
          self._he_params
      ) * num_limbs_write / self._hw_params.hbm_bandwidth_gbps / 1e3
    else:
      memory_write_time_us = 0

    compute_time_us = (num_limbs_read *
                       (self._he_params.N / self._hw_params.num_alu_lanes) *
                       utils.get_cycle_us(self._hw_params.frequency_mhz))
    logging.info(f"_estimate_limb_elementwise: "
                 f"compute_time_us: {compute_time_us}, "
                 f"memory_read_time_us: {memory_read_time_us}, "
                 f"memory_write_time_us: {memory_write_time_us}")

    latency_us = max(compute_time_us,
                     memory_read_time_us + memory_write_time_us)

    return latency_us * self._derating_factor

  def _predict_ntt_cost(self, instruction):
    pass

  def _predict_ksk_inner_product_cost(self, instruction):
    pass

  def _predict_automorph_cost(self, instruction):
    pass

  def _predict_decompose_cost(self, instruction):
    pass

  def _predict_base_conv_cost(self, instruction):
    pass
