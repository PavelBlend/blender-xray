MOTIONS_COUNT_CHUNK = 0x0
BONEPART_NONE = 0xffff

# motion flags
FL_T_KEY_PRESENT = 1 << 0
FL_R_KEY_ABSENT = 1 << 1
KPF_T_HQ = 1 << 2

# motion params flags
FX = 1 << 0
STOP_AT_END = 1 << 1
NO_MIX = 1 << 2
SYNC_PART = 1 << 3
USE_FOOT_STEPS = 1 << 4
ROOT_MOVER = 1 << 5
IDLE = 1 << 6
USE_WEAPON_BONE = 1 << 7

# data size
CRC32_SZ = 4
QUAT_16_SZ = 4 * 2    # x, y, z, w 16 bit
TRN_8_SZ = 3 * 1    # x, y, z 8 bit
TRN_16_SZ = 3 * 2    # x, y, z 16 bit
TRN_FLOAT_SZ = 3 * 4    # x, y, z float
TRN_INIT_SZ = 3 * 4    # x, y, z float
TRN_SIZE_SZ = 3 * 4    # x, y, z float
