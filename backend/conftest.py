"""
Pytest configuration for AuraTour backend.
Ensures thread limits are set for OpenBLAS / OMP on Windows to prevent memory allocation errors.
"""

import os
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
