import logging
import math
import os

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
logger = logging.getLogger('he_parameters')
logger.setLevel("DEBUG")


class HwParameters:

  def __init__(self,
               num_alu_lanes=512,
               num_permute_lanes=512,
               hbm_bandwidth_gbps=460):
    self.num_alu_lanes = num_alu_lanes
    self.num_permute_lanes = num_permute_lanes
    self.hbm_bandwidth_gbps = hbm_bandwidth_gbps
    self.scratchpad_read_bytes_per_cycle = 512 * 8
    self.scratchpad_write_bytes_per_cycle = 512 * 8
    self.frequency_mhz = 300
    self.send_bandwidth_gbps = 12.5
    self.receive_bandwidth_gbps = 12.5

  def display_parameters(self):
    logging.info("HW parameters are as shown below.")
    logging.info(f"\tNumber of ALU lanes: {self.num_alu_lanes}")
    logging.info(f"\tNumber of permute lanes: {self.num_permute_lanes}")
    logging.info(f"\tHBM bandwidth (GBps): {self.hbm_bandwidth_gbps}")
    logging.info(f"\tNIC send bandwidth (GBps): {self.send_bandwidth_gbps}")
    logging.info(
        f"\tNIC receive bandwidth (GBps): {self.receive_bandwidth_gbps}")

  @property
  def cycle_time_us(self):
    return 1 / (self.frequency_mhz * 1e6) * 1e6
