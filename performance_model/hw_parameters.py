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

  def display_parameters(self):
    logging.info("HW parameters are as shown below.")
    logging.info(f"\tNumber of ALU lanes: {self.num_alu_lanes}")
    logging.info(f"\tNumber of permute lanes: {self.num_permute_lanes}")
    logging.info(f"\tHBM bandwidth (Gbps): {self.hbm_bandwidth_gbps}")
