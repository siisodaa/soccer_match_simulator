import asyncio
import random
import math
from utilities import(is_within_zone, get_closest_zone_point)
import numpy as np
import csv

goal_position_teamA = [100,40]
goal_position_teamB = [0,40]


async def shoot_goal(self, ball, game):
    # Determine the target goal and goalpost range based on the player's team
    if self.player_team == "A":
        goal_position = goal_position_teamB  # Shooting at Team B's goal
        goal_post_min = goal_position[1] - 4
        goal_post_max = goal_position[1] + 4
    else:
        goal_position = goal_position_teamA  # Shooting at Team A's goal
        goal_post_min = goal_position[1] - 4
        goal_post_max = goal_position[1] + 4

    # Randomly select a target point within the goalposts
    target_y = random.uniform(goal_post_min, goal_post_max)
    target_x = goal_position[0]
    target_coordinates = (target_x, target_y)

    # Simulate the ball moving towards the goal
    await ball.shot_move(target_coordinates, game)

    # Calculate the shot outcome (miss or goal)
    shot_distance = math.dist(self.player_coordinates, goal_position)
    reward = 5  # Base reward for attempting a shot
    shot_success_chance = max(0.2, min(0.9, 30 / shot_distance))  # Success probability scales with distance

    # Penalize long-distance shots
    distance_penalty = max(0, (shot_distance - 20) * 0.1)  # Penalize shots more as distance increases
    reward -= distance_penalty

    # Calculate the shot result (goal or miss)
    if random.random() < shot_success_chance:
        print(f"Goal! {self.player_name} scored!")
        reward += 15  # Bonus reward for scoring
        game.stop()  # Stop game after a goal
    else:
        print(f"Missed shot by {self.player_name}.")
        reward -= 5  # Penalty for missing

    # Prepare data to write to CSV
    player_data = {
        'player': self.player_name,
        'player_team': self.player_team,
        'distance_from_goal': shot_distance,
        'reward': reward,
        'target_coordinates': target_coordinates
    }

    # Write to CSV
    file_name = "shots_data.csv"
    file_exists = False

    try:
        # Check if file exists to append or write header
        with open(file_name, mode='r', newline='') as f:
            file_exists = True
    except FileNotFoundError:
        file_exists = False

    # Append data to CSV
    with open(file_name, mode='a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=player_data.keys())
        if not file_exists:
            writer.writeheader()  # Write header only if file is new
        writer.writerow(player_data)

    print(f"Shot details saved to {file_name}")
    print(target_coordinates)
    return reward


async def pass_ball(self, team, ball, game, state, direction):
    closest_open_spaces, player_team, role, has_ball, player_pos, closest_teammate_coordinates, closest_teammate_object, number_of_opponents_nearby = state
    # Check if there is an open teammate who could score
    field_data = self.field_data
    # Extract state variables
    closest_open_spaces, player_team, role, has_ball, player_pos, closest_teammate_coordinates, closest_teammate_object, number_of_opponents_nearby = state
    ball_position = self.player_coordinates
    # Filter teammates ahead based on direction
    forward_teammates = {
        teammate: values for teammate, values in field_data.items()
        if direction * (teammate.player_coordinates[0] - self.player_coordinates[0]) > 0  # Adjust for direction
    }
    if not forward_teammates:
        # No forward teammates; fallback to the teammate with the highest pass receiving probability
        target_teammate, _ = max(field_data.items(), key=lambda item: item[1][1])  # Pass receiving prob
        if_forward_pass = False
    else:
        # Select forward teammate with highest scoring probability
        target_teammate, _ = max(forward_teammates.items(), key=lambda item: item[1][0])  # Scoring prob
        if_forward_pass = True

    # Target coordinates and open space condition
    target_coordinates = target_teammate.player_coordinates
    has_open_space = len(closest_open_spaces) > 0

    # Adjust penalties
    forward_pass_penalty = 1.5
    backward_pass_penalty = 0.5
    has_open_space_penalty = 0.5

    # Calculate the distance to the target teammate
    distance_to_target = math.dist(self.player_coordinates, target_coordinates)

    # Check for closer open teammates
    close_teammates = [
        teammate for teammate, values in field_data.items()
        if teammate != self and math.dist(self.player_coordinates, teammate.player_coordinates) < distance_to_target and values[1] > 0  # Ensure the teammate is open
    ]
    are_closer_teammates_open = len(close_teammates) > 0

    # Penalize if the target teammate is more than 20 units away and there are closer open teammates
    distance_penalty = 0
    if distance_to_target > 20 and are_closer_teammates_open:
        distance_penalty = 2  # Penalty for passing to a teammate too far away
    else:
        distance_penalty = 0  # No penalty if the target is close enough or there are no closer teammates

    # Set teammate to waiting for ball
    target_teammate.waiting_for_ball = True
    # Calculate base reward using ball movement
    base_reward = await ball.move(ball_position, target_coordinates, game, self, target_teammate)
    # Teammate no longer waiting for ball
    target_teammate.waiting_for_ball = False
    # Adjust reward based on conditions
    if if_forward_pass:
        reward = base_reward * forward_pass_penalty
    else:
        reward = base_reward * backward_pass_penalty

    if has_open_space:
        reward *= has_open_space_penalty

    # Apply distance penalty
    reward -= distance_penalty

    # Prepare data to write to CSV
    player_data = {
        'player_who_passed': self.player_name,
        'player_passed_to': target_teammate.player_name,
        'distance_between_players': distance_to_target,
        'are_closer_teammates_open': are_closer_teammates_open,
        'reward': reward
    }

    # Write to CSV
    file_name = "pass_data.csv"
    file_exists = False

    try:
        # Check if file exists to append or write header
        with open(file_name, mode='r', newline='') as f:
            file_exists = True
    except FileNotFoundError:
        file_exists = False

    # Append data to CSV
    with open(file_name, mode='a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=player_data.keys())
        if not file_exists:
            writer.writeheader()  # Write header only if file is new
        writer.writerow(player_data)

    print(f"Pass details saved to {file_name}")
    return reward


async def move(self, target):
    reward = 5
    player_pos_x, player_pos_y = self.player_coordinates
    target_x, target_y = target
    dx = target_x - player_pos_x
    dy = target_y - player_pos_y
    distance = math.dist(self.player_coordinates, target)

    # Use easing to smooth out the motion
    speed = max(0.1, min(distance / 5, 1))  # Speed decreases as the target is near

    # Normalize direction vector
    norm = np.linalg.norm([dx, dy])
    direction = (dx / norm, dy / norm) if norm != 0 else (0, 0)

    # Update player coordinates smoothly
    self.player_coordinates = (
        self.player_coordinates[0] + direction[0] * speed,
        self.player_coordinates[1] + direction[1] * speed,
    )

    if not is_within_zone(self, self.player_coordinates):
        zone = self.zone
        closest_zone_point = get_closest_zone_point(self, self.player_coordinates, zone)
        # await self.move(closest_zone_point, action)
        reward -= 5  # Penalize for being out of zone

    # Penalize clustering
    teammate_distances = [
        math.dist(self.player_coordinates, teammate.player_coordinates)
        for teammate in self.teammates if teammate != self
    ]
    if any(dist < 5 for dist in teammate_distances): 
        reward -= 5

    # Pause briefly to simulate asynchronous motion
    await asyncio.sleep(0.001)

    return reward

async def maintain_line(self, action):
    reward = 5  # Base reward for maintaining line

    if not is_within_zone(self, self.player_coordinates):
        zone = self.zone
        closest_zone_point = get_closest_zone_point(self, self.player_coordinates, zone)
        await self.move(closest_zone_point, action)
        reward -= 5  # Penalize for being out of zone

    # Penalize clustering
    teammate_distances = [
        math.dist(self.player_coordinates, teammate.player_coordinates)
        for teammate in self.teammates if teammate != self
    ]
    if any(dist < 5 for dist in teammate_distances): 
        reward -= 5


    return reward

async def cross_ball(self, target_zone, teammates, ball, game):
    reward = 5
    target = random.choice(teammates).player_coordinates
    ball_movement_reward = await ball.move(target)
    
    reward += ball_movement_reward

    # Reward teammates in better scoring positions
    if target[0] > self.player_coordinates[0] and math.dist(target, goal_position_teamA) < 20:
        reward += 10  # Reward for a good cross
    else:
        reward -= 2  # Penalize for ineffective cross

    return reward

async def support_player_with_ball(self, player_with_ball, game):
    reward = 5
    target = (
        player_with_ball[0] - 10,  # Adjust to maintain support distance
        player_with_ball[1] - 5
    )
    await self.move(target)

    return reward