from pettingzoo.utils import AECEnv, agent_selector
from gym import spaces
import numpy as np
from typing import Dict, Any, List, Tuple, Union
from malib.rollout.envs.env import Environment

class SimCityEnv(Environment, AECEnv):
    metadata = {"render.modes": ["human"]}

    def __init__(self, **configs):
        Environment.__init__(self, **configs)
        
        scenario_configs = configs.get("scenario_configs", {})
        self.grid_size = scenario_configs.get("grid_size", 4)
        self.num_players = scenario_configs.get("num_players", 3)
        
        # Initialize agents
        self._agents = [f"P{i+1}" for i in range(self.num_players)]
        self._possible_agents = self._agents[:]
        
        # Get game configs
        self.building_types = scenario_configs["building_types"]
        self.building_costs = scenario_configs["building_costs"]
        self.building_utilities = scenario_configs["building_utilities"]
        self.building_effects = scenario_configs["building_effects"]
        
        # Initialize spaces
        self._init_spaces()
        
        # Initialize agent selector
        self._agent_selector = agent_selector(self._agents)
        self.agent_selection = None
        
        # Initialize game state
        self.reset()

    @property
    def agents(self):
        return self._agents

    @property
    def possible_agents(self):
        return self._possible_agents

    @property
    def action_spaces(self):
        return self._action_spaces

    @property
    def observation_spaces(self):
        return self._observation_spaces

    def _init_spaces(self):
        self._action_spaces = {
            agent: spaces.Discrete(self.grid_size**2 * len(self.building_types))
            for agent in self._agents
        }
        
        # 只使用Box空间，不使用Dict空间
        total_obs_dim = (
            self.grid_size * self.grid_size * 3 +  # grid (G,V,D)
            2 +  # resources (money, reputation)
            self.grid_size * self.grid_size  # builders
        )
        
        self._observation_spaces = {
            agent: spaces.Box(
                low=-float('inf'),
                high=float('inf'),
                shape=(total_obs_dim,),
                dtype=np.float32
            ) for agent in self._agents
        }

    def reset(self, seed=None, options=None, max_step=None):
        if seed is not None:
            np.random.seed(seed)
            
        self.grid = np.full((self.grid_size, self.grid_size, 3), 30, dtype=np.int32)
        self.buildings = np.full((self.grid_size, self.grid_size), None)
        self.builders = np.full((self.grid_size, self.grid_size), -1, dtype=np.int32)
        
        # Initialize player states
        self.player_states = {
            agent: {
                "money": 20,
                "reputation": 20,
                "score": 0
            } for agent in self._agents
        }
        
        # Initialize PettingZoo required variables
        self._agent_selector = agent_selector(self._agents)
        self.agent_selection = self._agent_selector.reset()
        
        self.rewards = {agent: 0 for agent in self._agents}
        self.terminations = {agent: False for agent in self._agents}
        self.truncations = {agent: False for agent in self._agents}
        self.infos = {agent: {} for agent in self._agents}
        
        self.num_moves = 0
        
        observations = {agent: self._get_obs(agent) for agent in self._agents}
        return observations

    def step(self, action):
        if self.terminations[self.agent_selection] or self.truncations[self.agent_selection]:
            return self._was_dead_step(action)

        agent = self.agent_selection
        
        # Process action and update state
        reward = self._process_action(agent, action)
        
        # Update rewards
        self.rewards[agent] = reward
        
        # Check termination
        if self._is_game_over():
            self.terminations = {agent: True for agent in self._agents}
        
        # Update agent selection
        self.agent_selection = self._agent_selector.next()
        
        observations = {agent: self._get_obs(agent) for agent in self._agents}
        return observations, self.rewards, self.terminations, self.truncations, self.infos

    def _process_action(self, agent, action):
        building_type, x, y = self._decode_action(action)
        reward = 0
        
        if self.buildings[x][y] is not None:
            return -5  # Penalty for invalid move
            
        # Process building placement and calculate rewards
        cost = self.building_costs[building_type]
        if (self.player_states[agent]["money"] >= cost["money"] and 
            self.player_states[agent]["reputation"] >= cost["reputation"]):
            
            # Place building
            self.buildings[x][y] = building_type
            self.builders[x][y] = self._agents.index(agent)
            
            # Apply costs
            self.player_states[agent]["money"] -= cost["money"]
            self.player_states[agent]["reputation"] -= cost["reputation"]
            
            # Apply effects
            self._apply_building_effects(x, y, building_type)
            
            # Calculate reward
            utility = self.building_utilities[building_type]
            reward = utility["money"] + utility["reputation"]
            
        return reward

    def _decode_action(self, action):
        total_positions = self.grid_size ** 2
        building_type_idx = action // total_positions
        position_idx = action % total_positions
        
        building_type = self.building_types[building_type_idx]
        x = position_idx // self.grid_size
        y = position_idx % self.grid_size
        
        return building_type, x, y

    def _apply_building_effects(self, x, y, building_type):
        effects = self.building_effects[building_type]
        
        # Apply direct effects
        self.grid[x, y] += [effects["G"], effects["V"], effects["D"]]
        
        # Apply neighbor effects
        for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.grid_size and 0 <= ny < self.grid_size:
                self.grid[nx, ny] += [
                    effects["neighbors"]["G"],
                    effects["neighbors"]["V"],
                    effects["neighbors"]["D"]
                ]

    def _get_obs(self, agent):
        # 将所有观察数据扁平化为一维数组
        grid_flat = self.grid.reshape(-1).astype(np.float32)
        resources = np.array([
            self.player_states[agent]["money"],
            self.player_states[agent]["reputation"]
        ], dtype=np.float32)
        builders_flat = self.builders.reshape(-1).astype(np.float32)
        
        return np.concatenate([grid_flat, resources, builders_flat])

    def _is_game_over(self):
        return (np.all(self.buildings != None) or 
                np.mean(self.grid) < 10 or 
                self.num_moves >= self.grid_size**2)

    def render(self):
        # Implementation for rendering (if needed)
        pass

    def observe(self, agent):
        return self._get_obs(agent)

    def close(self):
        pass