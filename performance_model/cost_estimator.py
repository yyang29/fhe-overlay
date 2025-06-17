import logging
import math
from typing import Tuple

from compiler import ir
from performance_model import utils


class CostEstimator:

  def __init__(self,
               he_params,
               hw_params,
               layout_optimization,
               memory_derating_factor=1.0,
               compute_derating_factor=1.0,
               num_fpgas=1):
    self._he_params = he_params
    self._hw_params = hw_params
    self._time_us = 0
    self._compute_time_us = 0
    self._communication_time_us = 0
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
    self._total_num_fpgas = num_fpgas
    self._node_group_to_num_fpga = []
    self._node_group_to_insts = []

    logging.info("Cost Estimator initialized.")
    logging.info(f"HE parameters: {self._he_params}")
    logging.info(f"HW parameters: {self._hw_params}")
    logging.info(f"Total # of FPGAs: {num_fpgas}")

  def auto_tune(self, instructions,
                previous_num_fpgas) -> Tuple[int, float, float]:

    first_inst = instructions[0]
    if ir.is_valid_opcode(first_inst["ir_op"].opcode) == False:
      return 0, 0, 0

    if previous_num_fpgas == 0:
      num_fpgas = self._total_num_fpgas
      compute_time_us = 0
      comm_time_us = 0
      for instruction in instructions:
        compute_time_us += self._predict_cost(instruction, num_fpgas)
      return num_fpgas, compute_time_us, comm_time_us

    # For cases where previous_num_fpgas > 0.
    best_result = (previous_num_fpgas, float('inf'), float('inf'))
    for num_fpgas in range(1, self._total_num_fpgas + 1):
      compute_time_us = 0
      comm_time_us = self.get_comm_time_us(first_inst, previous_num_fpgas,
                                           num_fpgas)
      for instruction in instructions:
        compute_time_us += self._predict_cost(instruction, num_fpgas)
      logging.info(f"Auto-tuning result: num_fpgas={num_fpgas}, "
                   f"compute_time_us={compute_time_us}, "
                   f"comm_time_us={comm_time_us}")
      if compute_time_us + comm_time_us < best_result[1] + best_result[2]:
        best_result = (num_fpgas, compute_time_us, comm_time_us)
    return best_result

  def get_comm_time_us(self, instruction, previous_num_fpgas,
                       current_num_fpgas):
    ir_op = instruction["ir_op"]
    if instruction["ir_op"].opcode == ir.OpCode.LimbElementwise:
      num_limbs_read = ir_op.operand1.num_limbs * 2
      send_comm_time_us = utils.get_limb_size_bytes(
          self._he_params) * num_limbs_read / self._get_effective_nic_bandwidth(
          ) / 1e3 / previous_num_fpgas
      receive_comm_time_us = utils.get_limb_size_bytes(
          self._he_params) * num_limbs_read / self._get_effective_nic_bandwidth(
          ) / 1e3 / current_num_fpgas
      return max(send_comm_time_us, receive_comm_time_us)
    elif instruction["ir_op"].opcode == ir.OpCode.Ntt:
      num_limbs_read = ir_op.operand.num_limbs
      send_comm_time_us = utils.get_limb_size_bytes(
          self._he_params) * num_limbs_read / self._get_effective_nic_bandwidth(
          ) / 1e3 / previous_num_fpgas
      receive_comm_time_us = utils.get_limb_size_bytes(
          self._he_params) * num_limbs_read / self._get_effective_nic_bandwidth(
          ) / 1e3 / current_num_fpgas
      return max(send_comm_time_us, receive_comm_time_us)
    elif instruction["ir_op"].opcode == ir.OpCode.KskInnerProduct:
      beta = self._he_params.beta
      num_limbs_per_digit = ir_op.alpha
      limb_read_bytes = beta * utils.get_limb_size_bytes(
          self._he_params) * num_limbs_per_digit
      send_comm_time_us = limb_read_bytes / self._get_effective_nic_bandwidth(
      ) / 1e3 / previous_num_fpgas
      receive_comm_time_us = limb_read_bytes / self._get_effective_nic_bandwidth(
      ) / 1e3 / current_num_fpgas
      return max(send_comm_time_us, receive_comm_time_us)
    elif instruction["ir_op"].opcode == ir.OpCode.Automorph:
      return self._predict_automorph_cost(instruction)
    elif instruction["ir_op"].opcode == ir.OpCode.Decompose:
      num_limbs_read = ir_op.operand.num_limbs
      send_comm_time_us = utils.get_limb_size_bytes(
          self._he_params) * num_limbs_read / self._get_effective_nic_bandwidth(
          ) / 1e3 / previous_num_fpgas
      receive_comm_time_us = utils.get_limb_size_bytes(
          self._he_params) * num_limbs_read / self._get_effective_nic_bandwidth(
          ) / 1e3 / current_num_fpgas
      return max(send_comm_time_us, receive_comm_time_us)
    elif instruction["ir_op"].opcode == ir.OpCode.BaseConv:
      num_limbs_read = ir_op.operand.num_limbs
      send_comm_time_us = utils.get_limb_size_bytes(
          self._he_params) * num_limbs_read / self._get_effective_nic_bandwidth(
          ) / 1e3 / previous_num_fpgas
      receive_comm_time_us = utils.get_limb_size_bytes(
          self._he_params) * num_limbs_read / self._get_effective_nic_bandwidth(
          ) / 1e3 / current_num_fpgas
      logging.info(
          f"BaseConv comm time: send {send_comm_time_us}, receive {receive_comm_time_us},"
          f" previous_num_fpgas {previous_num_fpgas}, current_num_fpgas {current_num_fpgas}"
      )
      return max(send_comm_time_us, receive_comm_time_us)
    else:
      raise ValueError(f"Unsupported opcode: {instruction['ir_op'].opcode}")

  def predict_costs(self, instructions):
    is_new_node_group = True
    for instruction in instructions:
      if is_new_node_group == False and instruction[
          "ir_op"].node_group != self._node_group_to_insts[-1][0][
              "ir_op"].node_group:
        is_new_node_group = True

      if is_new_node_group:
        self._node_group_to_insts.append([])
        self._node_group_to_num_fpga.append(0)
        is_new_node_group = False

      self._node_group_to_insts[-1].append(instruction)

    num_node_groups = len(self._node_group_to_insts)
    logging.info(f"Number of node groups: {num_node_groups}")

    for i in range(num_node_groups):
      instructions = self._node_group_to_insts[i]
      num_fpgas, compute_time_us, comm_time_us = self.auto_tune(
          instructions, self._total_num_fpgas)
      self._node_group_to_num_fpga[i] = num_fpgas
      self._time_us += compute_time_us + comm_time_us
      self._compute_time_us += compute_time_us
      self._communication_time_us += comm_time_us
      logging.info(
          f"Node group {i}: num_fpgas={num_fpgas}, "
          f"compute_time_us={compute_time_us}, comm_time_us={comm_time_us}")
    logging.info(f"Predicted time (us): {self._time_us}")
    logging.info(f"Predicted compute time (us): {self._compute_time_us}")
    logging.info(
        f"Predicted communication time (us): {self._communication_time_us}")
    logging.info(f"Node group to num FPGA: {self._node_group_to_num_fpga}")

    # Implementation of the original cost model
    # for instruction in instructions:
    #   logging.info(f"Estimating cost for {instruction=}")
    #   predicted_time = self._predict_cost(instruction)
    #   self._time_us += predicted_time
    #   self._ir_time_breakdown[instruction["ir_op"].opcode] += predicted_time

    # logging.info(f"Predicted time (us): {self._time_us}")
    # logging.info(f"IR time breakdown: {self._ir_time_breakdown}")

  def _predict_cost(self, instruction, num_fpgas=1):
    if instruction["ir_op"].opcode == ir.OpCode.LimbElementwise:
      return self._predict_elementwise_cost(instruction, num_fpgas)
    elif instruction["ir_op"].opcode == ir.OpCode.Ntt:
      return self._predict_ntt_cost(instruction, num_fpgas)
    elif instruction["ir_op"].opcode == ir.OpCode.KskInnerProduct:
      return self._predict_ksk_inner_product_cost(instruction, num_fpgas)
    elif instruction["ir_op"].opcode == ir.OpCode.Automorph:
      return self._predict_automorph_cost(instruction, num_fpgas)
    elif instruction["ir_op"].opcode == ir.OpCode.Decompose:
      return self._predict_decompose_cost(instruction, num_fpgas)
    elif instruction["ir_op"].opcode == ir.OpCode.BaseConv:
      return self._predict_base_conv_cost(instruction, num_fpgas)
    else:
      # For nodes that are not materialized in the IR.
      return 0

  def _predict_elementwise_cost(self, instruction, num_fpgas=1):
    logging.info(f"Predicting cost for operation: {instruction}")
    ir_op = instruction["ir_op"]
    num_limbs_read = math.ceil(ir_op.operand1.num_limbs * 2 /
                               num_fpgas)  # Binary op.
    num_limbs_write = math.ceil(ir_op.result.num_limbs / num_fpgas)
    if ir_op.input_location == ir.MemoryLocation.Dram:
      memory_read_time_us = utils.get_limb_size_bytes(
          self._he_params) * num_limbs_read / self._get_effective_hbm_bandwidth(
              ir.DataflowType.Limb) / 1e3
    else:
      memory_read_time_us = 0

    if ir_op.output_location == ir.MemoryLocation.Dram:
      memory_write_time_us = utils.get_limb_size_bytes(
          self._he_params
      ) * num_limbs_write / self._get_effective_hbm_bandwidth(
          ir.DataflowType.Limb) / 1e3
    else:
      memory_write_time_us = 0

    compute_time_us = (num_limbs_read *
                       (self._he_params.N / self._hw_params.num_alu_lanes) *
                       utils.get_cycle_us(self._hw_params.frequency_mhz)
                      ) / self._compute_derating_factor
    logging.info(f"_estimate_limb_elementwise: "
                 f"compute_time_us: {compute_time_us}, "
                 f"memory_read_time_us: {memory_read_time_us}, "
                 f"memory_write_time_us: {memory_write_time_us}")

    latency_us = max(compute_time_us,
                     memory_read_time_us + memory_write_time_us)

    return latency_us

  def _predict_ntt_cost(self, instruction, num_fpgas=1):
    logging.info(f"Predicting cost for operation: {instruction}")
    ir_op = instruction["ir_op"]
    num_limbs_read = math.ceil(ir_op.operand.num_limbs / num_fpgas)
    num_limbs_write = math.ceil(ir_op.result.num_limbs / num_fpgas)
    tf_read_bytes = utils.get_twiddle_factor_size_bytes(self._he_params,
                                                        num_limbs_read)
    limb_read_bytes = utils.get_limb_size_bytes(
        self._he_params) * num_limbs_read
    if ir_op.input_location == ir.MemoryLocation.Dram:
      total_read_bytes = tf_read_bytes + limb_read_bytes
    else:
      total_read_bytes = tf_read_bytes
    memory_read_time_us = total_read_bytes / self._get_effective_hbm_bandwidth(
        ir.DataflowType.Limb) / 1e3

    if ir_op.output_location == ir.MemoryLocation.Dram:
      total_write_bytes = utils.get_limb_size_bytes(
          self._he_params) * num_limbs_write
    else:
      total_write_bytes = 0
    memory_write_time_us = total_write_bytes / self._get_effective_hbm_bandwidth(
        ir.DataflowType.Limb) / 1e3

    alu_cycles = (num_limbs_read * math.log2(self._he_params.N) *
                  (self._he_params.N / self._hw_params.num_alu_lanes))
    permute_cycles = (num_limbs_read * math.log2(self._he_params.N) *
                      (self._he_params.N / self._hw_params.num_permute_lanes))
    compute_time_us = (max(alu_cycles, permute_cycles) *
                       utils.get_cycle_us(self._hw_params.frequency_mhz) /
                       self._compute_derating_factor)

    logging.debug(f"compute time (us): {compute_time_us}, "
                  f"memory read time (us): {memory_read_time_us} "
                  f"memory write time (us): {memory_write_time_us}.")
    if compute_time_us > memory_read_time_us + memory_write_time_us:
      logging.debug(f"NTT/INTT is compute bound.")
    else:
      logging.debug(f"NTT/INTT is memory bound.")
    latency_us = max(compute_time_us,
                     memory_read_time_us + memory_write_time_us)

    return latency_us

  def _predict_ksk_inner_product_cost(self, instruction, num_fpgas=1):
    logging.info(f"Predicting cost for operation: {instruction}")
    ir_op = instruction["ir_op"]
    ksk_read_bytes = utils.get_key_switch_keys_size_bytes(self._he_params)

    alpha = ir_op.alpha
    beta = self._he_params.beta
    k = self._he_params.k
    num_limbs = math.ceil((alpha * beta + k - 1) / num_fpgas)
    logging.info(
        f"alpha: {alpha}, beta: {beta}, k: {k}, num_limbs: {num_limbs}")
    num_limbs_per_digit = ir_op.alpha
    limb_read_bytes = num_limbs * utils.get_limb_size_bytes(self._he_params)
    total_read_bytes = (ksk_read_bytes + limb_read_bytes if ir_op.input_location
                        == ir.MemoryLocation.Dram else ksk_read_bytes)
    memory_read_time_us = total_read_bytes / self._get_effective_hbm_bandwidth(
        ir.DataflowType.Limb) / 1e3

    total_write_bytes = utils.get_limb_size_bytes(
        self._he_params
    ) * ir_op.result.num_rows * ir_op.result.num_columns * ir_op.alpha
    memory_write_time_us = total_write_bytes / self._get_effective_hbm_bandwidth(
        ir.DataflowType.Limb) / 1e3

    compute_time_us = ((2 * num_limbs * beta *
                        (self._he_params.N / self._hw_params.num_alu_lanes)) *
                       utils.get_cycle_us(self._hw_params.frequency_mhz))

    latency_us = max(compute_time_us,
                     memory_read_time_us + memory_write_time_us)

    logging.debug(f"Estimating innerprod latency. "
                  f"memory_read_time {memory_read_time_us} "
                  f"memory write time {memory_write_time_us} "
                  f"compute time {compute_time_us}")

    return latency_us

  def _predict_automorph_cost(self, instruction):
    return 0

  def _predict_decompose_cost(self, instruction, num_fpgas=1):
    logging.info(f"Predicting cost for operation: {instruction}")
    ir_op = instruction["ir_op"]
    num_limbs_read = math.ceil(ir_op.operand.num_limbs / num_fpgas)
    num_limbs_write = ir_op.result.num_rows * ir_op.result.num_columns
    if ir_op.input_location == ir.MemoryLocation.Dram:
      memory_read_time_us = utils.get_limb_size_bytes(
          self._he_params) * num_limbs_read / self._get_effective_hbm_bandwidth(
              ir.DataflowType.Limb) / 1e3
    else:
      memory_read_time_us = 0

    if ir_op.output_location == ir.MemoryLocation.Dram:
      memory_write_time_us = utils.get_limb_size_bytes(
          self._he_params
      ) * num_limbs_write / self._get_effective_hbm_bandwidth(
          ir.DataflowType.Limb) / 1e3
    else:
      memory_write_time_us = 0

    compute_time_us = 2 * (num_limbs_read *
                           (self._he_params.N / self._hw_params.num_alu_lanes) *
                           utils.get_cycle_us(self._hw_params.frequency_mhz)
                          ) / self._compute_derating_factor
    logging.info(f"_estimate_decompose: "
                 f"compute_time_us: {compute_time_us}, "
                 f"memory_read_time_us: {memory_read_time_us}, "
                 f"memory_write_time_us: {memory_write_time_us}")

    latency_us = max(compute_time_us,
                     memory_read_time_us + memory_write_time_us)

    return latency_us

  def _predict_base_conv_cost(self, instruction, num_fpgas=1):
    logging.info(f"Predicting cost for operation: {instruction}")
    ir_op = instruction["ir_op"]
    num_limbs_read = ir_op.operand.num_limbs / num_fpgas
    num_limbs_write = ir_op.result.num_limbs
    # For base conversion, we store (num_input_limbs - num_limbs_read) limbs
    # in the scratchpad. They are reused by num_output_limbs times.
    # For the other limbs, they have to be streamed to DRAM once for each
    # output limb.
    limb_read_bytes = math.ceil(
        utils.get_limb_size_bytes(self._he_params) * num_limbs_read / num_fpgas)
    if ir_op.input_location == ir.MemoryLocation.Dram:
      total_read_bytes = limb_read_bytes
    else:
      total_read_bytes = 0
    memory_read_time_us = total_read_bytes / self._get_effective_hbm_bandwidth(
        ir.DataflowType.Coefficient) / 1e3

    if ir_op.output_location == ir.MemoryLocation.Dram:
      total_write_bytes = math.ceil(
          utils.get_limb_size_bytes(self._he_params) * num_limbs_write /
          num_fpgas)
    else:
      total_write_bytes = 0
    memory_write_time_us = total_write_bytes / self._get_effective_hbm_bandwidth(
        ir.DataflowType.Coefficient) / 1e3

    compute_time_us = (
        num_limbs_read *
        (self._he_params.N / num_fpgas / self._hw_params.num_alu_lanes) *
        utils.get_cycle_us(
            self._hw_params.frequency_mhz)) / self._compute_derating_factor
    logging.info(f"_estimate_base_conv: "
                 f"compute_time_us: {compute_time_us}, "
                 f"memory_read_time_us: {memory_read_time_us}, "
                 f"memory_write_time_us: {memory_write_time_us}")

    latency_us = max(compute_time_us,
                     memory_read_time_us + memory_write_time_us)

    return latency_us

  def _get_effective_hbm_bandwidth(self, dataflow):
    if dataflow == ir.DataflowType.Coefficient and self._layout_optimization == False:
      return self._hw_params.hbm_bandwidth_gbps * self._memory_derating_factor / 4
    else:
      return self._hw_params.hbm_bandwidth_gbps * self._memory_derating_factor

  def _get_effective_nic_bandwidth(self):
    return self._hw_params.send_bandwidth_gbps * 0.7
