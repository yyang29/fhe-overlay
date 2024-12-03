import math


def get_limb_size_bytes(he_params):
  N = he_params.N
  coefficient_bits = he_params.log_q_i
  return int(math.ceil(coefficient_bits / 8) * N)


def get_plaintext_size_bytes(he_params):
  return get_limb_size_bytes(he_params) * he_params.L


def get_twiddle_factor_size_bytes(he_params, num_limbs):
  return get_limb_size_bytes(he_params) * num_limbs


def get_ciphertext_size_bytes(he_params):
  return get_limb_size_bytes(he_params) * he_params.L * 2


def get_key_switch_keys_size_bytes(he_params):
  alpha = he_params.alpha
  beta = he_params.beta
  k = he_params.k
  return 2 * beta * (alpha * beta + k - 1) * get_limb_size_bytes(he_params)


def get_cycle_us(frequency_mhz):
  return 1 / frequency_mhz
