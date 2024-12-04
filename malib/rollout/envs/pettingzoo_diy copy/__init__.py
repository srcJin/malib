#__init__.py

from .env import SimCityEnv
from .scenario_configs_ref import SCENARIO_CONFIGS

def env_desc_gen(**config):
    env_id = config["env_id"]
    assert env_id in SCENARIO_CONFIGS, f"available env ids: {SCENARIO_CONFIGS.keys()}"

    if "scenario_configs" not in config:
        config["scenario_configs"] = SCENARIO_CONFIGS[env_id]
    else:
        scenario_config = SCENARIO_CONFIGS[env_id].copy()
        scenario_config.update(config["scenario_configs"])
        config["scenario_configs"] = scenario_config

    env = SimCityEnv(**config)
    env_desc = {
        "creator": SimCityEnv,
        "possible_agents": env.possible_agents,
        "action_spaces": env.action_spaces,
        "observation_spaces": env.observation_spaces,
        "config": config,
    }

    env.close()

    return env_desc
