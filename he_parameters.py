import logging
import math
import os

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
logger = logging.getLogger('he_parameters')
logger.setLevel("DEBUG")


class HeParameters:
  # Class members
  N = None
  L = None
  log_P = None
  dnum = None
  log_q_i = None
  alpha = None
  beta = None

  def __init__(self, N, L, log_P, dnum, log_q_i):
    self.N = N
    self.L = L
    self.log_P = log_P
    self.dnum = dnum
    self.log_q_i = log_q_i

    # Derived parameters
    self.alpha = math.ceil((L + 1) / dnum)
    self.beta = dnum
    self.k = math.ceil(self.log_P / self.log_q_i)

  def display_parameters(self):
    logger.info("HE parameters are as shown below.")
    logger.info(f"\tN: {self.N}")
    logger.info(f"\tL: {self.L}")
    logger.info(f"\tlog_P: {self.log_P}")
    logger.info(f"\tdnum: {self.dnum}")
    logger.info(f"\tlog_q_i: {self.log_q_i}")
    logger.info(f"\talpha: {self.alpha}")
    logger.info(f"\tbeta: {self.beta}")
    logger.info(f"\tk: {self.k}")
