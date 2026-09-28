import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/alice/rc_2026_mid360/install/rc2026_mid360_sim'
