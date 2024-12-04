# pragma: no cover
from argparse import ArgumentParser

import os
import time

from malib.runner import run
from malib.agent import IndependentAgent
from malib.scenarios.psro_scenario import PSROScenario
from malib.rl.dqn import DQNPolicy, DQNTrainer, DEFAULT_CONFIG
# from malib.rollout.envs.open_spiel import env_desc_gen
# from malib.rollout.envs.pettingzoo import env_desc_gen

from malib.rollout.envs.pettingzoo_diy import env_desc_gen


if __name__ == "__main__":
    parser = ArgumentParser("PSRO for SimCity")
    parser.add_argument("--log_dir", default="./logs/", help="Log directory.")
    parser.add_argument(
        "--env_id", 
        default="simcity.base_v0",
        help="SimCity environment id"
    )

    args = parser.parse_args()
    trainer_config = DEFAULT_CONFIG["training_config"].copy()
    trainer_config["total_timesteps"] = int(10)

    training_config = {
        "type": IndependentAgent,
        "trainer_config": trainer_config,
        "custom_config": {},
    }
    rollout_config = {
        "fragment_length": 20,  # every thread
        "max_step": 100,
        "num_eval_episodes": 5,
        "num_threads": 4,
        "num_env_per_thread": 10,
        "num_eval_threads": 1,
        "use_subproc_env": False,
        "batch_mode": "time_step",
        "postprocessor_types": ["defaults"],
        # every # rollout epoch run evaluation.
        "eval_interval": 1,
        "inference_server": "ray",  # three kinds of inference server: `local`, `pipe` and `ray`
    }
    agent_mapping_func = lambda agent: agent

    algorithms = {
        "default": (
            DQNPolicy,
            DQNTrainer,
            # model configuration, None for default
            {},
            {},
        )
    }

    env_description = env_desc_gen(
        env_id=args.env_id,
        scenario_configs={
            "grid_size": 4,
            "num_players": 3
        }
    )
    
    runtime_logdir = os.path.join(args.log_dir, f"psro_{args.env_id}/{time.time()}")

    if not os.path.exists(runtime_logdir):
        os.makedirs(runtime_logdir)

    scenario = PSROScenario(
        name=f"psro_{args.env_id}",
        log_dir=runtime_logdir,
        algorithms=algorithms,
        env_description=env_description,
        training_config=training_config,
        rollout_config=rollout_config,
        # control the outer loop.
        global_stopping_conditions={"max_iteration": 100},  # set iterations
        agent_mapping_func=agent_mapping_func,
        # for the training of best response.
        stopping_conditions={
            "training": {"max_iteration": int(100)},
            "rollout": {"max_iteration": 10},
        },
    )

    run(scenario)
