# CPU Monitor

![alt text](screenshot.png)

A real-time CPU monitoring desktop application built with PyQt6 and pyqtgraph. It displays a stacked area chart of **effective CPU throughput** (utilization × frequency) for every logical core, along with per-core stats and system totals.

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue) ![Platform: Linux](https://img.shields.io/badge/platform-Linux-lightgrey)

## Features

- **Stacked area chart** — each logical core is a distinct color band showing its effective GHz contribution over time.
- **Total frequency line** — white dashed line overlaying the chart shows aggregate clock speed.
- **Per-core legend** — live utilization percentage and current frequency for every core, reflowed into columns to fit the window width.
- **System totals** — overall CPU utilization, effective utilization, and aggregate frequency vs. maximum.
- **Dark theme** — comfortable for extended monitoring sessions.
- **Extensible panel architecture** — subclass `BasePanel` to add new monitoring panels (temperature, fan speed, etc.).

## Requirements

- Python 3.10+
- Linux (reads per-core frequencies from `/sys/devices/system/cpu/`)

## Installation

```bash
git clone <repo-url>
cd cpu_usage
pip install -r requirements.txt
```

## Usage

```bash
python cpu_util.py
```

The window opens at 1100×700 and updates every 500 ms by default. Tunable constants live in [helpers.py](helpers.py):

| Constant   | Default | Description                        |
|------------|---------|------------------------------------|
| `HISTORY`  | 100     | Number of samples visible on chart |
| `INTERVAL` | 500     | Milliseconds between updates       |

## Project Structure

```
cpu_util.py   — Application entry point and main window
helpers.py    — Configuration constants and system data collection
panels.py     — BasePanel class and CpuThroughputPanel implementation
```

## License

MIT