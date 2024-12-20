from gym import spaces
import numpy as np
from typing import Dict, Any, List, Tuple, Union
from malib.rollout.envs.env import Environment
from pettingzoo.utils import agent_selector

class SimCityEnv(Environment):
    metadata = {"render.modes": ["human"]}

    def __init__(self, **configs):
        super(SimCityEnv, self).__init__(**configs)
        
        # Extract scenario configurations
        scenario_configs = configs.get("scenario_configs", {}).copy()
        self.grid_size = scenario_configs.get("grid_size", 4)
        self.num_players = scenario_configs.get("num_players", 3)
        
        # Initialize agents
        self._agents = [f"P{i+1}" for i in range(self.num_players)]
        self._possible_agents = self._agents[:]
        
        # Get game configurations
        self.building_types = scenario_configs["building_types"]
        self.building_costs = scenario_configs["building_costs"]
        self.building_utilities = scenario_configs["building_utilities"]
        self.building_effects = scenario_configs["building_effects"]
        
        # Initialize action and observation spaces
        self._init_spaces()
        
        # Initialize agent selector
        self._agent_selector = agent_selector(self._agents)
        self.agent_selection = None
        
        # Initialize game state
        self.reset()

    @property
    def agents(self) -> List[str]:
        return self._agents

    @property
    def possible_agents(self) -> List[str]:
        return self._possible_agents

    @property
    def action_spaces(self) -> Dict[str, spaces.Space]:
        return self._action_spaces

    @property
    def observation_spaces(self) -> Dict[str, spaces.Space]:
        return self._observation_spaces

    def _init_spaces(self):
        # Define action spaces for each agent
        self._action_spaces = {
            agent: spaces.Discrete(self.grid_size**2 * len(self.building_types))
            for agent in self._agents
        }
        
        # Define observation spaces for each agent
        total_obs_dim = (
            self.grid_size * self.grid_size * 3 +  # grid (G, V, D)
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

    def reset(self, seed: int = None, options: Dict[str, Any] = None, max_step: int = None) -> Tuple[Union[None, Dict[str, Any]], Dict[str, Any]]:
        """
        Reset the environment.

        Args:
            seed (int, optional): Seed for random number generator.
            options (dict, optional): Additional options.
            max_step (int, optional): Maximum number of steps per episode.

        Returns:
            Tuple containing:
                - None (state)
                - Observations dictionary
        """
        super(SimCityEnv, self).reset(max_step)
        
        if seed is not None:
            np.random.seed(seed)
        
        # Initialize grid and buildings
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
        
        # Initialize rewards, terminations, truncations, and infos
        self.rewards = {agent: 0 for agent in self._agents}
        self.terminations = {agent: False for agent in self._agents}
        self.truncations = {agent: False for agent in self._agents}
        self.infos = {agent: {} for agent in self._agents}
        
        # Initialize step counter
        self.num_moves = 0
        
        # Get initial observations
        observations = {agent: self._get_obs(agent) for agent in self._agents}
        return None, observations

    def step(self, action: Dict[str, Any]) -> Tuple[
        Union[None, Dict[str, Any]],
        Dict[str, Any],
        Dict[str, float],
        Dict[str, bool],
        Dict[str, Any],
    ]:
        """
        Perform a step in the environment.

        Args:
            action (dict): Actions taken by agents.

        Returns:
            Tuple containing:
                - None (state)
                - Observations dictionary
                - Rewards dictionary
                - Dones dictionary (combination of terminations and truncations)
                - Infos dictionary
        """
        if self.terminations[self.agent_selection] or self.truncations[self.agent_selection]:
            return self._was_dead_step(action)

        agent = self.agent_selection

        # Process action and update state
        reward = self._process_action(agent, action[agent])
        
        # Update rewards
        self.rewards[agent] = reward
        
        # Check termination conditions
        if self._is_game_over():
            self.terminations = {agent: True for agent in self._agents}
        
        # Update agent selection
        self.agent_selection = self._agent_selector.next()
        
        # Get new observations
        observations = {agent: self._get_obs(agent) for agent in self._agents}
        
        # Combine terminations and truncations into dones
        dones = {agent: self.terminations[agent] or self.truncations[agent] for agent in self._agents}
        dones["__all__"] = all(dones.values())
        
        return None, observations, self.rewards, dones, self.infos

    def _process_action(self, agent: str, action: int) -> float:
        """
        Process the action taken by an agent.

        Args:
            agent (str): The agent taking the action.
            action (int): The action to process.

        Returns:
            float: The reward obtained from the action.
        """
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

    def _decode_action(self, action: int) -> Tuple[str, int, int]:
        """
        Decode the action into building type and grid position.

        Args:
            action (int): The action to decode.

        Returns:
            Tuple containing building type, x-coordinate, and y-coordinate.
        """
        total_positions = self.grid_size ** 2
        building_type_idx = action // total_positions
        position_idx = action % total_positions
        
        building_type = self.building_types[building_type_idx]
        x = position_idx // self.grid_size
        y = position_idx % self.grid_size
        
        return building_type, x, y

    def _apply_building_effects(self, x: int, y: int, building_type: str):
        """
        Apply the effects of placing a building.

        Args:
            x (int): X-coordinate of the building.
            y (int): Y-coordinate of the building.
            building_type (str): Type of the building.
        """
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

    def _get_obs(self, agent: str) -> np.ndarray:
        """
        Get the observation for a specific agent.

        Args:
            agent (str): The agent to get the observation for.

        Returns:
            np.ndarray: The flattened observation array.
        """
        # Flatten all observation data into a one-dimensional array
        grid_flat = self.grid.reshape(-1).astype(np.float32)
        resources = np.array([
            self.player_states[agent]["money"],
            self.player_states[agent]["reputation"]
        ], dtype=np.float32)
        builders_flat = self.builders.reshape(-1).astype(np.float32)
        
        return np.concatenate([grid_flat, resources, builders_flat])

    def _is_game_over(self) -> bool:
        """
        Check if the game is over.

        Returns:
            bool: True if the game is over, False otherwise.
        """
        return (np.all(self.buildings != None) or 
                np.mean(self.grid) < 10 or 
                self.num_moves >= self.grid_size**2)

    def render(self, mode: str = "human"):
        """
        Render the environment.

        Args:
            mode (str): The mode to render with.

        Returns:
            Any: Rendered output based on the mode.
        """
        # Implementation for rendering (if needed)
        pass

    def observe(self, agent: str) -> np.ndarray:
        """
        Observe the environment for a specific agent.

        Args:
            agent (str): The agent to observe for.

        Returns:
            np.ndarray: The observation array.
        """
        return self._get_obs(agent)

    def close(self):
        """
        Close the environment.
        """
        pass

    def _was_dead_step(self, action: Dict[str, Any]) -> Tuple[
        Union[None, Dict[str, Any]],
        Dict[str, Any],
        Dict[str, float],
        Dict[str, bool],
        Dict[str, Any],
    ]:
        """
        Handle the step when an agent is dead.

        Args:
            action (dict): Actions taken by agents.

        Returns:
            Tuple containing:
                - None (state)
                - Observations dictionary
                - Rewards dictionary
                - Dones dictionary
                - Infos dictionary
        """
        observations = {agent: self._get_obs(agent) for agent in self._agents}
        dones = {agent: True for agent in self._agents}
        dones["__all__"] = True
        return None, observations, self.rewards, dones, self.infos