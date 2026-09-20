import logging
logger = logging.getLogger(__name__)

import os
import json

BASE = os.path.dirname(os.path.abspath(__file__))
MEMORY_PATH = os.path.join(BASE, "geo_memory.json")


def load_memory():
    if os.path.exists(MEMORY_PATH):
        try:
            with open(MEMORY_PATH) as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_memory(memory):
    try:
        with open(MEMORY_PATH, "w") as f:
            json.dump(memory, f)
    except Exception as e:
        logger.warning(f"Warning: could not save geo_memory: {e}")


def update_memory(lat, lon, spread_velocity):
    memory = load_memory()
    key = f"{round(lat, 2)}_{round(lon, 2)}"
    if key not in memory:
        memory[key] = []
    memory[key].append(float(spread_velocity))
    if len(memory[key]) > 20:
        memory[key] = memory[key][-20:]
    save_memory(memory)


def compute_momentum(lat, lon):
    memory = load_memory()
    key = f"{round(lat, 2)}_{round(lon, 2)}"
    values = memory.get(key, [])
    if len(values) < 2:
        return 0.0
    recent = values[-1]
    older = values[-2]
    return float(round(recent - older, 4))
