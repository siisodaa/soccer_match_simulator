from mesa import Agent, Model
import asyncio
import math
import get_players
from mplsoccer import Pitch
import matplotlib.pyplot as plt
import numpy as np
import random
import time
from utilities import(scan_field_with_ball, make_hashable, get_belonging_group, get_role_prioritized_actions, apply_field_awareness_with_ball, write_to_csv, write_actions_to_csv, get_zones, is_within_zone, get_closest_zone_point, scan_field_without_ball)
import matplotlib.patches as patches

role_priorities = {
        "Defender": {
            "has_ball": ["clear_ball", "pass", "moveWithBall"],
            "no_ball": ["maintain_line", "tackle", "intercept_pass"]
        },
        "Midfielder": {
            "has_ball": ["pass", "move_to_open_space", "shoot"],
            "no_ball": ["supportPlayerWithBall", "move_to_open_space", "maintain_line"]
        },
        "Forward": {
            "has_ball": ["shoot", "moveWithBall", "pass"],
            "no_ball": ["run_off_the_ball", "move_to_open_space", "supportPlayerWithBall"]
        },
        "GK": {
            "has_ball": ["distribute_ball", "clear_ball"],
            "no_ball": ["saveBall", "organize_defense"]
        }
    }

goal_position_teamA = [100,50]
goal_position_teamB = [0,50]
class Player(Agent):
    def __init__(self, unique_id, model, player_pos, player_coordinates, player_team):
        super().__init__(unique_id, model)
        self.player_name = unique_id
        self.player_pos = player_pos
        self.player_coordinates = player_coordinates
        self.player_team = player_team
        self.has_ball = False
        self.waiting_for_ball = False
        self.q_table = []
        self.field_data = None
        self.zone = [(0,0), (0,0)]
        self.teammates = []
        self.player_group = get_belonging_group(self)
    

        self.q_table = {}
        self.learning_rate = 0.1
        self.discount_factor = 0.9
        self.exploration_rate = 1
        self.exploration_decay = 0.995



        if player_team == "A" :
            self.zone = get_zones(self.player_pos, self.player_team)
        
    async def play(self, game, ball, attacking_team, defending_team, player_with_ball):

        if self.waiting_for_ball:
            return
        

        if self in attacking_team:

            await self.attack(attacking_team, defending_team, ball, game, player_with_ball)
        else:
            await self.defend(attacking_team, defending_team, ball, game, player_with_ball)
        

    ####### ATTACK CODE

    async def attack(self, attacking_team,defending_team, ball, game, player_with_ball):
        
        
        if self.has_ball and not self.waiting_for_ball :

            #  Evaluate the state of the game to decide what to do

            state = scan_field_with_ball(self, defending_team, attacking_team)
            
            action = self.choose_action_with_ball(state)

            # print(state)
            
            # print(f"For {self.player_name} , {self.player_team}  -->  {state}")

            reward = await self.execute_action(action, game, ball, attacking_team, defending_team, state)
                
            if reward is not None:
                next_state = scan_field_with_ball(self, defending_team, attacking_team)

                await self.update_q_value(state, action, reward, next_state)
            else:
                print(f"reward is none for {action}")
                return
        
        else:

            # #  Evaluate the state of the game to decide what to do

            # state = scan_field_without_ball(self, defending_team, attacking_team)
            
            # action = self.choose_action_without_ball(state)

            # # print(state)
            
            # # print(f"For {self.player_name} , {self.player_team}  -->  {state}")

            # reward = await self.execute_action(action, game, ball, attacking_team, defending_team, state)
                
            # if reward is not None:
            #     next_state = scan_field_without_ball(self, defending_team, attacking_team)

            #     await self.update_q_value(state, action, reward, next_state)
            # else:
            #     print(f"reward is none for {action}")
            #     return

            #  All other players move independently
            targets = [
                [50, 50], [0, 90], [60, 100], [40, 30], [20, 30], [21, 75], [5, 95], [9, 89], [56, 23], [92, 23],
                [10, 10], [70, 70], [25, 85], [45, 15], [15, 40], [35, 55], [65, 10], [85, 25], [30, 70], [80, 40],
                [55, 60], [5, 10]
            ]
            target = random.choice(targets)
            await self.move(target)
            
    
        
        # # If this player has the ball, pass it
        # if self.has_ball and not self.waiting_for_ball :
        #     teammate = self.pick_a_teammate(attacking_team, game)
        #     await self.pass_ball(teammate, ball, game) 
        # else:
        #     # All other players move independently
        #     targets = [
        #         [50, 50], [0, 90], [60, 100], [40, 30], [20, 30], [21, 75], [5, 95], [9, 89], [56, 23], [92, 23],
        #         [10, 10], [70, 70], [25, 85], [45, 15], [15, 40], [35, 55], [65, 10], [85, 25], [30, 70], [80, 40],
        #         [55, 60], [5, 10]
        #     ]
        #     target = random.choice(targets)
        #     await self.move(target)

    async def update_q_value(self, state, action, reward, next_state):
        # Convert state and next_state to fully hashable formats
        state_key = make_hashable(state)
        next_state_key = make_hashable(next_state)

        # Ensure the state_key and next_state_key exist in the Q-table
        if state_key not in self.q_table:
            self.q_table[state_key] = {}
        if next_state_key not in self.q_table:
            self.q_table[next_state_key] = {}

        # Get the current Q-value for the state-action pair
        current_q = self.q_table[state_key].get(action, 0)

        # Calculate the maximum future Q-value for the next state
        next_state_values = self.q_table[next_state_key].values()
        max_future_q = max(next_state_values) if next_state_values else 0

        # Update the Q-value using the Q-learning formula
        new_q = (1 - self.learning_rate) * current_q + self.learning_rate * (reward + self.discount_factor * max_future_q)

        # Save the updated Q-value
        self.q_table[state_key][action] = new_q

        # Log the update to a CSV
        write_to_csv(self, state, action, reward, new_q)

    def choose_action_with_ball(self, state):
        """Choose an action based on the player's role, current state, and field awareness."""
        # Normalize state for consistency
        state_key = make_hashable(state)

        # Fetch and prioritize available actions based on role
        actions = get_role_prioritized_actions(state)

        # print(f"{self.player_group} got {actions}")

        # Refine action list based on field awareness
        prioritized_actions = apply_field_awareness_with_ball(state, actions)

        write_actions_to_csv(self, actions, prioritized_actions)

        # Decide between exploration and exploitation
        if np.random.rand() < self.exploration_rate:
            # Exploration: Pick a random action
            action = random.choice(prioritized_actions)
        else:
            # Exploitation: Choose the best action based on Q-values
            q_values = self.q_table.get(state_key, {})

            action = max(q_values, key=q_values.get, default=random.choice(prioritized_actions))
        return action
    
    async def execute_action(self, action, game, ball, attacking_team, defending_team, state):

        direction = 1 if self.player_team == "A" else -1
        closest_open_spaces, player_team, role, has_ball, player_pos, closest_teammate_coordinates,closest_teammate_object, number_of_opponents_nearby = state
        if action == "pass":
            return await self.pass_ball(attacking_team, ball, game, state, direction)
        elif action == "shoot":
            return await self.shoot_goal(state)
        # elif action == "supportPlayerWithBall":
        #     return await self.supportPlayerWithBall(player_with_ball, action)
        elif action == "moveWithBall":
            target = state[0]
            return await self.move(target)
            # penalty = self.zone_penalty()  # Apply zone penalty if necessary
            # return move_reward + penalty
        # elif action == "maintain_line":
        #     maintain_reward = await self.maintain_line()
        #     return maintain_reward

        return 0  # default reward for unknown actions
    
    async def shoot_goal(self, action):
        # reward = 5  # Base reward for attempting a shot
        # goal_position = goal_position_teamA if self.player_team == "A" else goal_position_teamB
        # shot_distance = math.dist(self.player_coordinates, goal_position)

        # # Add rewards for high-probability shots
        # if shot_distance <= 18:
        #     reward += 10
        # elif shot_distance <= 30:
        #     reward += 3
        # else:
        #     reward -= 3  # Penalize low-probability shots

        # # await write_to_live_csv(self.player_name, self.player_coordinates, self.player_team, self.has_ball, action, self.zone, self.player_pos)
        # return reward

        return 5

    async def pass_ball(self, team, ball, game, state, direction):

        closest_open_spaces, player_team, role, has_ball, player_pos, closest_teammate_coordinates,closest_teammate_object, number_of_opponents_nearby = state
       
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
            player_with_ball.player_coordinates[0] - 10,  # Adjust to maintain support distance
            player_with_ball.player_coordinates[1] - 5
        )
        await self.move(target)
        return reward

    ######## DEFEND Code

    async def defend(self, attacking_team, defending_team, ball, game, player_with_ball):

        # All other players move independently
        targets = [
            [10, 50], [20, 75], [30, 20], [40, 90], [50, 10], [60, 85], [70, 40], [80, 30], [90, 60], [5, 95],
            [15, 15], [25, 70], [35, 35], [45, 80], [55, 45], [65, 5], [75, 25], [85, 65], [95, 50], [50, 95],
            [60, 20], [40, 55]
        ]

        target = random.choice(targets)
        await self.move(target)

class Ball:

    def __init__(self, player_with_ball_position):
        super().__init__()

        self.position = player_with_ball_position
    


    async def move(self, start, finish, game, player_who_passed, target_player):
        self.position = start

        reward = 5
        while math.dist(self.position, finish) >= 0.5:  # Continue until the ball reaches the target
            ball_start_x, ball_start_y = self.position
            target_x, target_y = finish

            dx = target_x - ball_start_x
            dy = target_y - ball_start_y

            distance = math.dist(self.position, finish)
            speed = max(0.1, min(distance / 5, 10))  # Ball speed

            norm = np.linalg.norm([dx, dy])
            direction = (dx / norm, dy / norm) if norm != 0 else (0, 0)

            # Update ball position incrementally
            self.position = (
                self.position[0] + direction[0] * speed,
                self.position[1] + direction[1] * speed,
            )

            # Check if the ball path has come close to an opponent position or a another teammate position
            for player in game.players:
                
                if player != player_who_passed and math.dist(self.position, player.player_coordinates) <= 1:

                    self.switch_possession(player, game)
                    await asyncio.sleep(0.1)
                    if player.player_team != target_player.player_team:

                        reward -= 10

                    return reward

            # Update visualization to reflect ball movement
            if game:
                game.update_visualization(self)

            # Simulate time for ball movement
            await asyncio.sleep(0.005)  # Reduce delay for quicker updates

        # Ensure the ball ends exactly at the target position
        self.position = finish
        self.switch_possession(target_player, game)

        if game:
            game.update_visualization(self)
        
        return reward 


    def switch_possession(self, new_player, game):

        # Reset all players for ball possession

        for player in game.players:
            player.has_ball = False
        
        new_player.has_ball = True

        game.update_team_with_ball(new_player)


class Game(Model):
    def __init__(self):
        super().__init__()
        self.players = []
        self.TeamA = []
        self.TeamB = []
        self.ball_movement = []

        # Generate players for Team A and Team B
        teamAPlayers, teamBPlayers = get_players.generate_players(4, 3, 3)

        # Initialize player class
        for player_name, player_info in teamAPlayers.items():
            player_pos = player_info[0]
            player_coordinates = player_info[1]
            player = Player(player_name, self, player_pos, player_coordinates, "A")
            self.players.append(player)
            self.TeamA.append(player)

        for player_name, player_info in teamBPlayers.items():
            player_pos = player_info[0]
            player_coordinates = player_info[1]
            player = Player(player_name, self, player_pos, player_coordinates, "B")
            self.players.append(player)
            self.TeamB.append(player)

        # Add teammates 

        for player in self.TeamA :
            self.add_teammates(player, self.TeamA)
        
        for player in self.TeamB:
            self.add_teammates(player, self.TeamB)
        # Initialize pitch and plot elements
        self.pitch = Pitch(pitch_type='statsbomb', pitch_color='grass', line_color='white')
        self.fig, self.ax = plt.subplots(figsize=(10, 8))
        self.pitch.draw(self.ax)

        # Initialize scatter plots and ball
        self.player_scatters = self.ax.scatter([], [], s=100, color=[])
        self.ball_scatter = self.ax.scatter([], [], s=30, color="yellow")

        self.zone_patches = []
        for zone in [player.zone for player in self.players]:
            (x_min, y_min), (x_max, y_max) = zone
            rect = patches.Rectangle(
                (x_min, y_min),  # Bottom-left corner
                x_max - x_min,   # Width
                y_max - y_min,   # Height
                linewidth=1,
                edgecolor='green',
                facecolor='none'  # Transparent fill
            )
            self.ax.add_patch(rect)
            self.zone_patches.append(rect)

    def add_teammates(self, player, team):

        player.teammates = [teammate for teammate in team if teammate != player]

    def update_visualization(self, ball):
        # Update player positions and colors
        player_positions = [player.player_coordinates for player in self.players]

        player_colors = [
            'white' if player.has_ball else ('blue' if player.player_team == 'A' else 'red')
            for player in self.players
        ]
        self.player_scatters.set_offsets(player_positions)
        self.player_scatters.set_color(player_colors)


        # Update ball position
        self.ball_scatter.set_offsets([ball.position])

        # Redraw the updated plot
        self.fig.canvas.draw_idle()
        plt.pause(0.01)  # Allow time for rendering
    
    def setTeamPossession(self, player_with_ball):

        attacking_team = None
        defending_team = None
        if player_with_ball in self.TeamA:
            attacking_team = self.TeamA
            defending_team = self.TeamB
        elif player_with_ball in self.TeamB:
            attacking_team = self.TeamB
            defending_team = self.TeamA
        
        return (attacking_team, defending_team)
    
    def update_team_with_ball(self, new_player):

        attacking_team, defending_team = self.setTeamPossession(new_player, )
        
        return attacking_team, defending_team
    
    async def start_game(self, ball, player_with_ball):

        
        # Create a separate coroutine for each player
        player_tasks = [asyncio.create_task(self.player_loop(player, ball)) for player in self.players]

        # Run visualization independently
        visualization_task = asyncio.create_task(self.visualization_loop(ball))

        # Wait for all tasks to complete (they won't in this loop, so this keeps running)
        await asyncio.gather(*player_tasks, visualization_task)
    

    async def player_loop(self, player, ball):
        while True:

            player_with_ball = next(player for player in self.players if player.has_ball)
            attacking_team, defending_team = self.update_team_with_ball(player_with_ball)

            await player.play(self, ball, attacking_team, defending_team, player_with_ball)
            # Add a small delay to prevent overwhelming the event loop
            await asyncio.sleep(0.01)
    

    async def visualization_loop(self, ball):
        while True:
            self.update_visualization(ball)
            await asyncio.sleep(0.1)  # Adjust the interval as needed


async def run_game():
    game = Game()
    # targets = [
    #     [50, 50], [0, 90], [60, 100], [40, 30], [20, 30], [21, 75], [5, 95], [9, 89], [56, 23], [92, 23],
    #     [10, 10], [70, 70], [25, 85], [45, 15], [15, 40], [35, 55], [65, 10], [85, 25], [30, 70], [80, 40],
    #     [55, 60], [5, 10]
    # ]
    # Show the plot
    plt.ion()  # Turn on interactive mode
    player_with_ball = random.choice([player for player in game.players])
    player_with_ball.has_ball = True

    ball = Ball(player_with_ball.player_coordinates)

    print(player_with_ball.player_name)
    await game.start_game(ball, player_with_ball)
    plt.ioff()  # Turn off interactive mode
    plt.show()


asyncio.run(run_game())
