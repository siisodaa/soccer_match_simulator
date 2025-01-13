import math
import random
import os
import csv
defense = ["LCB", "RCB", "RB", "LB"]
midfield = ["LCM", "RCM", "CAM", "CDM"]
offense = ["LW", "RW", "ST"]


goal_position_teamA = [100,50]
goal_position_teamB = [0,50]

import csv
import os

def write_actions_to_csv(self, actions, priority_actions):

    filepath = "actions.csv"

    fileexists = os.path.isfile(filepath)

    headers = ["Player Role", "Player Position", "Actions", "Prioratized Actions"]

    with open(filepath, 'a', newline='') as file:

        writer = csv.writer(file)

    
        if not fileexists:
            writer.writerow(headers)
        

        writer.writerow([self.player_pos, self.player_coordinates, actions, priority_actions])

def write_to_csv(player, state, action, reward, new_q):
    filepath = "state.csv"  # Define the CSV file path
    fileexists = os.path.isfile(filepath)  # Check if the file already exists

    headers = ["Player Name", "Player Position", "Player Team", "Player Group", "Has Ball", "Action", "Reward", "Closest Open Space", "Q Value"]

    with open(filepath, "a", newline="") as file:  # Use newline="" to prevent extra blank lines in the file
        writer = csv.writer(file)
        
        # Write headers only if the file does not exist
        if not fileexists:
            writer.writerow(headers)
        
        # Extract player details and state information
        player_name = player.player_name
        closest_open_spaces, player_team, player_group, has_ball, player_position, closest_teammate_coordinates,closest_teammate_object, number_of_opponents_nearby = state

        # Write the row with the player's data
        writer.writerow([
            player_name, player_position, player.player_team, player_group, has_ball, action, reward, closest_open_spaces, new_q
        ])


def scan_field_with_ball(self, defending_team, attacking_team):
    
    teammates = [player for player in attacking_team if player != self]
    player_position = self.player_coordinates
    player_role = self.player_group
    has_ball = self.has_ball
    player_team = self.player_team
    open_teammates = [teammate for teammate in teammates if is_marked(teammate.player_coordinates, defending_team) == False]

    # For every open player, check their pass recieving possibility and goal scoring possibility

    teammates_info = teammate_probabilities(open_teammates, defending_team, attacking_team)

    self.field_data = teammates_info

    if open_teammates is None:
        closest_teammate_coordinates = None
        closest_teammate_object = None
    else:
        closest_teammate_coordinates, closest_teammate_object = get_closest_open_teammate(self, open_teammates)

    number_of_opponents_nearby = len(opponents_nearby(self, defending_team))

    closest_open_spaces = get_open_space(self, defending_team)


    return (closest_open_spaces, player_team, player_role, has_ball, player_position, closest_teammate_coordinates,closest_teammate_object, number_of_opponents_nearby)

def scan_field_without_ball(self, defending_team, attacking_team):
    
    teammates = self.teammates
    player_position = self.player_coordinates
    player_role = self.player_group
    has_ball = self.has_ball
    player_team = self.player_team
    player_with_ball = next(player for player in attacking_team if player.has_ball)

    is_current_player_closest_to_player_with_ball = math.dist(player_with_ball.player_coordinates, self.player_coordinates) < 5


    number_of_opponents_nearby = len(opponents_nearby(self, defending_team))

    closest_open_spaces = get_open_space(self, defending_team)


    return (is_current_player_closest_to_player_with_ball,player_with_ball,  closest_open_spaces, player_team, player_role, has_ball, player_position, number_of_opponents_nearby)



def teammate_probabilities(open_teammates, defending_team, attacking_team):

    teammate_info = {}
    for teammate in open_teammates:

        scoring_probability = get_scoring_probability(teammate, defending_team)
        recieving_pass_probability = get_receiving_pass_prob(teammate, defending_team)
        teammate_info[teammate] = [scoring_probability, recieving_pass_probability]
    

    return teammate_info


def get_distance(point1, point2):
    """Calculate the Euclidean distance between two points."""
    return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

def get_scoring_probability(teammate, defending_team):

    goal_position = goal_position_teamA if teammate.player_team == "A" else goal_position_teamB
    max_distance_to_goal = 120  # Maximum distance considered for scoring probability
    distance_to_goal = get_distance(teammate.player_coordinates, goal_position)
    
    # Normalize distance to range [0, 1]
    distance_factor = max(0, 1 - (distance_to_goal / max_distance_to_goal))
    
    # Consider defenders' proximity
    defender_proximity_penalty = 0
    for defender in defending_team:
        distance_to_defender = get_distance(teammate.player_coordinates, defender.player_coordinates)
        defender_proximity_penalty += max(0, 1 - (distance_to_defender / 10))  # 20 is a threshold
    
    defender_penalty_factor = max(0, 1 - (defender_proximity_penalty / len(defending_team)))
    
    # Combine factors
    scoring_probability = distance_factor * defender_penalty_factor

    return round(scoring_probability, 2)

def get_receiving_pass_prob(teammate, defending_team):

    max_proximity_threshold = 10 
    defender_proximity_penalty = 0
    
    for defender in defending_team:
        distance_to_defender = get_distance(teammate.player_coordinates, defender.player_coordinates)
        if distance_to_defender < max_proximity_threshold:
            defender_proximity_penalty += max(0, 1 - (distance_to_defender / max_proximity_threshold))
    
    defender_penalty_factor = max(0, 1 - (defender_proximity_penalty / len(defending_team)))
    
    # Assume static factors like teammate's positioning or skills
    positioning_factor = 0.8  # Higher value for better-positioned teammates
    receiving_pass_probability = positioning_factor * defender_penalty_factor
    return round(receiving_pass_probability, 2)

def get_open_space(player, defending_team):

    open_space_threshold = 3
    pos_x, pos_y = int(player.player_coordinates[0]), int(player.player_coordinates[1])
    open_spaces = []

    for x in range(pos_x - 5, pos_x + 6):
        for y in range(pos_y - 5, pos_y + 6):
            if is_within_bounds(x, y) and all(
                math.dist((x, y), opponent.player_coordinates) > open_space_threshold for opponent in defending_team
            ):
                open_spaces.append((x, y))


    return min(open_spaces)

def is_within_bounds(x, y, min_x=0, max_x=100, min_y=0, max_y=100):
    """
    Checks if the given coordinates (x, y) are within the specified bounds.
    
    Parameters:
    - x, y: int - Coordinates to check.
    - min_x, max_x, min_y, max_y: int - Boundaries of the field (default is (0,0) to (100,100)).
    
    Returns:
    - bool - True if within bounds, False otherwise.
    """
    return min_x <= x <= max_x and min_y <= y <= max_y
def is_marked(coord, defending_team):

    for opponent in defending_team:

        if math.dist(coord, opponent.player_coordinates) < 2:
            return True
    
    return False

def get_closest_open_teammate(self, open_teammates):

    min_distance = float('inf')
    closest_teammate = None
    for teammate in open_teammates:
        current_distance = math.dist(self.player_coordinates, teammate.player_coordinates)
        if current_distance < min_distance:
            closest_teammate = (teammate.player_coordinates, teammate)
    

    return closest_teammate


def opponents_nearby(self, defending_team):

    opponents_nearby = []
    for opponent in defending_team:
        
        if is_opponent_in_2_by_2(self, opponent):
            opponents_nearby.append(opponent)
    

    return opponents_nearby


def make_hashable(data):
    """Recursively converts unhashable types (e.g., dict, list) into hashable types (e.g., tuple)."""
    if isinstance(data, dict):
        return tuple(sorted((key, make_hashable(value)) for key, value in data.items()))
    elif isinstance(data, list):
        return tuple(make_hashable(item) for item in data)
    elif isinstance(data, set):
        return tuple(sorted(make_hashable(item) for item in data))
    else:
        return data

def get_role_prioritized_actions(state):
    """Return prioritized actions based on role and ball possession."""

    closest_open_spaces, player_team, player_role, has_ball, player_position, closest_teammate_coordinates,closest_teammate_object, number_of_opponents_nearby = state

    
    # Role-specific prioritization
    role_priorities = {
    "Defender": {
        "has_ball": ["pass", "moveWithBall"],  # "clear_ball" is not implemented
        "no_ball": ["maintain_line"]  # "tackle" is not implemented
    },
    "Midfielder": {
        "has_ball": ["pass", "move_to_open_space", "shoot"],  # "shoot" is implemented, "move_to_open_space" is related to "move" 
        "no_ball": ["supportPlayerWithBall", "move_to_open_space", "maintain_line"]  # "move_to_open_space" is related to "move"
    },
    "Forward": {
        "has_ball": ["shoot", "moveWithBall", "pass"],  # "shoot" and "moveWithBall" are implemented
        "no_ball": ["move_to_open_space", "supportPlayerWithBall"]  # "move_to_open_space" is related to "move"
    },
    "GK": {
        "has_ball": ["clear_ball"],  # "distribute_ball" is not implemented
        "no_ball": ["saveBall", "organize_defense"]  # These are implemented
    }
}


    # Default actions for undefined roles
    default_actions = {
        "has_ball": ["pass", "moveWithBall"],
        "no_ball": ["maintain_line", "supportPlayerWithBall"]
    }

    actions = role_priorities.get(player_role, default_actions)
    return actions["has_ball"] if has_ball else actions["no_ball"]

def get_role_prioritized_actions_without_ball(state):
    """Return prioritized actions based on role and ball possession."""

    is_current_player_closest_to_player_with_ball,player_with_ball, closest_open_spaces, player_team, player_role, has_ball, player_position, number_of_opponents_nearby = state

    
    # Role-specific prioritization
    # Role-specific prioritization
    role_priorities = {
    "Defender": {
        "has_ball": ["pass", "moveWithBall"],  # "clear_ball" is not implemented
        "no_ball": ["maintain_line"]  # "tackle" is not implemented
    },
    "Midfielder": {
        "has_ball": ["pass", "move_to_open_space", "shoot"],  # "shoot" is implemented, "move_to_open_space" is related to "move" 
        "no_ball": ["supportPlayerWithBall", "move_to_open_space", "maintain_line"]  # "move_to_open_space" is related to "move"
    },
    "Forward": {
        "has_ball": ["shoot", "moveWithBall", "pass"],  # "shoot" and "moveWithBall" are implemented
        "no_ball": ["move_to_open_space", "supportPlayerWithBall"]  # "move_to_open_space" is related to "move"
    },
    "GK": {
        "has_ball": ["clear_ball"],  # "distribute_ball" is not implemented
        "no_ball": ["saveBall", "organize_defense"]  # These are implemented
    }
}

    # Default actions for undefined roles
    default_actions = {
        "has_ball": ["pass", "moveWithBall"],
        "no_ball": ["maintain_line", "supportPlayerWithBall"]
    }

    actions = role_priorities.get(player_role, default_actions)
    return actions["has_ball"] if has_ball else actions["no_ball"]


def apply_field_awareness_with_ball(state, actions):
        
        closest_open_spaces, player_team, role, has_ball, player_pos, closest_teammate_coordinates,closest_teammate_object, number_of_opponents_nearby = state
        """Refine action prioritization based on field awareness."""
        refined_actions = actions.copy()
        ball_pos = player_pos
        goal_pos = goal_position_teamA if player_team == "A" else goal_position_teamB

        # Teammate Positioning: Prefer passing if a teammate is unmarked and close
        if "pass" in refined_actions:

            if closest_teammate_coordinates:

                distance = math.dist(player_pos, closest_teammate_coordinates)
                refined_actions.insert(0, "pass")
            
            else:
                refined_actions.remove("pass")

        # Opponent Proximity: Avoid risky actions under pressure
        if "moveWithBall" in refined_actions:
            if number_of_opponents_nearby > 1:  # High pressure threshold
                refined_actions.remove("moveWithBall")

            elif not closest_open_spaces:
                refined_actions.remove("moveWithBall")

        # Goal Proximity: Encourage shooting if close to the goal
        if "shoot" in refined_actions:
            distance_to_goal = math.dist(player_pos, goal_pos)
            if distance_to_goal < 18:  # Optimal shooting range
                refined_actions.insert(0, "shoot")

        return refined_actions

def apply_field_awareness_without_ball(state, actions):
        
        is_current_player_closest_to_player_with_ball,player_with_ball,  closest_open_spaces, player_team, player_role, has_ball, player_position, number_of_opponents_nearby = state
        """Refine action prioritization based on field awareness."""
        refined_actions = actions.copy()
        ball_pos = player_with_ball
        goal_pos = goal_position_teamA if player_team == "A" else goal_position_teamB

        
        

        return refined_actions

def get_belonging_group(player):


    if player.player_pos in defense:
        return "Defender"
    elif player.player_pos in midfield:
        return "Midfielder"
    elif player.player_pos in offense:
        return "Forward"
    else:
        return "GK"


def is_opponent_in_2_by_2(self, opponent):
    # Get the player's current position
    x, y = self.player_coordinates

    # Get the opponent's position
    opponent_x, opponent_y = opponent.player_coordinates

    # Check if the opponent's position falls within the 2x2 square
    if x - 1 <= opponent_x <= x and y - 1 <= opponent_y <= y:
        return True
    return False


def get_zones(player_pos, player_team):
    # [(x_min, y_min), (x_max, y_max)]
    zones = {
    "LCB": ((0, 20), (40, 40)),
    "RCB": ((0, 40), (40, 60)),
    "LB": ((0, 0), (60, 20)),
    "RB": ((0, 60), (60, 80)),
    "CM": ((40, 20), (100, 60)),
    "LCM": ((40, 20), (100, 60)),
    "RCM": ((40, 20), (100, 60)),
    "CDM": ((40, 20), (100, 60)),
    "CAM": ((40, 20), (100, 60)),
    "LW": ((40, 0), (120, 30)),
    "RW": ((40, 50), (120, 80)),
    "ST": ((80, 20), (120, 60))          # Striker
}

    return zones[player_pos]


def is_within_zone(self, coordinates):
        """Checks if the given coordinates are within the player's assigned zone."""
        x, y = coordinates
        (x_min, y_min), (x_max, y_max) = self.zone

        return x_min <= x <= x_max and y_min <= y <= y_max

def get_closest_zone_point(self, player_current_Pos, zone):
        # Unpack points
        x_tr, y_tr = zone[1]
        x_bl, y_bl = zone[0]

        # Compute corners
        top_left = (x_bl, y_tr)
        top_right = (x_tr, y_tr)
        bottom_left = (x_bl, y_bl)
        bottom_right = (x_tr, y_bl)

        # Points along top side (top_left to top_right)
        top_side = [(x, y_tr) for x in range(x_bl, x_tr + 1)]

        # Points along bottom side (bottom_left to bottom_right)
        bottom_side = [(x, y_bl) for x in range(x_bl, x_tr + 1)]

        # Points along left side (bottom_left to top_left)
        left_side = [(x_bl, y) for y in range(y_bl, y_tr + 1)]

        # Points along right side (bottom_right to top_right)
        right_side = [(x_tr, y) for y in range(y_bl, y_tr + 1)]

        # Combine all points along the sides
        all_side_points = top_side + bottom_side + left_side + right_side

        # Player's current position
        player_x, player_y = player_current_Pos

        # Find the closest point in all_side_points
        closest_point = min(
            all_side_points,
            key=lambda point: (point[0] - player_x) ** 2 + (point[1] - player_y) ** 2
        )

        return closest_point

