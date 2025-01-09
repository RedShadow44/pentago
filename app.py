from flask import Flask, render_template, request, redirect, url_for, session
from flask_session import Session
import uuid
app = Flask(__name__)

# Configure session to use filesystem
app.config['SESSION_TYPE'] = 'filesystem'
app.secret_key = 'your_secret_key'
Session(app)

# Global dictionary to store game states
games = {}

def initialize_game():
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
    'winner': None

    }


def print_board(board):
    """Prints the current state of the board for debugging."""
    print("\nCurrent Board State:")
    for row in board:
        print(' '.join(['⚫' if cell == 1 else '⚪' if cell == 2 else '.' for cell in row]))
    print()

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

@app.route('/')
def index():
    """Displays the starting page."""
    session.clear()  # Clear any existing session data before starting a new games
    return render_template('start.html')

@app.route('/new_game')
def new_game():
    """Starts a new game and redirects to the game page."""
    game_id = str(uuid.uuid4())  # Generate a unique game ID
    games[game_id] = initialize_game()  # Store the new game state
    return redirect(url_for('game', game_id=game_id))  # Redirect with game_id in the URL

# @app.route('/game')
# def game():
#     global rotation_required, current_player, game_over, winner
#     print_board()  # Print the board for debugging
#     return render_template(
#         'board.html',
#         board=board,
#         enumerate=enumerate,
#         rotation_required=rotation_required,
#         current_player=current_player,
#         game_over=game_over,
#         winner=winner
#     )

@app.route('/game/<game_id>')
def game(game_id):
    """Displays the game board for a specific game."""
    if game_id not in games:
        return redirect(url_for('index'))  # Redirect to start if game ID is invalid

    game_state = games[game_id]
    print_board(game_state['board'])
    return render_template(
        'board.html',
        game_id=game_id,
        enumerate=enumerate,
        board=game_state['board'],
        rotation_required=game_state['rotation_required'],
        current_player=game_state['current_player'],
        game_over=game_state['game_over'],
        winner=game_state['winner']
    )
# @app.route('/move', methods=['POST'])
# def move():
#     global board, rotation_required, current_player, game_over, winner
#
#     # Prevent marble placement if a rotation is required or game is over
#     if rotation_required or game_over:
#         return redirect(url_for('game'))
#
#     row = int(request.form['row'])
#     col = int(request.form['col'])
#
#     # Place the player's marble if the spot is empty
#     if board[row][col] == 0:
#         board[row][col] = current_player
#         rotation_required = True  # Require rotation after placing the marble
#
#         # Check if the move results in a win or draw
#         result = check_winner()
#         if result:
#             game_over = True
#             winner = result
#             print(f"Game Over! Winner: {winner}")
#             return redirect(url_for('game'))
#
#     return redirect(url_for('game'))

@app.route('/move/<game_id>', methods=['POST'])
def move(game_id):
    """Handles placing a marble on the board."""
    if game_id not in games:
        return redirect(url_for('index'))

    game_state = games[game_id]

    print_board(game_state['board'])

    board = game_state['board']
    current_player = game_state['current_player']

    row = int(request.form['row'])
    col = int(request.form['col'])

    # Place the player's marble if the spot is empty and the game is not over
    if not game_state['game_over'] and board[row][col] == 0:
        board[row][col] = current_player
        game_state['rotation_required'] = True  # Require rotation after placing the marble

        # Check for a winner or draw
        result = check_winner(board)
        if result:
            game_state['game_over'] = True
            game_state['winner'] = result
        # else:
        #     # Switch player if the game is not over
        #     game_state['current_player'] = 2 if current_player == 1 else 1

    return redirect(url_for('game', game_id=game_id))

# @app.route('/rotate', methods=['POST'])
# def rotate():
#     global board, rotation_required, current_player, game_over, winner
#
#     # Allow rotation only if it is required and the game is not over
#     if not rotation_required or game_over:
#         return redirect(url_for('game'))
#
#     quadrant = int(request.form['quadrant'])  # 1 to 4
#     direction = request.form['direction']  # 'cw' or 'ccw'
#
#     # Extract the corresponding 3x3 subgrid
#     start_row = 0 if quadrant in [1, 2] else 3
#     start_col = 0 if quadrant in [1, 3] else 3
#
#     subgrid = [row[start_col:start_col + 3] for row in board[start_row:start_row + 3]]
#
#     # Rotate the subgrid
#     if direction == 'cw':
#         subgrid = list(zip(*subgrid[::-1]))
#     else:
#         subgrid = list(zip(*subgrid))[::-1]
#
#     # Update the board with the rotated subgrid
#     for i in range(3):
#         for j in range(3):
#             board[start_row + i][start_col + j] = subgrid[i][j]
#
#     rotation_required = False  # Reset rotation requirement after a valid rotation
#
#     # Check if the rotation results in a win or draw
#     result = check_winner()
#     if result:
#         game_over = True
#         winner = result
#         print(f"Game Over! Winner: {winner}")
#         return redirect(url_for('game'))
#
#     # Switch to the next player
#     current_player = 2 if current_player == 1 else 1
#
#     return redirect(url_for('game'))

@app.route('/rotate/<game_id>', methods=['POST'])
def rotate(game_id):
    """Handles rotating a quadrant."""
    if game_id not in games:
        return redirect(url_for('index'))

    game_state = games[game_id]

    print_board(game_state['board'])

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

    # After rotation, allow the player to place a marble
    return redirect(url_for('game', game_id=game_id))


# @app.route('/reset')
# def reset():
#     global board, current_player, game_over, winner
#     board = [[0 for _ in range(6)] for _ in range(6)]  # Reset the board
#     current_player = 1  # Set the starting player
#     game_over = False
#     winner = None
#     return redirect(url_for('game'))

@app.route('/reset/<game_id>')
def reset(game_id):
    """Resets the game state and redirects to the game page."""
    if game_id in games:
        games[game_id] = initialize_game()  # Reset the specific game
    return redirect(url_for('game', game_id=game_id))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='12203', debug=True)
