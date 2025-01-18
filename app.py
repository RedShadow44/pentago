from flask import Flask, render_template, request, redirect, url_for, session
from flask_session import Session
import uuid
from random import choice

app = Flask(__name__)

# Configure session to use filesystem
app.config['SESSION_TYPE'] = 'filesystem'
app.secret_key = 'your_secret_key'
Session(app)

# Global dictionary to store game states
games = {}


def initialize_game(against_bot=False):
    """Initializes a new game state."""
    return {
    # Initialize a 6x6 board (0: empty, 1: black, 2: white)
    'board': [[0 for _ in range(6)] for _ in range(6)],

    # Track whether rotation is required before the next move
    'rotation_required': False,

    # Track the current player (1: black, 2: white)
    'current_player': 1,

    # Track game state
    'game_over': False,
    'winner': None,

    'against_bot': against_bot,  # True if playing against the bot

    }



def print_game_state(game_state):
    """Prints the current game state to the console."""
    print("\n--- Game State ---")
    print("Board:")
    for row in game_state['board']:
        print(' '.join(['⚫' if cell == 1 else '⚪' if cell == 2 else '.' for cell in row]))
    print(f"\nCurrent Player: {'⚫ (Black)' if game_state['current_player'] == 1 else '⚪ (White)'}")
    print(f"Rotation Required: {'Yes' if game_state['rotation_required'] else 'No'}")
    print(f"Game Over: {'Yes' if game_state['game_over'] else 'No'}")
    if game_state['game_over']:
        if game_state['winner'] == 1:
            print("Winner: ⚫ (Black)")
        elif game_state['winner'] == 2:
            print("Winner: ⚪ (White)")
        elif game_state['winner'] == 'draw':
            print("Result: It's a Draw!")
    print("------------------\n")

def check_winner(board):
    """Checks if there's a winner or a draw."""

    def five_in_a_row(line):
        """Checks if a line contains five consecutive identical non-zero values."""
        for i in range(len(line) - 4):
            if line[i] != 0 and line[i] == line[i+1] == line[i+2] == line[i+3] == line[i+4]:
                return line[i]
        return None

    # Check rows and columns
    for i in range(6):
        row_result = five_in_a_row(board[i])
        col_result = five_in_a_row([board[j][i] for j in range(6)])
        if row_result:
            return row_result
        if col_result:
            return col_result

    # Check diagonals
    diagonals = []
    for d in range(-2, 3):  # Diagonals with at least 5 elements
        # Top-left to bottom-right
        diagonals.append([board[i][i + d] for i in range(max(0, -d), min(6, 6 - d))])
        # Bottom-left to top-right
        diagonals.append([board[i][5 - i - d] for i in range(max(0, d), min(6, 6 - d)) if 0 <= 5 - i - d < 6])

    for diag in diagonals:
        diag_result = five_in_a_row(diag)
        if diag_result:
            return diag_result

    # Check for a draw (no empty spaces and no winner)
    if all(cell != 0 for row in board for cell in row):
        return 'draw'

    return None

# def rotate_board_smartly(game_state):
#     """Rotate the board with a smart strategy."""
#     from random import choice
#
#     board = game_state['board']
#     current_player = 2
#     opponent = 1
#
#     def simulate_rotation(quadrant, direction):
#         """Simulates rotation on the board and returns the resulting board."""
#         temp_board = [row[:] for row in board]
#
#         start_row = 0 if quadrant in [1, 2] else 3
#         start_col = 0 if quadrant in [1, 3] else 3
#         subgrid = [temp_board[i][start_col:start_col + 3] for i in range(start_row, start_row + 3)]
#
#         if direction == 'cw':
#             subgrid = list(zip(*subgrid[::-1]))
#         elif direction == 'ccw':
#             subgrid = list(zip(*subgrid))[::-1]
#
#         for i in range(3):
#             for j in range(3):
#                 temp_board[start_row + i][start_col + j] = subgrid[i][j]
#
#         return temp_board
#
#     def evaluate_rotation(board_after_rotation, player):
#         """Evaluate the board after rotation. Higher score means better for the player."""
#         # Simple heuristic: number of player's pieces in a row/column/diagonal
#         score = 0
#         for row in board_after_rotation:
#             score += row.count(player)
#         for col in zip(*board_after_rotation):
#             score += list(col).count(player)
#         return score
#
#     best_rotation = None
#     best_score = float('-inf')
#
#     # Try all rotations and evaluate
#     for quadrant in [1, 2, 3, 4]:
#         for direction in ['cw', 'ccw']:
#             rotated_board = simulate_rotation(quadrant, direction)
#             score = evaluate_rotation(rotated_board, current_player)
#             if score > best_score:
#                 best_score = score
#                 best_rotation = (quadrant, direction)
#
#     # Apply the best rotation
#     if best_rotation:
#         quadrant, direction = best_rotation
#         start_row = 0 if quadrant in [1, 2] else 3
#         start_col = 0 if quadrant in [1, 3] else 3
#         subgrid = [board[i][start_col:start_col + 3] for i in range(start_row, start_row + 3)]
#
#         if direction == 'cw':
#             subgrid = list(zip(*subgrid[::-1]))
#         elif direction == 'ccw':
#             subgrid = list(zip(*subgrid))[::-1]
#
#         for i in range(3):
#             for j in range(3):
#                 board[start_row + i][start_col + j] = subgrid[i][j]

def rotate_board_smartly(game_state):
    """Rotate the board with a strategy that minimizes opponent's score and maximizes the bot's advantage."""
    board = game_state['board']
    current_player = 2  # Bot's pieces
    opponent = 1  # Opponent's pieces

    def simulate_rotation(quadrant, direction):
        """Simulates rotation on the board and returns the resulting board."""
        temp_board = [row[:] for row in board]

        start_row = 0 if quadrant in [1, 2] else 3
        start_col = 0 if quadrant in [1, 3] else 3
        subgrid = [temp_board[i][start_col:start_col + 3] for i in range(start_row, start_row + 3)]

        if direction == 'cw':
            subgrid = list(zip(*subgrid[::-1]))
        elif direction == 'ccw':
            subgrid = list(zip(*subgrid))[::-1]

        for i in range(3):
            for j in range(3):
                temp_board[start_row + i][start_col + j] = subgrid[i][j]

        return temp_board

    def evaluate_board(board_to_evaluate, player):
        """Evaluates the score for the given player."""
        score = 0

        # Check rows and columns
        for row in board_to_evaluate:
            score += count_potential_lines(row, player)
        for col in zip(*board_to_evaluate):
            score += count_potential_lines(col, player)

        # Check diagonals
        diagonals = [
            [board_to_evaluate[i][i] for i in range(6)],  # Main diagonal
            [board_to_evaluate[i][5 - i] for i in range(6)]  # Anti-diagonal
        ]
        for diag in diagonals:
            score += count_potential_lines(diag, player)

        return score

    def count_potential_lines(line, player):
        """Counts potential lines (3 or more in a row) for the given player."""
        count = 0
        pieces = [1 if x == player else 0 for x in line]
        if sum(pieces) >= 3:  # If at least 3 marbles of the player exist
            count += 1
        return count

    best_rotation = None
    best_score_difference = float('-inf')  # Maximize bot's advantage, minimize opponent's

    # Try all rotations and evaluate
    for quadrant in [1, 2, 3, 4]:
        for direction in ['cw', 'ccw']:
            rotated_board = simulate_rotation(quadrant, direction)
            bot_score = evaluate_board(rotated_board, current_player)
            opponent_score = evaluate_board(rotated_board, opponent)
            score_difference = bot_score - opponent_score

            # Choose the rotation that maximizes the score difference
            if score_difference > best_score_difference:
                best_score_difference = score_difference
                best_rotation = (quadrant, direction)

    # Apply the best rotation
    if best_rotation:
        quadrant, direction = best_rotation
        start_row = 0 if quadrant in [1, 2] else 3
        start_col = 0 if quadrant in [1, 3] else 3
        subgrid = [board[i][start_col:start_col + 3] for i in range(start_row, start_row + 3)]

        if direction == 'cw':
            subgrid = list(zip(*subgrid[::-1]))
        elif direction == 'ccw':
            subgrid = list(zip(*subgrid))[::-1]

        for i in range(3):
            for j in range(3):
                board[start_row + i][start_col + j] = subgrid[i][j]


@app.route('/')
def index():
    """Displays the starting page."""
    session.clear()  # Clear any existing session data before starting a new games
    return render_template('start.html')

@app.route('/new_game/<against_bot>')
def new_game(against_bot):
    """Starts a new game against a bot or player."""
    against_bot = against_bot == 'true'  # Convert to boolean
    game_id = str(uuid.uuid4())  # Generate a unique game ID
    games[game_id] = initialize_game(against_bot=against_bot)  # Store the new game state
    session['game_id'] = game_id  # Store the game_id in the session
    return redirect(url_for('game', game_id=game_id))  # Redirect with game_id in the URL



@app.route('/game/<game_id>')
def game(game_id):
    """Displays the game board for a specific game."""
    if game_id not in games:
        return redirect(url_for('index'))  # Redirect to start if game ID is invalid

    game_state = games[game_id]
    # print_board(game_state['board'])
    # print("Plansza:")
    # print_game_state(game_state)
    return render_template(
        'board.html',
        game_id=game_id,
        enumerate=enumerate,
        board=game_state['board'],
        rotation_required=game_state['rotation_required'],
        current_player=game_state['current_player'],
        game_over=game_state['game_over'],
        winner=game_state['winner'],
        against_bot=game_state['against_bot'],
    )


@app.route('/move/<game_id>', methods=['POST'])
def move(game_id):
    """Handles placing a marble on the board."""
    if game_id not in games:
        return redirect(url_for('index'))

    game_state = games[game_id]

    # print_board(game_state['board'])


    board = game_state['board']
    current_player = game_state['current_player']

    # Ensure moves cannot happen when the game is over
    if game_state['game_over']:
        return redirect(url_for('game', game_id=game_id))

    # Only allow the human player to place a marble
    if game_state['against_bot'] and current_player == 2:
        return redirect(url_for('game', game_id=game_id))

    row = int(request.form['row'])
    col = int(request.form['col'])

    # Place the player's marble if the spot is empty
    if board[row][col] == 0:
        board[row][col] = current_player
        game_state['rotation_required'] = True # Require rotation after placing the marble

        print("Plansza po kulce gracza:")
        print_game_state(game_state)

        # Check for a winner or draw
        result = check_winner(board)
        if result:
            game_state['game_over'] = True
            game_state['winner'] = result
            return redirect(url_for('game', game_id=game_id))


    return redirect(url_for('game', game_id=game_id))



def bot_move(game_state):
    """Handles the bot's move with smart logic."""
    from random import choice

    board = game_state['board']
    current_player = 2  # Bot is always player 2
    opponent = 1

    def find_winning_move(player):
        """Find a winning move for the given player."""
        for row in range(6):
            for col in range(6):
                if board[row][col] == 0:  # Check empty spots
                    # Simulate placing a marble
                    board[row][col] = player
                    if check_winner(board) == player:
                        board[row][col] = 0  # Undo simulation
                        return row, col
                    board[row][col] = 0  # Undo simulation
        return None

    def find_blocking_move(player):
        """Find a move to block the player from getting 2 or more in a line."""
        def count_line(line, target):
            """Count occurrences of target and empty spaces in a line."""
            count_target = sum(1 for x in line if x == target)
            empty_positions = [i for i, x in enumerate(line) if x == 0]
            return count_target, empty_positions

        # Check rows and columns
        for row in range(6):
            count, empties = count_line(board[row], player)
            if count >= 2 and empties:  # Block if 2 or more marbles and space exists
                return row, empties[0]

        for col in range(6):
            column = [board[row][col] for row in range(6)]
            count, empties = count_line(column, player)
            if count >= 2 and empties:
                return empties[0], col

        # Check diagonals
        diagonals = [
            [(i, i) for i in range(6)],  # Main diagonal
            [(i, 5 - i) for i in range(6)]  # Anti-diagonal
        ]
        for diag in diagonals:
            line = [board[i][j] for i, j in diag]
            count, empties = count_line(line, player)
            if count >= 2 and empties:
                i, j = diag[empties[0]]
                return i, j

        return None

    # 1. Check for bot's winning move
    winning_move = find_winning_move(current_player)
    if winning_move:
        row, col = winning_move
    else:
        # 2. Block opponent's winning move
        block_opponent = find_winning_move(opponent)
        if block_opponent:
            row, col = block_opponent
        else:
            # 3. Find a blocking move to disrupt opponent's strategy
            blocking_move = find_blocking_move(opponent)
            if blocking_move:
                row, col = blocking_move
            else:
                # 4. Choose a strategic move
                strategic_order = [
                    (2, 2), (2, 3), (3, 2), (3, 3),  # Center of the board
                    (1, 1), (1, 4), (4, 1), (4, 4),  # Centers of quadrants
                    (0, 0), (0, 5), (5, 0), (5, 5),  # Corners
                ]
                empty_spots = [(i, j) for i in range(6) for j in range(6) if board[i][j] == 0]
                strategic_moves = [pos for pos in strategic_order if pos in empty_spots]
                row, col = choice(strategic_moves) if strategic_moves else choice(empty_spots)

    # Place the marble
    board[row][col] = current_player
    game_state['rotation_required'] = True

    print("Plansza po kulce bota:")
    print_game_state(game_state)

    # Check for a winner after placing the marble
    result = check_winner(board)
    if result:
        game_state['game_over'] = True
        game_state['winner'] = result
        return

    # If no winner, proceed to rotation
    rotate_board_smartly(game_state)
    game_state['rotation_required'] = False

    print("Plansza po obruceniu przez bota:")
    print_game_state(game_state)

    # Check for a winner after rotating board
    result = check_winner(board)
    if result:
        game_state['game_over'] = True
        game_state['winner'] = result
        return

    # Switch back to the human player
    game_state['current_player'] = 1





@app.route('/rotate/<game_id>', methods=['POST'])
def rotate(game_id):
    """Handles rotating a quadrant."""
    if game_id not in games:
        return redirect(url_for('index'))

    game_state = games[game_id]

    # print_board(game_state['board'])


    board = game_state['board']

    current_player = game_state['current_player']

    # Allow rotation only if it is required and the game is not over
    if not game_state['rotation_required'] or game_state['game_over']:
        return redirect(url_for('game', game_id=game_id))

    quadrant = int(request.form['quadrant'])  # 1 to 4
    direction = request.form['direction']  # 'cw' or 'ccw'

    # Determine the quadrant start positions
    start_row = 0 if quadrant in [1, 2] else 3
    start_col = 0 if quadrant in [1, 3] else 3

    # Extract the subgrid
    subgrid = [row[start_col:start_col + 3] for row in board[start_row:start_row + 3]]

    # Rotate the subgrid
    if direction == 'cw':
        subgrid = list(zip(*subgrid[::-1]))
    elif direction == 'ccw':
        subgrid = list(zip(*subgrid))[::-1]

    # Place the rotated subgrid back
    for i in range(3):
        for j in range(3):
            board[start_row + i][start_col + j] = subgrid[i][j]

    print("Plansza po obruceniu przez gracza:")
    print_game_state(game_state)

    # Check for a winner or draw
    result = check_winner(board)
    if result:
        game_state['game_over'] = True
        game_state['winner'] = result
    else:
        # Switch player if the game is not over
        game_state['current_player'] = 2 if current_player == 1 else 1
    # Reset rotation requirement
    game_state['rotation_required'] = False

    # If the next player is the bot, trigger its move
    # if game_state['against_bot'] and game_state['current_player'] == 2:
    #     bot_move(game_state)

    return redirect(url_for('game', game_id=game_id))

@app.route('/bot_move/<game_id>', methods=['GET','POST'])
def bot_move_route(game_id):
    """Trigger the bot's move."""
    if game_id not in games:
        return redirect(url_for('index'))

    game_state = games[game_id]

    # Make the bot move
    bot_move(game_state)

    # Redirect to the game page after bot makes its move
    return redirect(url_for('game', game_id=game_id))


@app.route('/reset/<game_id>')
def reset(game_id):
    """Resets the game state and redirects to the game page."""
    if game_id in games:
        games[game_id] = initialize_game()  # Reset the specific game
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='12203', debug=True)
