import psutil
import os
import glob
import json
from pathlib import Path

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


def get_base_freqs():
    """Return base (TDP-rated sustainable) frequencies in GHz for each logical core.
    
    Falls back to cpuinfo_max_freq if base_frequency is unavailable.
    """
    base_freqs = []

    for i in range(N_CORES):
        cpufreq_base = f"/sys/devices/system/cpu/cpu{i}/cpufreq"
        try:
            # Try base_frequency first (available on Intel/AMD modern CPUs)
            base_path = os.path.join(cpufreq_base, "base_frequency")
            with open(base_path) as f:
                base = float(f.read().strip()) / 1e6  # kHz -> GHz
        except Exception:
            try:
                # Fallback to cpuinfo_max_freq if base_frequency unavailable
                with open(os.path.join(cpufreq_base, "cpuinfo_max_freq")) as f:
                    base = float(f.read().strip()) / 1e6
            except Exception:
                # Final fallback to psutil
                fi = psutil.cpu_freq(percpu=True)[i]
                base = fi.max / 1000.0 if fi.max else fi.current / 1000.0

        base_freqs.append(base)

    return base_freqs


def get_cpu_limits():
    """Return (scaling_max_freqs, hw_max_freqs) in GHz for each logical core.

    scaling_max_freqs reflects the current policy cap (what the core is allowed
    to run at), while hw_max_freqs reflects the hardware max frequency.
    """
    scaling_max_freqs = []
    hw_max_freqs = []

    for i in range(N_CORES):
        base = f"/sys/devices/system/cpu/cpu{i}/cpufreq"
        try:
            with open(os.path.join(base, "scaling_max_freq")) as f:
                scaling_max = float(f.read().strip()) / 1e6  # kHz -> GHz
            with open(os.path.join(base, "cpuinfo_max_freq")) as f:
                hw_max = float(f.read().strip()) / 1e6
        except Exception:
            fi = psutil.cpu_freq(percpu=True)[i]
            fallback = fi.max / 1000.0 if fi.max else fi.current / 1000.0
            scaling_max = fallback
            hw_max = fallback

        scaling_max_freqs.append(scaling_max)
        hw_max_freqs.append(hw_max)

    return scaling_max_freqs, hw_max_freqs


def get_cpu_temperature_c():
    """Return a best-effort CPU temperature in Celsius, or None."""
    try:
        temps = psutil.sensors_temperatures(fahrenheit=False)
    except Exception:
        return None

    if not temps:
        return None

    cpu_entries = []
    fallback_entries = []
    for name, entries in temps.items():
        name_l = name.lower()
        for e in entries:
            if e.current is None:
                continue
            fallback_entries.append(e.current)
            label = (e.label or "").lower()
            if "cpu" in name_l or "core" in name_l or "package" in label:
                cpu_entries.append(e.current)

    if cpu_entries:
        return max(cpu_entries)
    if fallback_entries:
        return max(fallback_entries)
    return None


def get_fan_rpm():
    """Return a best-effort fan speed in RPM, or None."""
    preferred = []
    fallback = []

    try:
        fans = psutil.sensors_fans()
    except Exception:
        fans = {}

    for source, entries in (fans or {}).items():
        source_l = source.lower()
        for e in entries:
            if e.current is None:
                continue
            rpm = float(e.current)
            if rpm <= 0:
                continue
            if "acpi" in source_l:
                fallback.append(rpm)
            else:
                preferred.append(rpm)

    # Fallback to sysfs in case psutil only exposes dummy ACPI values.
    for fan_path in glob.glob("/sys/class/hwmon/hwmon*/fan*_input"):
        hwmon_dir = os.path.dirname(fan_path)
        name_path = os.path.join(hwmon_dir, "name")
        try:
            with open(name_path) as f:
                hwmon_name = f.read().strip().lower()
        except Exception:
            hwmon_name = ""

        try:
            with open(fan_path) as f:
                rpm = float(f.read().strip())
        except Exception:
            continue

        if rpm <= 0:
            continue
        if "acpi" in hwmon_name:
            fallback.append(rpm)
        else:
            preferred.append(rpm)

    if preferred:
        return max(preferred)
    if fallback:
        return max(fallback)
    return None


def get_ram_utilization_percent():
    """Return RAM utilization percentage."""
    return psutil.virtual_memory().percent


# =========================
# Learned max frequency persistence
# =========================
_APP_DATA_DIR = Path.home() / ".local" / "share" / "cpu_monitor"
_LEARNED_MAX_FILE = _APP_DATA_DIR / "learned_max_freq.json"


def load_learned_max_freq():
    """Load the learned max frequency high water mark from disk. Returns float or None."""
    try:
        with open(_LEARNED_MAX_FILE) as f:
            data = json.load(f)
        value = float(data["high_water_mark"])
        if value > 0:
            return value
    except Exception:
        pass
    return None


def save_learned_max_freq(value):
    """Atomically save the learned max frequency high water mark to disk."""
    try:
        _APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
        tmp = _LEARNED_MAX_FILE.with_suffix(".tmp")
        with open(tmp, "w") as f:
            json.dump({"high_water_mark": value}, f)
        tmp.replace(_LEARNED_MAX_FILE)
    except Exception:
        pass
