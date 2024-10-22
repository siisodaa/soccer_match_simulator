import time
import random
import matplotlib.pyplot as plt
import numpy as np
import math

goal_keeper_start_wth = [100, 50]
GOAL_POS_X = 100
GOAL_POS_Y = [46, 54]
INNER_GOAL_POS_X = 94
INNER_GOAL_POS_Y = [37, 63]
GOALKEEPER_height = 2
GOALKEEPER_forward = 6
FIELD_X = 100
FIELD_Y = 100

defense = {
    "CB1": [random.randint(15, 15), random.randint(35, 45)],  # Center Back 1
    "CB2": [random.randint(15, 15), random.randint(45, 55)],  # Center Back 2
    "LB": [30, 75],  # Left Back
    "RB": [30, 15]   # Right Back
}

midfield = {
    "CM": [random.randint(50, 50), random.randint(45, 55)],  # Central Midfielders (spread across the center)
    "LM": [50, 85],  # Left Midfielder
    "RM": [50, 15]   # Right Midfielder
}

offense = {
    "ST": [85, 50],  # Striker
    "LW": [75, 90],  # Left Winger
    "RW": [75, 10]   # Right Winger
}

class Game:

    def __init__(self):
        self.groupA = []
        self.groupB = []

    def add_players(self, player_name, player_role, player_group):

        player_start_pos = None

        if player_role in defense:
            player_start_pos = defense[player_role]
        elif player_role in midfield:
            player_start_pos = midfield[player_role]
        elif player_role in offense:
            player_start_pos = offense[player_role]

        player = Player(player_name, player_start_pos, player_role, player_group)

        if player_group == "A":
            self.groupA.append(player)

    def start_game(self, player_with_ball, duration):


        # Initialize plot
        plt.figure(figsize=(10, 6))
        plt.ion()  # Interactive mode on for real-time updates

        # Draw the initial field and fixed elements
        self.draw_field()


        teams = [self.groupA]
        currentPossessionTeam = random.choice(teams)
        player_with_ball = pick_player(currentPossessionTeam)
        player_with_ball.has_ball = True

        # Plot player positions initially
        player_markers = {}
        for player in currentPossessionTeam:
            x, y = player.playerPosition
            marker, = plt.plot(x, y, marker='o', linestyle='', label=player.playerName)
            player_markers[player.playerName] = marker

        plt.legend()
        plt.pause(0.1)


        print("Game is on")
        for i in range(duration):
            for player in self.groupA:
                if player.has_ball:
                    # Execute attacking behavior for player with the ball
                    executeAttackingBehavior(player, currentPossessionTeam, self.groupB)
                else:
                    # Execute support movement for players without the ball
                    executeSupportMovement(player, self.groupB, player_with_ball)

                player_markers[player.playerName].set_data([player.playerPosition[0]], [player.playerPosition[1]])

            # Draw the updated plot
            plt.draw()
            plt.pause(0.1)  # Pause for a short time to allow updates

            time.sleep(0.5)  # Pause to simulate time passing in the game
            
            # Move defenders forward while maintaining a line
            for player in self.groupA:
                if player.playerRole in defense:
                    moveDefendersForward(player, self.groupB)
                
                player_markers[player.playerName].set_data([player.playerPosition[0]], [player.playerPosition[1]])

            # Draw the updated plot
            plt.draw()
            plt.pause(0.1)  # Pause for a short time to allow updates

            time.sleep(0.5)  # Pause to simulate time passing in the game


            # Ensure offensive players have an opportunity to run towards the goal
            for player in self.groupA:
                if player.playerRole in offense and not player.has_ball:
                    makeRunTowardsGoal(player, self.groupB)
                
                player_markers[player.playerName].set_data([player.playerPosition[0]], [player.playerPosition[1]])

            # Draw the updated plot
            plt.draw()
            plt.pause(0.1)  # Pause for a short time to allow updates

            time.sleep(0.5)  # Pause to simulate time passing in the game

        plt.ioff()  # Turn off interactive mode
        plt.show()  # Show the final state of the plot after the game ends
        print("Game is over")
        print("Game is over")

    # def plot_game(player_positions=None, player_labels=None, player_movement=None, penalty_bottomleft=(84, 19), goal_keeper_movement=None, shot_points=None, penalty_topright=(100, 81)):
    #     # Create the rectangle's corners for the soccer field
    #     length = 100
    #     width = 100
    #     x = [0, length, length, 0, 0]
    #     y = [0, 0, width, width, 0]

    #     # Create the plot
    #     plt.figure(figsize=(10, 6))
    #     plt.plot(x, y, marker='o')
    #     plt.xlim(-10, length + 10)
    #     plt.ylim(-10, width + 10)

    #     # GOAL POINTS
    #     goal_start = [100, 46]  # Start point of the goal post
    #     goal_end = [100, 54]    # End point of the goal post
    #     plt.plot([goal_start[0], goal_end[0]], [goal_start[1], goal_end[1]], color='blue', linewidth=5, label='Goal Post')

    #     # CENTER
    #     center_start = [50, 100]
    #     center_end = [50, 0]
    #     plt.plot([center_start[0], center_end[0]], [center_start[1], center_end[1]], color='blue', linewidth=1, label='Center Line')

    #     # PENALTY BOX
    #     penalty_topleft = [penalty_bottomleft[0], penalty_topright[1]]
    #     penalty_bottomright = [penalty_topright[0], penalty_bottomleft[1]]

    #     # Plot the PENALTY BOX (rectangle)
    #     plt.plot([penalty_bottomleft[0], penalty_bottomleft[0]], [penalty_bottomleft[1], penalty_topright[1]], color='blue', linewidth=2)  # Left side
    #     plt.plot([penalty_bottomright[0], penalty_bottomright[0]], [penalty_bottomleft[1], penalty_topright[1]], color='blue', linewidth=2)  # Right side
    #     plt.plot([penalty_bottomleft[0], penalty_topright[0]], [penalty_bottomleft[1], penalty_bottomleft[1]], color='blue', linewidth=2)  # Bottom side
    #     plt.plot([penalty_bottomleft[0], penalty_topright[0]], [penalty_topright[1], penalty_topright[1]], color='blue', linewidth=2)  # Top side

    #     # Player Movement
    #     if player_movement:
    #         player_positions = {
    #             player_name: np.array(movements)
    #             for player_name, movements in player_movement.items()
    #         }

    #         for label, positions in player_positions.items():
    #             if positions.ndim == 2 and positions.shape[1] == 2:
    #                 x, y = positions[:, 0], positions[:, 1]
    #                 plt.plot(x, y, label=label, marker='o')
    #             else:
    #                 print(f"Warning: Skipping {label} due to incorrect shape {positions.shape}")
    #                 continue
        
    #     # Shot Movement

    #     if shot_points:
    #         # Preprocess shot_points to extract valid positions
    #         shot_positions = {}

    #         for player_name, movements in shot_points.items():
    #             # Flatten the nested lists to make it consistent
    #             flattened_movements = []
    #             for movement in movements:
    #                 if isinstance(movement, list):
    #                     # Further flatten any sub-list levels
    #                     for sub_movement in movement:
    #                         if isinstance(sub_movement, list):
    #                             flattened_movements.extend(sub_movement)
    #                         else:
    #                             flattened_movements.append(sub_movement)

    #             # Ensure all shot positions are valid (2D coordinates)
    #             valid_movements = [np.array(pos) for pos in flattened_movements if len(pos) == 2]

    #             if valid_movements:
    #                 shot_positions[player_name] = np.array(valid_movements)

    #         # Plot the shot points
    #         for label, positions in shot_positions.items():
    #             if positions.ndim == 2 and positions.shape[1] == 2:
    #                 x, y = positions[:, 0], positions[:, 1]
    #                 plt.plot(x, y, label="Shot", marker='o')
    #             else:
    #                 print(f"Warning: Skipping shot for {label} due to incorrect shape {positions.shape}")
    #                 continue

    #     # Show the plot
    #     plt.legend()
    #     plt.axis("off")
    #     plt.show()


    def draw_field(self):
        # Create the rectangle's corners for the soccer field
        length = 100
        width = 100
        x = [0, length, length, 0, 0]
        y = [0, 0, width, width, 0]

        # Draw the field
        plt.plot(x, y, marker='o')
        plt.xlim(-10, length + 10)
        plt.ylim(-10, width + 10)

        # Draw goal post
        goal_start = [100, 46]  # Start point of the goal post
        goal_end = [100, 54]    # End point of the goal post
        plt.plot([goal_start[0], goal_end[0]], [goal_start[1], goal_end[1]], color='blue', linewidth=5, label='Goal Post')

        # Draw center line
        center_start = [50, 100]
        center_end = [50, 0]
        plt.plot([center_start[0], center_end[0]], color='blue', linewidth=1, label='Center Line')

        # Draw penalty box
        penalty_bottomleft = (84, 19)
        penalty_topright = (100, 81)
        penalty_topleft = [penalty_bottomleft[0], penalty_topright[1]]
        penalty_bottomright = [penalty_topright[0], penalty_bottomleft[1]]

        # Plot the PENALTY BOX (rectangle)
        plt.plot([penalty_bottomleft[0], penalty_bottomleft[0]], [penalty_bottomleft[1], penalty_topright[1]], color='blue', linewidth=2)  # Left side
        plt.plot([penalty_bottomright[0], penalty_bottomright[0]], [penalty_bottomleft[1], penalty_topright[1]], color='blue', linewidth=2)  # Right side
        plt.plot([penalty_bottomleft[0], penalty_topright[0]], [penalty_bottomleft[1], penalty_bottomleft[1]], color='blue', linewidth=2)  # Bottom side
        plt.plot([penalty_bottomleft[0], penalty_topright[0]], [penalty_topright[1], penalty_topright[1]], color='blue', linewidth=2)  # Top side

        plt.axis("off")


class Player:

    def __init__(self, player_name, player_start_pos, player_role, player_team):
        self.playerName = player_name
        self.playerPosition = list(player_start_pos)
        self.playerMovement = [player_start_pos[:]]
        self.has_ball = False
        self.teammates = []
        self.playerRole = player_role
        self.pass_attempts = []
        self.shot_attempts = []
        self.playerTeam = player_team


def pick_player(currentPossessionTeam):
    options = [player for player in currentPossessionTeam if player.playerRole in midfield]
    if not options:
        options = [player for player in currentPossessionTeam if player.playerRole not in offense]
    player = random.choice(options)
    return player


def executeAttackingBehavior(player, currentPossessionTeam, defendingTeam):
    if player.playerRole in midfield:
        if player.has_ball:
            decidePassOption(player, currentPossessionTeam, defendingTeam)
        else:
            moveIntoOpenSpace(player, defendingTeam)

    elif player.playerRole in offense:
        if player.has_ball:
            # Run with the ball before attempting a pass or a shot
            runWithBall(player, defendingTeam)
            decidePassOrShoot(player, currentPossessionTeam, defendingTeam)
        else:
            makeRunTowardsGoal(player, defendingTeam)


def runWithBall(player, defendingTeam):
    print(f"{player.playerName} is running with the ball")
    x, y = player.playerPosition[0], player.playerPosition[1]
    possible_moves = [(i, j) for i in range(x, x + 5) if 0 <= i < FIELD_X for j in range(y - 5, y + 5) if 0 <= j < FIELD_Y]

    for opponent in defendingTeam:
        if opponent.playerPosition in possible_moves:
            possible_moves.remove(opponent.playerPosition)

    if possible_moves:
        old_position = player.playerPosition
        player.playerPosition = random.choice(possible_moves)
        simulate_run(player, list(old_position), defendingTeam)
    else:
        print("No valid moves while running with the ball")

# HARD CODED NUMBER HERE
def decidePassOrShoot(player, currentPossessionTeam, defendingTeam):
    # Check if the player is close enough to the goal or if there is an open teammate in the penalty area
    if player.playerPosition[0] >= 84 and player.playerPosition[1] < 80 or player.playerPosition[1] > 20:
        # Check for open teammates in the penalty area
        open_teammates = [
            teammate for teammate in currentPossessionTeam
            if not teammate.has_ball and
            INNER_GOAL_POS_X >= teammate.playerPosition[0] <= GOAL_POS_X and
            INNER_GOAL_POS_Y[0] >= teammate.playerPosition[1] <= INNER_GOAL_POS_Y[1]
        ]
        if open_teammates:
            teammate = random.choice(open_teammates)
            teammate.has_ball = True
            player.has_ball = False
            player.pass_attempts.append([player.playerPosition, teammate.playerPosition])
            print(f"{player.playerName} passed the ball to {teammate.playerName} in the penalty area")
        else:
            # Shoot the ball if no open teammates in the penalty area
            attemptShotOnGoal(player, defendingTeam)
    else:
        # Continue running with the ball if not close enough to the goal
        runWithBall(player, defendingTeam)


def executeSupportMovement(player, defendingTeam, ballCarrier):
    print("Executing Support Movement")
    if player.playerRole in midfield:
        moveCloserToBallCarrier(player, defendingTeam, ballCarrier)
    elif player.playerRole in offense:
        makeRunTowardsGoal(player, defendingTeam)


def decidePassOption(player, currentPossessionTeam, defendingTeam):
    # Pass it to someone in front of you who is open
    for teammate in currentPossessionTeam:
        if teammate != player:
            if teammate.playerPosition[0] > player.playerPosition[0]:
                # Is the player open?
                if is_player_open(teammate.playerPosition, defendingTeam):
                    # Pass the ball to that player
                    teammate.has_ball = True
                    player.has_ball = False
                    player.pass_attempts.append([player.playerPosition, teammate.playerPosition])
                    print(f"passed the ball to {teammate.playerName}")
                    return

    if player.has_ball:
        print('Could not find a close teammate that was before me that was open')


def is_player_open(teammate_coordinates, defendingTeam):
    # Check if there is a player from the defending team in their 1 by 1 square
    teammate_is_open = True
    x, y = teammate_coordinates[0], teammate_coordinates[1]
    player_square = get_surrounding_square(x, y)

    for opponent in defendingTeam:
        if opponent.playerPosition in player_square:
            teammate_is_open = False
    return teammate_is_open


def get_surrounding_square(x, y):
    surrounding_square = [(i, j) for i in range(max(0, x - 1), min(FIELD_X, x + 2)) for j in range(max(0, y - 1), min(FIELD_Y, y + 2))]
    return surrounding_square


def moveIntoOpenSpace(player, defendingTeam):
    print("Moved into space")
    x, y = player.playerPosition[0], player.playerPosition[1]
    possible_moves = [(i, j) for i in range(x, x + 10) if i < FIELD_X for j in range(y - 10, y + 10) if 0 <= j < FIELD_Y]

    for opponent in defendingTeam:
        if opponent.playerPosition in possible_moves:
            possible_moves.remove(opponent.playerPosition)

    if possible_moves:
        old_position = player.playerPosition 
        player.playerPosition = random.choice(possible_moves)

        # Simulate run from old position to new position
        simulate_run(player, old_position, defendingTeam)
        
        print(f"Moved into {player.playerPosition}")
    else:
        print("No valid moves available!")


def simulate_run(player, old_position, defendingTeam):
    print("Simulating run")
    dx = player.playerPosition[0] - old_position[0]
    dy = player.playerPosition[1] - old_position[1]

    distance = math.dist(player.playerPosition, old_position)

    step_size = 1
    if distance > 0:  # Avoid division by zero
        dx = (dx / distance) * step_size
        dy = (dy / distance) * step_size

    current_position = old_position[:]
    while math.dist(current_position, player.playerPosition) > step_size:
        next_position = [current_position[0] + dx, current_position[1] + dy]

        # Avoid going beyond the field bounds
        next_position[0] = max(0, min(FIELD_X - 1, next_position[0]))
        next_position[1] = max(0, min(FIELD_Y - 1, next_position[1]))

        # Avoid positions occupied by the defending team
        if next_position not in [opponent.playerPosition for opponent in defendingTeam]:
            current_position = next_position
            player.playerMovement.append(current_position[:])
        else:
            break

    # Ensure the final position is exactly the target position
    player.playerMovement.append(player.playerPosition[:])


def attemptShotOnGoal(player, goal_keeper_start_wth):
    start_pos_x, start_pos_y = player.playerPosition[0], player.playerPosition[1]
    start_wth = [start_pos_x, start_pos_y]
    points_to_shoot = random.randint(min(GOAL_POS_Y), max(GOAL_POS_Y))
    shot_the_ball = [GOAL_POS_X, points_to_shoot]
    end_with = shot_the_ball
    player.shot_attempts.append([start_wth, end_with])
    print(f"{player.playerName} attempted a shot")

    if player.playerTeam == "A":
        currentPossessionTeam = game.groupA
    else:
        currentPossessionTeam = game.groupB

    player_with_ball = pick_player(currentPossessionTeam)
    player_with_ball.has_ball = True
    print(f"After shot, possession reset to {player_with_ball.playerName} at midfield")


def makeRunTowardsGoal(player, defendingTeam):
    print("making run towards goal")
    x, y = player.playerPosition[0], player.playerPosition[1]
    possible_moves = [(i, j) for i in range(x, x + 5) if i < FIELD_X for j in range(y - 10, y + 10) if 0 <= j < FIELD_Y]

    for opponent in defendingTeam:
        if opponent.playerPosition in possible_moves:
            possible_moves.remove(opponent.playerPosition)

    if possible_moves:
        old_position = player.playerPosition
        player.playerPosition = random.choice(possible_moves)

        simulate_run(player, old_position, defendingTeam)
    else:
        print("No possible moves")


def moveCloserToBallCarrier(player, defendingTeam, ballCarrier):
    print("Moving closer to Ball Carrier")
    x, y = ballCarrier.playerPosition[0], ballCarrier.playerPosition[1]
    possible_moves = [(i, j) for i in range(max(0, x), min(FIELD_X, x + 5)) for j in range(max(0, y - 5), min(FIELD_Y, y + 5))]

    for opponent in defendingTeam:
        if opponent.playerPosition in possible_moves:
            possible_moves.remove(opponent.playerPosition)

    if possible_moves:
        old_position = player.playerPosition
        player.playerPosition = random.choice(possible_moves)

        simulate_run(player, old_position, defendingTeam)
    else:
        print("No possible moves")

# ACCOUNT FOR POSITIONS WHERE DEFENDING TEAM IS
def moveDefendersForward (player, defendingTeam):

  print("Moving Defenders forward")

  x, y = player.playerPosition[0], player.playerPosition[1]

  # Adjust the possible range to ensure valid moves
  possible_moves = [
      (i, j)
      for i in range(max(0, x), min(50, x + 10))
      for j in range(max(0, y - 5), min(FIELD_Y, y + 5))
  ]

  old_position = player.playerPosition
  player.playerPosition = random.choice(possible_moves)

  simulate_run(player, old_position, defendingTeam)



if __name__ == "__main__":
    game = Game()

    game.add_players("Xassan", "CB1", "A")
    game.add_players("Ali", "CB2", "A")
    game.add_players("Ahmed", "CM", "A")
    game.add_players("Umar", "LM", "A")
    game.add_players("Saki", "RM", "A")
    game.add_players("Geedi", "ST", "A")
    game.add_players("Dembele", "LW", "A")
    game.add_players("Mohamed", "RW", "A")

    game.groupA[0].has_ball = True

    # Add teammates
    for player in game.groupA:
        player.teammates = [p for p in game.groupA if p != player]

    game.start_game(game.groupA[0], duration=50)

    # player_movement = {}
    # shot_movement = {}

    # for player in game.groupA:
    #     if player.playerName not in player_movement:
    #         player_movement[player.playerName] = []  # Initialize as an empty list
    #     player_movement[player.playerName].extend(player.playerMovement)

    #     if player.playerName not in shot_movement:
    #         shot_movement[player.playerName] = []
    #     shot_movement[player.playerName].append(player.shot_attempts)
    

    # game.plot_game(player_movement=player_movement, shot_points=shot_movement)
