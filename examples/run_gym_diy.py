from argparse import ArgumentParser

import os
import time

from malib.runner import run
from malib.agent import IndependentAgent
from malib.scenarios.marl_scenario import MARLScenario
from malib.rl.dqn import DQNPolicy, DQNTrainer, DEFAULT_CONFIG
# Import your custom environment's env_desc_gen and scenario configurations
from malib.rollout.envs.pettingzoo_diy import env_desc_gen, SCENARIO_CONFIGS

if __name__ == "__main__":
    parser = ArgumentParser("Multi-agent reinforcement learning for custom PettingZoo environments.")
    parser.add_argument("--log-dir", default="./logs/", help="Log directory.")
    parser.add_argument("--env-id", default="simcity.base_v0", help="Custom environment id.")
    parser.add_argument("--use-cuda", action="store_true")

    args = parser.parse_args()

    trainer_config = DEFAULT_CONFIG["training_config"].copy()
    trainer_config["total_timesteps"] = int(12)  # Increase timesteps as needed
    trainer_config["use_cuda"] = args.use_cuda

    training_config = {
        "type": IndependentAgent,
        "trainer_config": trainer_config,
        "custom_config": {},
    }
    rollout_config = {
        "fragment_length": 2000,  # Determine the size of sent data block
        "max_step": 10,  # Adjust based on your environment's episode length
        "num_eval_episodes": 10,
        "num_threads": 2,
        "num_env_per_thread": 10,
        "num_eval_threads": 1,
        "use_subproc_env": False,
        "batch_mode": "time_step",
        "postprocessor_types": ["defaults"],
        # Every # rollout epoch run evaluation.
        "eval_interval": 5,
        "inference_server": "ray",  # Options: `local`, `pipe`, `ray`
    }
    agent_mapping_func = lambda agent: agent

    algorithms = {
        "default": (
            DQNPolicy,
            DQNTrainer,
            # Model configuration, None for default
            {},
            {"use_cuda": args.use_cuda},
        )
    }

    # Use your custom environment's description generator
    env_description = env_desc_gen(env_id=args.env_id, scenario_configs=SCENARIO_CONFIGS.get(args.env_id, {}))
    runtime_logdir = os.path.join(args.log_dir, f"custom_env/{time.time()}")

    if not os.path.exists(runtime_logdir):
        os.makedirs(runtime_logdir)

    scenario = MARLScenario(
        name="custom_pettingzoo",
        log_dir=runtime_logdir,
        algorithms=algorithms,
        env_description=env_description,
        training_config=training_config,
        rollout_config=rollout_config,
        agent_mapping_func=agent_mapping_func,
        stopping_conditions={
            "training": {"max_iteration": int(10)},  # Adjust iterations as needed
            "rollout": {"max_iteration": int(100), "minimum_reward_improvement": 1.0},
        },
    )

    run(scenario)
