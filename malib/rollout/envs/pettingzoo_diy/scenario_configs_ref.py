# MIT License

# Copyright (c) 2021 MARL @ SJTU

# Author: Ming Zhou

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

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