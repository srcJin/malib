SCENARIO_CONFIGS = {
    "simcity.base_v0": {
        "grid_size": 4,
        "num_players": 3,
        "parallel_simulate": False,
        "building_types": ["Park", "House", "Shop"],
        "building_costs": {
            "Park": {"money": 1, "reputation": 3},
            "House": {"money": 2, "reputation": 2}, 
            "Shop": {"money": 3, "reputation": 1}
        },
        "building_utilities": {
            "Park": {"money": -1, "reputation": 3},
            "House": {"money": 2, "reputation": 0},
            "Shop": {"money": 3, "reputation": -1}
        },
        "building_effects": {
            "Park": {"G": 30, "V": -30, "D": 0, "neighbors": {"G": 10, "V": -10, "D": 0}},
            "House": {"G": -30, "V": 0, "D": 30, "neighbors": {"G": -10, "V": 10, "D": 10}},
            "Shop": {"G": -30, "V": 30, "D": -30, "neighbors": {"G": -10, "V": 10, "D": -10}}
        }
    }
}
