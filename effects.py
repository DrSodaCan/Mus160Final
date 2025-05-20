from pedalboard import Pedalboard, Reverb, Delay, Chorus, Phaser, PitchShift, Gain, Distortion, Limiter, Compressor

# Define available effects and their parameter configurations
EFFECTS = {
    "None": {
        "class": None,
        "params": []
    },
    "Reverb": {
        "class": Reverb,
        "params": [
            {"name": "room_size", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
            {"name": "damping", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
            {"name": "width", "type": "float", "min": 0.0, "max": 1.0, "default": 1.0},
        ]
    },
    "Delay": {
        "class": Delay,
        "params": [
            {"name": "delay_seconds", "type": "float", "min": 0.001, "max": 2.0, "default": 0.5},
            {"name": "feedback", "type": "float", "min": 0.0, "max": 0.95, "default": 0.3},
            {"name": "mix", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        ]
    },
    "Chorus": {
        "class": Chorus,
        "params": [
            {"name": "rate_hz", "type": "float", "min": 0.1, "max": 5.0, "default": 1.5},
            {"name": "depth", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5}
        ]
    },
    "Phaser": {
        "class": Phaser,
        "params": [
            {"name": "rate_hz", "type": "float", "min": 0.1, "max": 5.0, "default": 0.5},
            {"name": "depth", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5}
        ]
    },
    "Gain": {
        "class": Gain,
        "params": [
            {"name": "gain_db", "type": "float", "min": -24.0, "max": 24.0, "default": 0.0}
        ]
    },
    "Distortion": {
        "class": Distortion,
        "params": [
            {"name": "drive_db", "type": "float", "min": 0.0, "max": 60.0, "default": 0.0}
        ]
    },
    "Compressor": {
        "class": Compressor,
        "params": [
            {"name": "threshold_db", "type": "float", "min": -60.0, "max": 0.0, "default": -24.0},
            {"name": "ratio", "type": "float", "min": 1.0, "max": 20.0, "default": 4.0}
        ]
    }
}

def get_available_effects():
    """
    Return a list of effect names for populating UI dropdowns.
    """
    return list(EFFECTS.keys())


def get_param_configs(effect_name):
    """
    Return the parameter configuration list for a given effect.
    Each entry contains: name, type, min, max, default.
    """
    return EFFECTS.get(effect_name, {}).get("params", [])


def create_pedalboard(effect_name, **kwargs):
    """
    Construct a Pedalboard instance for the given effect and parameter values.
    """
    eff = EFFECTS.get(effect_name)
    # No effect or "None"
    if not eff or eff["class"] is None:
        return Pedalboard([])

    cls = eff["class"]
    # Build parameter dict, using defaults where not provided
    params = {}
    for cfg in eff["params"]:
        param_name = cfg["name"]
        params[param_name] = kwargs.get(param_name, cfg["default"])

    return Pedalboard([cls(**params)])
