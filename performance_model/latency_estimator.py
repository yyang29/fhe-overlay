import platform_constants
import utils

import logging
import math
import os

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
logger = logging.getLogger('latency_estimator')
logger.setLevel("INFO")


class LatencyEstimator:
  design_params = None

  def __init__(self, he_params, op, constraints, logger=None):
    self.he_params = he_params
    self.op = op
    self.constraints = constraints
    self.logger = logger
    self.derating_factor = 1.21083452

    # scratchpad data reuse policy:
    # first, reuse twiddle factors
    # then, reuse 1/2 ciphertext across sub-routines
    # then, reuse KSK plaintext (column by column)
    # then, alpha limbs for basis conversion

  def estimate_latency(self, design_params):
    self.design_params = design_params

    if self.op == "CtCtAdd" or self.op == "CtCtSub":
      latency_us = self._estimate_limb_elementwise(
          platform_constants.POLYNOMIALS_PER_CIPHERTEXT * self.he_params.L,
          2 * platform_constants.POLYNOMIALS_PER_CIPHERTEXT * self.he_params.L,
          platform_constants.POLYNOMIALS_PER_CIPHERTEXT * self.he_params.L)
      logger.info(f"{self.op} takes {latency_us} us.")
      return latency_us

    elif self.op == "CtCtMult":
      latency_us = self._estimate_limb_elementwise(
          platform_constants.POLYNOMIALS_PER_CIPHERTEXT * self.he_params.L,
          4 * platform_constants.POLYNOMIALS_PER_CIPHERTEXT * self.he_params.L,
          3 * self.he_params.L)
      latency_ks = self._estimate_key_switch()
      logger.info(f"latency_limbmult: {latency_us}")
      return latency_us + latency_ks

    elif self.op == "Rotate":
      latency_automorph = self._estimate_automorph(self.he_params.L,
                                                   self.he_params.L,
                                                   self.he_params.L)
      latency_automorph += (self.he_params.L *
                            utils.get_limb_size_bytes(self.he_params) * 4 /
                            self.constraints.bandwidth_gbps / 1e3)
      latency_ks = self._estimate_key_switch()
      return latency_automorph + latency_ks

    elif self.op == "KeySwitch":
      assert 0

    elif self.op == "Rescale":
      L = self.he_params.L
      num_limbs_available = self._get_max_num_limbs_in_scratchpad()
      if num_limbs_available <= self.he_params.L:
        # Scratchpad allocation policy
        #  Intt produces num_limbs_available limbs on-chip while streams
        #  (L-num_limbs_available) limbs to DRAM.
        #  Baseconv reuse the num_limbs_available limbs and reads (L-num_limbs_available)
        #  L-1 times, writes out all the output limbs to DRAM.
        #  No reuse on Intt and Ntt twiddle factors.
        intt_output_limbs_in_scratchpad = num_limbs_available
        baseconv_output_limbs_in_scratchpad = 0
        intt_tf_sets_in_scratchpad = 0
        ntt_tf_sets_in_scratchpad = 0
      elif num_limbs_available <= 2 * self.he_params.L:
        # Scratchpad allocation policy
        #  Intt produces num_limbs_available/2 limbs on-chip while streams
        #  (L-num_limbs_available/2) limbs to DRAM.
        #  Baseconv reuse the num_limbs_available/2 limbs and reads (L-num_limbs_available/2)
        #  L-1 times, writes (L-1-num_limbs_available/2) output limbs to DRAM.
        #  No reuse on Intt and Ntt twiddle factors.
        intt_output_limbs_in_scratchpad = num_limbs_available // 2
        baseconv_output_limbs_in_scratchpad = min(num_limbs_available // 2,
                                                  self.he_params.L - 1)
        intt_tf_sets_in_scratchpad = 0
        ntt_tf_sets_in_scratchpad = 0
      else:
        # Scratchpad allocation policy
        #  Intt produces L limbs on-chip while streams 0 limbs to DRAM.
        #  Baseconv reuses the L limbs and writes 0 output limbs to DRAM.
        #  There could be reuse on Intt and Ntt twiddle factors depending on
        #  how much scratchpad space is left.
        intt_output_limbs_in_scratchpad = self.he_params.L
        baseconv_output_limbs_in_scratchpad = self.he_params.L - 1
        num_limbs_left = num_limbs_available - 2 * self.he_params.L
        intt_tf_sets_in_scratchpad = max(min(num_limbs_left, self.he_params.L),
                                         0)
        num_limbs_left -= intt_tf_sets_in_scratchpad
        ntt_tf_sets_in_scratchpad = max(
            min(num_limbs_left, self.he_params.L - 1), 0)

      logger.debug(
          f"scratchpad allocation: "
          f"intt output limbs - {intt_output_limbs_in_scratchpad}, "
          f"baseconv output limbs - {baseconv_output_limbs_in_scratchpad}, "
          f"intt tf sets - {intt_tf_sets_in_scratchpad}, "
          f"ntt tf sets - {ntt_tf_sets_in_scratchpad}.")

      # Polynomial 0
      p0_latency_intt = self._estimate_ntt_new(
          L, L, L - intt_output_limbs_in_scratchpad, L)
      p0_latency_base_conv = self._estimate_base_conv_new(
          L, L - 1, L - intt_output_limbs_in_scratchpad,
          L - 1 - baseconv_output_limbs_in_scratchpad)
      p0_latency_base_conv = self._estimate_base_conv_new(
          L, L - 1, L - 7 * intt_output_limbs_in_scratchpad // 8,
          L - 1 - baseconv_output_limbs_in_scratchpad)
      p0_latency_ntt = self._estimate_ntt_new(
          L - 1, L - 1 - baseconv_output_limbs_in_scratchpad, L - 1, L - 1)
      p0_latency_us = p0_latency_intt + p0_latency_base_conv + p0_latency_ntt
      # Polynomial 1
      p1_latency_intt = self._estimate_ntt_new(
          L, L, L - intt_output_limbs_in_scratchpad,
          L - intt_tf_sets_in_scratchpad)
      p1_latency_base_conv = self._estimate_base_conv_new(
          L, L - 1, L - intt_output_limbs_in_scratchpad,
          L - 1 - baseconv_output_limbs_in_scratchpad)
      p1_latency_base_conv = self._estimate_base_conv_new(
          L, L - 1, L - 7 * intt_output_limbs_in_scratchpad // 8,
          L - 1 - baseconv_output_limbs_in_scratchpad)
      p1_latency_ntt = self._estimate_ntt_new(
          L - 1, L - 1 - baseconv_output_limbs_in_scratchpad, L - 1,
          L - 1 - ntt_tf_sets_in_scratchpad)
      p1_latency_us = p1_latency_intt + p1_latency_base_conv + p1_latency_ntt

      latency_us = p0_latency_us + p1_latency_us
      logger.info(f"{self.op} takes {latency_us} us.")

      return latency_us

    else:
      raise ValueError

  def _estimate_key_switch(self):
    # The dataflow is one digit at a time.
    # Fuse all the sub-routines until KskInnerProd.
    # For KskInnerProd, we store the two partial sums on-chip (if available).
    # Each partial sum has (alpha * beta + k - 1) limbs.
    # Then we perform ModDown on the first polynomial (alpha * beta + k - 1) limbs.
    # Then we perform ModDown on the second polynomial, and fuse with the final
    # addition.
    # ---- Scratchpad Allocation Policy
    # 1st -- alpha limbs --> fuse with INTT immediately
    # 2nd -- base conv, fuse with NTT immediately fuse with KskInnerProd
    #     -- alpha limbs can be evicted.
    #     -- if have space for 2 * (alpha * beta + k - 1) limbs, run ModDown
    L = self.he_params.L
    alpha = self.he_params.alpha
    beta = self.he_params.beta
    k = self.he_params.k
    num_limbs_available = self._get_max_num_limbs_in_scratchpad()

    # Dataflow planning goes below
    # decomp fused with INTT next, no write out to DRAM
    if num_limbs_available > alpha:
      modup_intt_output_limbs_in_scratchpad = alpha
    else:
      modup_intt_output_limbs_in_scratchpad = num_limbs_available
    # Modup-baseconv fused with ntt next, no need to write out to DRAM
    modup_baseconv_output_limbs_in_scratchpad = alpha * beta + k - 1
    # Modup-ntt fused with innerprod next, no need to write out to DRAM
    modup_ntt_output_limbs_in_scratchpad = alpha * beta + k - 1
    num_limbs_left = num_limbs_available - modup_intt_output_limbs_in_scratchpad
    num_limbs_left = 0 if num_limbs_left < 0 else num_limbs_left
    if num_limbs_left > 2 * (alpha * beta + k - 1):
      kskinnerprod_output_limbs_in_scratchpad = 2 * (alpha * beta + k - 1)
    else:
      kskinnerprod_output_limbs_in_scratchpad = num_limbs_left
    # Moddown INTT get SRAM space if there is lefe over from innerprod.
    num_limbs_left = num_limbs_available - kskinnerprod_output_limbs_in_scratchpad
    assert (num_limbs_left >= 0)
    if num_limbs_left > 2 * (alpha * beta + k - 1):
      moddown_intt_output_limbs_in_scratchpad = 2 * (alpha * beta + k - 1)
    else:
      moddown_intt_output_limbs_in_scratchpad = num_limbs_left
    # baseconv is fused with NTT next.
    moddown_baseconv_output_limbs_in_scratchpad = L - 1
    moddown_ntt_output_limbs_in_scratchpad = 0

    latency_decomp = self._estimate_decomp(L, 0)

    latency_modup_intt = self._estimate_ntt_new(alpha, 0, alpha, alpha)
    latency_modup_intt *= beta

    latency_modup_base_conv = self._estimate_base_conv_new(
        alpha, alpha * beta + k - 1,
        alpha - modup_intt_output_limbs_in_scratchpad, 0)
    latency_modup_base_conv *= beta
    # TODO
    latency_modup_base_conv += (L * utils.get_limb_size_bytes(self.he_params) *
                                4 / self.constraints.bandwidth_gbps / 1e3)

    latency_modup_ntt = self._estimate_ntt_new(alpha * beta + k - 1 - alpha, 0,
                                               alpha * beta + k - 1 - alpha,
                                               alpha * beta + k - 1 - alpha)
    latency_modup_ntt *= beta

    # Reset scratchpad after modup NTT.
    num_limbs_available = self._get_max_num_limbs_in_scratchpad()
    if num_limbs_available > 2 * (alpha * beta + k - 1):
      kskinnerprod_output_limbs_in_scratchpad = 2 * (alpha * beta + k - 1)
    else:
      kskinnerprod_output_limbs_in_scratchpad = num_limbs_available
    latency_inner_prod = self._estimate_inner_prod(alpha * beta + k - 1, 0)

    latency_moddown_intt = self._estimate_ntt_new(alpha * beta + k - 1, 0,
                                                  alpha * beta + k - 1, 0)
    latency_moddown_intt *= 2
    # TODO
    latency_modup_base_conv += (L * utils.get_limb_size_bytes(self.he_params) *
                                3 / self.constraints.bandwidth_gbps / 1e3)

    latency_moddown_base_conv = self._estimate_base_conv_new(
        alpha * beta + k - 1, self.he_params.L - 1,
        alpha * beta + k - 1 - kskinnerprod_output_limbs_in_scratchpad // 2, 0)
    latency_moddown_base_conv *= 2

    latency_moddown_ntt = self._estimate_ntt_new(L - 1, 0, L - 1, 0)
    latency_moddown_ntt *= 2

    logger.info(
        f"latency_decomp: {latency_decomp}, "
        f"latency_modup: {latency_modup_intt + latency_modup_base_conv + latency_modup_ntt} "
        f"latency_innerprod: {latency_inner_prod}, "
        f"latency_moddown: {latency_moddown_intt + latency_moddown_base_conv + latency_moddown_ntt}"
    )

    return (latency_decomp + latency_modup_intt + latency_modup_base_conv +
            latency_modup_ntt + latency_inner_prod + latency_moddown_intt +
            latency_moddown_base_conv + latency_moddown_ntt)

  def _estimate_limb_elementwise(self, num_limbs, num_limbs_read,
                                 num_limbs_write):
    memory_read_time_us = utils.get_limb_size_bytes(
        self.he_params) * num_limbs_read / self.constraints.bandwidth_gbps / 1e3
    memory_write_time_us = utils.get_limb_size_bytes(
        self.he_params
    ) * num_limbs_write / self.constraints.bandwidth_gbps / 1e3
    compute_time_us = (
        num_limbs * (self.he_params.N / self.design_params.num_modular_alus) *
        utils.get_cycle_us(self.constraints.frequency_mhz))
    logger.debug(f"_estimate_limb_elementwise: "
                 f"compute_time_us: {compute_time_us}, "
                 f"memory_read_time_us: {memory_read_time_us}, "
                 f"memory_write_time_us: {memory_write_time_us}")

    latency_us = max(compute_time_us,
                     memory_read_time_us + memory_write_time_us)

    return latency_us * self.derating_factor

  def _estimate_ntt(self,
                    num_limbs,
                    tf_reuse_ratio=0.0,
                    input_fused=False,
                    output_fused=False):
    tf_read_bytes = utils.get_twiddle_factor_size_bytes(
        self.he_params, num_limbs) * (1 - tf_reuse_ratio)
    limb_read_bytes = 0 if input_fused else utils.get_limb_size_bytes(
        self.he_params) * num_limbs
    total_read_bytes = tf_read_bytes + limb_read_bytes
    memory_read_time_us = total_read_bytes / self.constraints.bandwidth_gbps / 1e3

    total_write_bytes = 0 if output_fused else utils.get_limb_size_bytes(
        self.he_params) * num_limbs
    memory_write_time_us = total_write_bytes / self.constraints.bandwidth_gbps / 1e3

    # Factor of "1.5" in the alu_cycles to indicate the mult and add/sub require
    # separate issue slots.
    alu_cycles = (1.5 * num_limbs * math.log2(self.he_params.N) *
                  (self.he_params.N / self.design_params.num_modular_alus))
    permute_cycles = (
        num_limbs * math.log2(self.he_params.N) *
        (self.he_params.N / self.design_params.permute_throughput))
    compute_time_us = (max(alu_cycles, permute_cycles) *
                       utils.get_cycle_us(self.constraints.frequency_mhz))

    latency_us = max(compute_time_us,
                     memory_read_time_us + memory_write_time_us)

    return latency_us * self.derating_factor

  def _estimate_base_conv(self, num_input_limbs, num_output_limbs,
                          num_compute_limbs):
    memory_read_time_us = (utils.get_limb_size_bytes(self.he_params) *
                           num_input_limbs / self.constraints.bandwidth_gbps /
                           1e3)
    memory_write_time_us = (utils.get_limb_size_bytes(self.he_params) *
                            num_output_limbs / self.constraints.bandwidth_gbps /
                            1e3)
    compute_time_us = (
        2 * num_compute_limbs *
        (self.he_params.N / self.design_params.num_modular_alus) *
        utils.get_cycle_us(self.constraints.frequency_mhz))

    latency_us = max(compute_time_us,
                     memory_read_time_us + memory_write_time_us)

    return latency_us * self.derating_factor

  def _estimate_decomp(self, num_limbs_read, num_limbs_write):
    logger.debug(f"Estimating decomp latency. "
                 f"num_limbs_read = {num_limbs_read} "
                 f"num_limbs_write = {num_limbs_write}")
    # only one polynomial goes through decomp.
    limb_read_bytes = utils.get_limb_size_bytes(self.he_params) * num_limbs_read
    memory_read_time_us = limb_read_bytes / self.constraints.bandwidth_gbps / 1e3

    # only one polynomial goes through decomp.
    limb_write_bytes = utils.get_limb_size_bytes(
        self.he_params) * num_limbs_write
    memory_write_time_us = limb_write_bytes / self.constraints.bandwidth_gbps / 1e3

    compute_time_us = (
        2 * self.he_params.L *
        (self.he_params.N / self.design_params.num_modular_alus) *
        utils.get_cycle_us(self.constraints.frequency_mhz))

    logger.debug(f"Estimating decomp latency. {self.he_params.L} "
                 f"memory_read_time {memory_read_time_us} "
                 f"memory write time {memory_write_time_us} "
                 f"compute time {compute_time_us}")

    latency_us = max(compute_time_us,
                     memory_read_time_us + memory_write_time_us)

    return latency_us * self.derating_factor

  def _estimate_inner_prod(self, num_limbs_read_per_digit, num_limbs_write):
    ksk_read_bytes = utils.get_key_switch_keys_size_bytes(self.he_params)

    alpha = self.he_params.alpha
    beta = self.he_params.beta
    k = self.he_params.k
    num_limbs = alpha * beta + k - 1

    limb_read_bytes = beta * utils.get_limb_size_bytes(
        self.he_params) * num_limbs_read_per_digit
    total_read_bytes = ksk_read_bytes + limb_read_bytes
    memory_read_time_us = total_read_bytes / self.constraints.bandwidth_gbps / 1e3

    total_write_bytes = utils.get_limb_size_bytes(
        self.he_params) * num_limbs_write
    memory_write_time_us = total_write_bytes / self.constraints.bandwidth_gbps / 1e3

    compute_time_us = (
        (2 * num_limbs * beta *
         (self.he_params.N / self.design_params.num_modular_alus)) *
        utils.get_cycle_us(self.constraints.frequency_mhz))

    latency_us = max(compute_time_us,
                     memory_read_time_us + memory_write_time_us)

    logger.debug(f"Estimating innerprod latency. "
                 f"memory_read_time {memory_read_time_us} "
                 f"memory write time {memory_write_time_us} "
                 f"compute time {compute_time_us}")

    return latency_us * self.derating_factor

  def _estimate_automorph(self, num_limbs, num_limbs_read, num_limbs_write):
    memory_read_time_us = utils.get_limb_size_bytes(
        self.he_params) * num_limbs_read / self.constraints.bandwidth_gbps / 1e3
    memory_write_time_us = utils.get_limb_size_bytes(
        self.he_params
    ) * num_limbs_write / self.constraints.bandwidth_gbps / 1e3
    compute_time_us = (
        num_limbs * (self.he_params.N / self.design_params.permute_throughput) *
        utils.get_cycle_us(self.constraints.frequency_mhz))
    logger.debug(f"_estimate_automorph: "
                 f"compute_time_us: {compute_time_us}, "
                 f"memory_read_time_us: {memory_read_time_us}, "
                 f"memory_write_time_us: {memory_write_time_us}")

    latency_us = max(compute_time_us,
                     memory_read_time_us + memory_write_time_us)

    return latency_us * self.derating_factor

  def _estimate_ntt_new(self, num_limbs, num_limbs_read, num_limbs_write,
                        num_tf_sets_read):
    logger.debug(f"Estimating NTT/INTT latency. "
                 f"num_limbs={num_limbs} "
                 f"num_limbs_read={num_limbs_read} "
                 f"num_limbs_write={num_limbs_write} "
                 f"num_tf_sets_read={num_tf_sets_read}.")
    tf_read_bytes = utils.get_twiddle_factor_size_bytes(self.he_params,
                                                        num_tf_sets_read)
    limb_read_bytes = utils.get_limb_size_bytes(self.he_params) * num_limbs_read
    total_read_bytes = tf_read_bytes + limb_read_bytes
    memory_read_time_us = total_read_bytes / self.constraints.bandwidth_gbps / 1e3

    total_write_bytes = utils.get_limb_size_bytes(
        self.he_params) * num_limbs_write
    memory_write_time_us = total_write_bytes / self.constraints.bandwidth_gbps / 1e3

    alu_cycles = (num_limbs * math.log2(self.he_params.N) *
                  (self.he_params.N / self.design_params.num_modular_alus))
    permute_cycles = (
        num_limbs * math.log2(self.he_params.N) *
        (self.he_params.N / self.design_params.permute_throughput))
    compute_time_us = (max(alu_cycles, permute_cycles) *
                       utils.get_cycle_us(self.constraints.frequency_mhz))

    logger.debug(f"compute time (us): {compute_time_us}, "
                 f"memory read time (us): {memory_read_time_us} "
                 f"memory write time (us): {memory_write_time_us}.")
    if compute_time_us > memory_read_time_us + memory_write_time_us:
      logger.debug(f"NTT/INTT is compute bound.")
    else:
      logger.debug(f"NTT/INTT is memory bound.")
    latency_us = max(compute_time_us,
                     memory_read_time_us + memory_write_time_us)

    return latency_us * self.derating_factor

  def _estimate_base_conv_new(self, num_input_limbs, num_output_limbs,
                              num_limbs_read, num_limbs_write):
    logger.debug(f"Estimating base conversion latency. "
                 f"num_input_limbs={num_input_limbs} "
                 f"num_output_limbs={num_output_limbs} "
                 f"num_limbs_read={num_limbs_read} "
                 f"num_limbs_write={num_limbs_write}.")
    # For base conversion, we store (num_input_limbs - num_limbs_read) limbs
    # in the scratchpad. They are reused by num_output_limbs times.
    # For the other limbs, they have to be streamed to DRAM once for each
    # output limb.
    memory_read_time_us = (utils.get_limb_size_bytes(self.he_params) *
                           num_limbs_read * num_output_limbs /
                           self.constraints.bandwidth_gbps / 1e3)
    memory_write_time_us = (utils.get_limb_size_bytes(self.he_params) *
                            num_limbs_write / self.constraints.bandwidth_gbps /
                            1e3)
    compute_time_us = (
        2 * num_output_limbs *
        (self.he_params.N / self.design_params.num_modular_alus) *
        utils.get_cycle_us(self.constraints.frequency_mhz))

    logger.debug(f"compute time (us): {compute_time_us}, "
                 f"memory read time (us): {memory_read_time_us} "
                 f"memory write time (us): {memory_write_time_us}.")
    if compute_time_us > memory_read_time_us + memory_write_time_us:
      logger.debug(f"base_conv is compute bound.")
    else:
      logger.debug(f"base_conv is memory bound.")
    latency_us = max(compute_time_us,
                     memory_read_time_us + memory_write_time_us)

    return latency_us * self.derating_factor

  def _get_max_num_limbs_in_scratchpad(self):
    limb_size_bytes = utils.get_limb_size_bytes(self.he_params)
    scratchpad_size_bytes = self.design_params.scratchpad_size_bytes

    num_limbs = scratchpad_size_bytes // limb_size_bytes
    logger.debug(f"Design point can store {num_limbs} limbs.")
    return num_limbs
