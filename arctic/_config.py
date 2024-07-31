import logging
import os

import pymongo
from enum import Enum

logger = logging.getLogger(__name__)


# -----------------------------
# VersionStore configuration
# -----------------------------
# Controls is the write handler can only match handlers for the specific data type. No fallback to pickling if True.
STRICT_WRITE_HANDLER_MATCH = bool(os.environ.get('STRICT_WRITE_HANDLER_MATCH'))


# -----------------------------
# NdArrayStore configuration
# -----------------------------
# Extra sanity checks for corruption during appends. Introduces a 5-7% performance hit (off by default)
CHECK_CORRUPTION_ON_APPEND = bool(os.environ.get('CHECK_CORRUPTION_ON_APPEND'))


# -----------------------------
# Serialization configuration
# -----------------------------
# If a row is too large, then auto-expand the data chunk size from the default _CHUNK_SIZE (it is 2MB)
ARCTIC_AUTO_EXPAND_CHUNK_SIZE = bool(os.environ.get('ARCTIC_AUTO_EXPAND_CHUNK_SIZE'))

# This is the maximum size the auto-expanding can reach in an effort trying to reach the max
MAX_DOCUMENT_SIZE = int(pymongo.common.MAX_BSON_SIZE * 0.8)

# Enables the fast check for 'can_write' of the Pandas stores (significant speed-ups for large dataframes with objects)
FAST_CHECK_DF_SERIALIZABLE = bool(os.environ.get('FAST_CHECK_DF_SERIALIZABLE'))


# -------------------------------
# Forward pointers configuration
# -------------------------------
# This enum provides all the available modes of operation for Forward pointers
class FwPointersCfg(Enum):
    ENABLED = 0   # use only forward pointers, don't update segment parent references
    DISABLED = 1  # operate in legacy mode, update segment parent references, don't add forward pointers
    HYBRID = 2    # maintain both forward pointers and parent references in segments; for reads prefer fw pointers


# The version document key used to store the ObjectIDs of segments
FW_POINTERS_REFS_KEY = 'SEGMENT_SHAS'

# The version document key holding the FW pointers configuration used to create this version (enabled/disabled/hybrid)
FW_POINTERS_CONFIG_KEY = 'FW_POINTERS_CONFIG'

# This variable has effect only in Hybrid mode, and controls whether forward and legacy pointers are cross-verified
ARCTIC_FORWARD_POINTERS_RECONCILE = False
ARCTIC_FORWARD_POINTERS_CFG = FwPointersCfg.DISABLED

# ---------------------------
# Compression configuration
# ---------------------------
# Use the parallel LZ4 compress (default is True)
ENABLE_PARALLEL = not os.environ.get('DISABLE_PARALLEL')

# Use the high-compression configuration for LZ4 (trade runtime speed for better compression ratio)
LZ4_HIGH_COMPRESSION = bool(os.environ.get('LZ4_HIGH_COMPRESSION'))

# For a guide on how to tune the following parameters, read:
#     arctic/benchmarks/lz4_tuning/README.txt
# The size of the compression thread pool.
# Rule of thumb: use 2 for non HC (VersionStore/NDarrayStore/PandasStore, and 8 for HC (TickStore).
LZ4_WORKERS = os.environ.get('LZ4_WORKERS', 2)

# The minimum required number of chunks to use parallel compression
LZ4_N_PARALLEL = os.environ.get('LZ4_N_PARALLEL', 16)

# Minimum data size to use parallel compression
LZ4_MINSZ_PARALLEL = os.environ.get('LZ4_MINSZ_PARALLEL', 0.5 * 1024 ** 2)  # 0.5 MB

# Enable this when you run the benchmark_lz4.py
BENCHMARK_MODE = False


# ---------------------------
# Async arctic
# ---------------------------
# Configures the size of the workers pools used for async arctic requests
ARCTIC_ASYNC_NWORKERS = os.environ.get('ARCTIC_ASYNC_NWORKERS', 4)


# -------------------------------
# Flag used to convert byte column/index/column names to unicode when read back.
# -------------------------------
FORCE_BYTES_TO_UNICODE = bool(os.environ.get('FORCE_BYTES_TO_UNICODE'))

# -------------------------------
# Flag used for indicating caching levels. For now just for list_libraries.
# -------------------------------
ENABLE_CACHE = bool(os.environ.get('ENABLE_CACHE'))

# -------------------------------
# Currently we try to bson encode if the data is less than a given size and store it in
# the version collection, but pickling might be preferable if we have characters that don't
# play well with the bson encoder or if you always want your data in the data collection.
# -------------------------------
SKIP_BSON_ENCODE_PICKLE_STORE = bool(os.environ.get('SKIP_BSON_ENCODE_PICKLE_STORE'))

# -------------------------------
# Maximum size up to which the input will be bson encoded and stored in the version doc instead of being pickled in
# the version store. For very large input (> 10 MB) we ignore this option and fall back to using pickle.
# -------------------------------
MAX_BSON_ENCODE = os.environ.get('MAX_BSON_ENCODE', 256 * 1024)  # 256 KB
