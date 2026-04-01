import psutil
import os

# =========================
# Config
# =========================
HISTORY = 100       # number of samples shown
INTERVAL = 500      # milliseconds between updates
N_CORES = psutil.cpu_count(logical=True)


# =========================
# System data collection
# =========================
def get_freqs():
    """Return (freqs, max_freqs) lists in GHz for each logical core."""
    freqs = []
    max_freqs = []

    for i in range(N_CORES):
        base = f"/sys/devices/system/cpu/cpu{i}/cpufreq"
        try:
            with open(os.path.join(base, "scaling_cur_freq")) as f:
                cur = float(f.read().strip()) / 1e6  # kHz -> GHz
            with open(os.path.join(base, "cpuinfo_max_freq")) as f:
                maxf = float(f.read().strip()) / 1e6
        except Exception:
            fi = psutil.cpu_freq(percpu=True)[i]
            cur = fi.current / 1000.0
            maxf = fi.max / 1000.0 if fi.max else cur

        freqs.append(cur)
        max_freqs.append(maxf)

    return freqs, max_freqs
