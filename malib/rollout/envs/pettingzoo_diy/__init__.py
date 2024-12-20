#__init__.py

from .env import SimCityEnv
from .scenario_configs_ref import SCENARIO_CONFIGS

def env_desc_gen(**config):
    """
    Generate the environment description.

    Args:
        **config: Arbitrary keyword arguments for environment configuration.

    Returns:
        dict: Environment description containing creator, possible_agents, action_spaces, observation_spaces, and config.
    """
    env_id = config.get("env_id")
    assert env_id in SCENARIO_CONFIGS, f"Available env ids: {list(SCENARIO_CONFIGS.keys())}"

    # Merge default scenario configurations with any custom configurations provided
    if "scenario_configs" not in config:
        config["scenario_configs"] = SCENARIO_CONFIGS[env_id]
    else:
        scenario_config = SCENARIO_CONFIGS[env_id].copy()
        scenario_config.update(config["scenario_configs"])
        config["scenario_configs"] = scenario_config

    # Initialize the environment
    env = SimCityEnv(**config)
    
    # Create the environment description
    env_desc = {
        "creator": SimCityEnv,
        "possible_agents": env.possible_agents,
        "action_spaces": env.action_spaces,
        "observation_spaces": env.observation_spaces,
        "config": config,
    }

    # Close the environment as it's no longer needed after extracting the description
    env.close()

    return env_desc
