import streamlit as st
import random
import numpy as np
from PIL import Image, ImageDraw
import io
import base64

# Set page config
st.set_page_config(
    page_title="Streamlit Ludo Game",
    page_icon="🎲",
    layout="wide"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem !important;
        font-weight: 700 !important;
        color: #4527A0 !important;
        text-align: center !important;
        margin-bottom: 20px !important;
    }
    .player-box {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 20px;
    }
    .active-player {
        background-color: #e8f0fe;
        border: 2px solid #1967D2;
    }
    .dice {
        font-size: 4rem;
        text-align: center;
    }
    .instructions {
        background-color: #f9f9f9;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    .winner-text {
        font-size: 2rem;
        font-weight: 700;
        color: #4CAF50;
        text-align: center;
        margin: 20px 0;
    }
    .notification {
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
        text-align: center;
    }
    .info {
        background-color: #e3f2fd;
        color: #0d47a1;
    }
    .success {
        background-color: #e8f5e9;
        color: #2e7d32;
    }
    .warning {
        background-color: #fff8e1;
        color: #ff8f00;
    }
    .colored-circle {
        display: inline-block;
        height: 15px;
        width: 15px;
        border-radius: 50%;
        margin-right: 5px;
    }
    .board-container {
        display: flex;
        justify-content: center;
        margin: 20px 0;
    }
</style>
""", unsafe_allow_html=True)

# Constants for the game
PLAYER_COLORS = ['#FF0000', '#00FF00', '#0000FF', '#FFFF00']  # Red, Green, Blue, Yellow
PLAYER_NAMES = ['Red', 'Green', 'Blue', 'Yellow']
HOME_POSITIONS = {
    'Red': [(1, 1), (1, 2), (2, 1), (2, 2)],
    'Green': [(1, 13), (1, 14), (2, 13), (2, 14)],
    'Blue': [(13, 1), (13, 2), (14, 1), (14, 2)],
    'Yellow': [(13, 13), (13, 14), (14, 13), (14, 14)]
}
START_POSITIONS = {
    'Red': (2, 7),
    'Green': (7, 2),
    'Blue': (12, 7),
    'Yellow': (7, 12)
}
PATH = {
    'Red': [
        (2, 7), (3, 7), (4, 7), (5, 7), (6, 7), 
        (7, 6), (7, 5), (7, 4), (7, 3), (7, 2), 
        (7, 1), (8, 1), (9, 1), 
        (9, 2), (9, 3), (9, 4), (9, 5), (9, 6), 
        (10, 7), (11, 7), (12, 7), (13, 7), (14, 7), 
        (14, 8), (14, 9), 
        (13, 9), (12, 9), (11, 9), (10, 9), (9, 9), 
        (9, 10), (9, 11), (9, 12), (9, 13), (9, 14), 
        (8, 14), (7, 14), 
        (7, 13), (7, 12), (7, 11), (7, 10), (7, 9), 
        (6, 8), (5, 8), (4, 8), (3, 8), (2, 8), 
        (1, 8), (1, 7),
        # Final stretch for Red
        (2, 7), (3, 7), (4, 7), (5, 7), (6, 7), (7, 7), (8, 7)
    ],
    'Green': [
        (7, 2), (7, 3), (7, 4), (7, 5), (7, 6), 
        (8, 7), (9, 7), (10, 7), (11, 7), (12, 7), 
        (13, 7), (13, 8), (13, 9), 
        (12, 9), (11, 9), (10, 9), (9, 9), (8, 9), 
        (7, 10), (7, 11), (7, 12), (7, 13), (7, 14), 
        (6, 14), (5, 14), 
        (5, 13), (5, 12), (5, 11), (5, 10), (5, 9), 
        (4, 9), (3, 9), (2, 9), (1, 9), (0, 9), 
        (0, 8), (0, 7), 
        (1, 7), (2, 7), (3, 7), (4, 7), (5, 7), 
        (6, 6), (6, 5), (6, 4), (6, 3), (6, 2), 
        (6, 1), (7, 1),
        # Final stretch for Green
        (7, 2), (7, 3), (7, 4), (7, 5), (7, 6), (7, 7), (7, 8)
    ],
    'Blue': [
        (12, 7), (11, 7), (10, 7), (9, 7), (8, 7), 
        (7, 8), (7, 9), (7, 10), (7, 11), (7, 12), 
        (7, 13), (6, 13), (5, 13), 
        (5, 12), (5, 11), (5, 10), (5, 9), (5, 8), 
        (4, 7), (3, 7), (2, 7), (1, 7), (0, 7), 
        (0, 6), (0, 5), 
        (1, 5), (2, 5), (3, 5), (4, 5), (5, 5), 
        (5, 4), (5, 3), (5, 2), (5, 1), (5, 0), 
        (6, 0), (7, 0), 
        (7, 1), (7, 2), (7, 3), (7, 4), (7, 5), 
        (8, 6), (9, 6), (10, 6), (11, 6), (12, 6), 
        (13, 6), (13, 7),
        # Final stretch for Blue
        (12, 7), (11, 7), (10, 7), (9, 7), (8, 7), (7, 7), (6, 7)
    ],
    'Yellow': [
        (7, 12), (7, 11), (7, 10), (7, 9), (7, 8), 
        (6, 7), (5, 7), (4, 7), (3, 7), (2, 7), 
        (1, 7), (1, 6), (1, 5), 
        (2, 5), (3, 5), (4, 5), (5, 5), (6, 5), 
        (7, 4), (7, 3), (7, 2), (7, 1), (7, 0), 
        (8, 0), (9, 0), 
        (9, 1), (9, 2), (9, 3), (9, 4), (9, 5), 
        (10, 5), (11, 5), (12, 5), (13, 5), (14, 5), 
        (14, 6), (14, 7), 
        (13, 7), (12, 7), (11, 7), (10, 7), (9, 7), 
        (8, 8), (8, 9), (8, 10), (8, 11), (8, 12), 
        (8, 13), (7, 13),
        # Final stretch for Yellow
        (7, 12), (7, 11), (7, 10), (7, 9), (7, 8), (7, 7), (7, 6)
    ]
}

# Dice faces
DICE_FACES = {
    1: "⚀",
    2: "⚁",
    3: "⚂",
    4: "⚃",
    5: "⚄",
    6: "⚅"
}

# Function to generate the Ludo board
def create_board_image():
    # Create a new image with white background
    width, height = 600, 600
    image = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    
    # Define cell size
    cell_size = width // 15
    
    # Draw grid lines
    for i in range(16):
        # Vertical lines
        draw.line([(i * cell_size, 0), (i * cell_size, height)], fill=(200, 200, 200), width=1)
        # Horizontal lines
        draw.line([(0, i * cell_size), (width, i * cell_size)], fill=(200, 200, 200), width=1)
    
    # Draw colored home areas
    # Red (top-left)
    draw.rectangle([(0, 0), (6 * cell_size, 6 * cell_size)], fill=(255, 200, 200))
    draw.rectangle([(cell_size, cell_size), (5 * cell_size, 5 * cell_size)], fill=(255, 255, 255))
    draw.rectangle([(cell_size, cell_size), (3 * cell_size, 3 * cell_size)], fill=(255, 0, 0))
    
    # Green (top-right)
    draw.rectangle([(9 * cell_size, 0), (15 * cell_size, 6 * cell_size)], fill=(200, 255, 200))
    draw.rectangle([(10 * cell_size, cell_size), (14 * cell_size, 5 * cell_size)], fill=(255, 255, 255))
    draw.rectangle([(12 * cell_size, cell_size), (14 * cell_size, 3 * cell_size)], fill=(0, 255, 0))
    
    # Blue (bottom-left)
    draw.rectangle([(0, 9 * cell_size), (6 * cell_size, 15 * cell_size)], fill=(200, 200, 255))
    draw.rectangle([(cell_size, 10 * cell_size), (5 * cell_size, 14 * cell_size)], fill=(255, 255, 255))
    draw.rectangle([(cell_size, 12 * cell_size), (3 * cell_size, 14 * cell_size)], fill=(0, 0, 255))
    
    # Yellow (bottom-right)
    draw.rectangle([(9 * cell_size, 9 * cell_size), (15 * cell_size, 15 * cell_size)], fill=(255, 255, 200))
    draw.rectangle([(10 * cell_size, 10 * cell_size), (14 * cell_size, 14 * cell_size)], fill=(255, 255, 255))
    draw.rectangle([(12 * cell_size, 12 * cell_size), (14 * cell_size, 14 * cell_size)], fill=(255, 255, 0))
    
    # Draw central home area
    draw.rectangle([(6 * cell_size, 6 * cell_size), (9 * cell_size, 9 * cell_size)], fill=(230, 230, 230))
    
    # Draw paths
    # Horizontal paths
    draw.rectangle([(1 * cell_size, 7 * cell_size), (6 * cell_size, 8 * cell_size)], fill=(255, 200, 200))  # Red
    draw.rectangle([(9 * cell_size, 7 * cell_size), (14 * cell_size, 8 * cell_size)], fill=(255, 255, 200))  # Yellow
    
    # Vertical paths
    draw.rectangle([(7 * cell_size, 1 * cell_size), (8 * cell_size, 6 * cell_size)], fill=(200, 255, 200))  # Green
    draw.rectangle([(7 * cell_size, 9 * cell_size), (8 * cell_size, 14 * cell_size)], fill=(200, 200, 255))  # Blue
    
    # Draw safe spots
    safe_spots = [(2, 7), (7, 2), (12, 7), (7, 12)]
    for spot in safe_spots:
        x, y = spot
        draw.ellipse([(x * cell_size, y * cell_size), ((x + 1) * cell_size, (y + 1) * cell_size)], fill=(220, 220, 220))

    # Draw home stretch paths
    # Red
    for i in range(2, 8):
        draw.rectangle([(i * cell_size, 7 * cell_size), ((i + 1) * cell_size, 8 * cell_size)], fill=(255, 100, 100))
    
    # Green
    for i in range(2, 8):
        draw.rectangle([(7 * cell_size, i * cell_size), (8 * cell_size, (i + 1) * cell_size)], fill=(100, 255, 100))

    # Blue
    for i in range(7, 13):
        draw.rectangle([((14 - i) * cell_size, 7 * cell_size), ((15 - i) * cell_size, 8 * cell_size)], fill=(100, 100, 255))
        
    # Yellow
    for i in range(7, 13):
        draw.rectangle([(7 * cell_size, (14 - i) * cell_size), (8 * cell_size, (15 - i) * cell_size)], fill=(255, 255, 100))
    
    # Convert the image to bytes
    img_bytes = io.BytesIO()
    image.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    return img_bytes.getvalue()

# Function to draw player tokens on the board
def draw_player_tokens(board_image_bytes, player_tokens):
    # Convert bytes back to image
    img_bytes = io.BytesIO(board_image_bytes)
    image = Image.open(img_bytes)
    draw = ImageDraw.Draw(image)
    
    cell_size = image.width // 15
    token_radius = cell_size // 3
    
    # Draw each player's tokens on the board
    for player_color, tokens in player_tokens.items():
        color_rgb = tuple(int(player_color[1:][i:i+2], 16) for i in (0, 2, 4))  # Convert hex to RGB
        
        for token_idx, position in enumerate(tokens):
            # Skip tokens that are still in the starting position (-1)
            if position == -1:
                # Draw in home area
                if player_color == '#FF0000':  # Red
                    home_pos = HOME_POSITIONS['Red'][token_idx]
                elif player_color == '#00FF00':  # Green
                    home_pos = HOME_POSITIONS['Green'][token_idx]
                elif player_color == '#0000FF':  # Blue
                    home_pos = HOME_POSITIONS['Blue'][token_idx]
                elif player_color == '#FFFF00':  # Yellow
                    home_pos = HOME_POSITIONS['Yellow'][token_idx]
                
                x, y = home_pos
                center_x = (x + 0.5) * cell_size
                center_y = (y + 0.5) * cell_size
                
                draw.ellipse([
                    (center_x - token_radius, center_y - token_radius),
                    (center_x + token_radius, center_y + token_radius)
                ], fill=color_rgb, outline=(0, 0, 0))
                
                draw.text((center_x - token_radius // 3, center_y - token_radius // 3), str(token_idx + 1), fill=(255, 255, 255))
                
            elif position >= 0:
                # Get the corresponding player path
                if player_color == '#FF0000':  # Red
                    path = PATH['Red']
                elif player_color == '#00FF00':  # Green
                    path = PATH['Green']
                elif player_color == '#0000FF':  # Blue
                    path = PATH['Blue']
                elif player_color == '#FFFF00':  # Yellow
                    path = PATH['Yellow']
                
                # Make sure position is within path range
                if position < len(path):
                    # Get the coordinates from the path
                    x, y = path[position]
                    
                    # Calculate the center of the cell
                    center_x = (x + 0.5) * cell_size
                    center_y = (y + 0.5) * cell_size
                    
                    # Draw the token as a circle
                    draw.ellipse([
                        (center_x - token_radius, center_y - token_radius),
                        (center_x + token_radius, center_y + token_radius)
                    ], fill=color_rgb, outline=(0, 0, 0))
                    
                    # Add token number
                    draw.text((center_x - token_radius // 3, center_y - token_radius // 3), str(token_idx + 1), fill=(255, 255, 255))
    
    # Convert the image back to bytes
    img_bytes = io.BytesIO()
    image.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    return img_bytes.getvalue()

# Initialize the game state
def initialize_game_state():
    if 'player_names' not in st.session_state:
        st.session_state.player_names = []
    if 'num_players' not in st.session_state:
        st.session_state.num_players = 0
    if 'game_started' not in st.session_state:
        st.session_state.game_started = False
    if 'current_player' not in st.session_state:
        st.session_state.current_player = 0
    if 'dice_value' not in st.session_state:
        st.session_state.dice_value = 0
    if 'player_tokens' not in st.session_state:
        st.session_state.player_tokens = {}
    if 'game_over' not in st.session_state:
        st.session_state.game_over = False
    if 'winner' not in st.session_state:
        st.session_state.winner = None
    if 'token_moved' not in st.session_state:
        st.session_state.token_moved = False
    if 'show_dice' not in st.session_state:
        st.session_state.show_dice = False
    if 'notification' not in st.session_state:
        st.session_state.notification = None
    if 'notification_type' not in st.session_state:
        st.session_state.notification_type = "info"
    
# Start a new game
def start_game():
    num_players = st.session_state.num_players_input
    player_names = []
    
    for i in range(num_players):
        name = st.session_state.get(f"player_{i}_name", f"Player {i+1}")
        if not name:
            name = f"Player {i+1}"
        player_names.append(name)
    
    st.session_state.player_names = player_names
    st.session_state.num_players = num_players
    st.session_state.current_player = 0
    st.session_state.game_started = True
    
    # Initialize player tokens
    # Each player has 4 tokens
    # -1 means the token is in the starting area
    # 0+ means the position in the player's path
    st.session_state.player_tokens = {}
    
    for i in range(num_players):
        player_color = PLAYER_COLORS[i]
        st.session_state.player_tokens[player_color] = [-1, -1, -1, -1]
    
    st.session_state.notification = "Game started! Roll the dice to begin."
    st.session_state.notification_type = "info"

# Roll the dice
def roll_dice():
    if st.session_state.token_moved:
        st.session_state.notification = "You already moved a token. Next player's turn."
        st.session_state.notification_type = "warning"
        return
        
    # Roll the dice
    st.session_state.dice_value = random.randint(1, 6)
    st.session_state.show_dice = True
    st.session_state.token_moved = False
    
    # Check if the player can move any tokens
    current_player = st.session_state.current_player
    player_color = PLAYER_COLORS[current_player]
    player_tokens = st.session_state.player_tokens[player_color]
    
    can_move = False
    
    for token_idx, position in enumerate(player_tokens):
        # If token is in starting area, need a 6 to move out
        if position == -1:
            if st.session_state.dice_value == 6:
                can_move = True
                break
        else:
            # Check if token can move dice_value steps without going past the end
            if position + st.session_state.dice_value < len(PATH[PLAYER_NAMES[current_player]]):
                can_move = True
                break
    
    if not can_move:
        st.session_state.notification = f"No valid moves. Next player's turn."
        st.session_state.notification_type = "warning"
        st.session_state.token_moved = True  # Mark as moved to allow next player
    else:
        st.session_state.notification = f"Select a token to move."
        st.session_state.notification_type = "info"

# Move a token
def move_token(token_idx):
    if st.session_state.token_moved:
        st.session_state.notification = "You already moved a token. Next player's turn."
        st.session_state.notification_type = "warning"
        return
        
    current_player = st.session_state.current_player
    player_color = PLAYER_COLORS[current_player]
    player_name = PLAYER_NAMES[current_player]
    
    # Current position of the selected token
    position = st.session_state.player_tokens[player_color][token_idx]
    
    # If token is in starting area, need a 6 to move out
    if position == -1:
        if st.session_state.dice_value == 6:
            # Move to starting position on the board
            st.session_state.player_tokens[player_color][token_idx] = 0
            st.session_state.notification = f"Token {token_idx + 1} moved to the starting position."
            st.session_state.notification_type = "success"
            st.session_state.token_moved = True
        else:
            st.session_state.notification = f"Need a 6 to move token {token_idx + 1} out of home."
            st.session_state.notification_type = "warning"
            return
    else:
        # Check if token can move dice_value steps without going past the end
        new_position = position + st.session_state.dice_value
        
        if new_position < len(PATH[player_name]):
            # Move the token
            st.session_state.player_tokens[player_color][token_idx] = new_position
            
            # Check if the token reached the end
            if new_position == len(PATH[player_name]) - 1:
                st.session_state.notification = f"Token {token_idx + 1} reached home! 🎉"
                st.session_state.notification_type = "success"
                
                # Check if all tokens have reached home
                all_home = all(pos == len(PATH[player_name]) - 1 for pos in st.session_state.player_tokens[player_color])
                if all_home:
                    st.session_state.game_over = True
                    st.session_state.winner = st.session_state.player_names[current_player]
            else:
                st.session_state.notification = f"Token {token_idx + 1} moved to position {new_position}."
                st.session_state.notification_type = "success"
            
            st.session_state.token_moved = True
        else:
            st.session_state.notification = f"Cannot move token {token_idx + 1} beyond the end."
            st.session_state.notification_type = "warning"
            return

# Next player's turn
def next_turn():
    if not st.session_state.token_moved and st.session_state.dice_value != 6:
        st.session_state.notification = "You must roll the dice and move a token."
        st.session_state.notification_type = "warning"
        return
        
    if st.session_state.dice_value == 6 and not st.session_state.token_moved:
        st.session_state.notification = "You rolled a 6. You must move a token."
        st.session_state.notification_type = "warning"
        return
    
    # If player rolled a 6, they get another turn
    if st.session_state.dice_value == 6 and st.session_state.token_moved:
        st.session_state.notification = "You rolled a 6! Roll again."
        st.session_state.notification_type = "success"
        # Reset for next roll but don't change player
        st.session_state.dice_value = 0
        st.session_state.show_dice = False
        st.session_state.token_moved = False
        return
    
    # Move to next player
    st.session_state.current_player = (st.session_state.current_player + 1) % st.session_state.num_players
    st.session_state.dice_value = 0
    st.session_state.show_dice = False
    st.session_state.token_moved = False
    st.session_state.notification = f"{st.session_state.player_names[st.session_state.current_player]}'s turn. Roll the dice."
    st.session_state.notification_type = "info"

# Restart the game
def restart_game():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    initialize_game_state()

# Main app
def main():
    # Initialize session state if not already done
    initialize_game_state()
    
    # Title
    st.markdown("<h1 class='main-header'>🎲 Streamlit Ludo Game</h1>", unsafe_allow_html=True)
    
    # Game setup
    if not st.session_state.game_started:
        st.markdown("<div class='instructions'>", unsafe_allow_html=True)
        st.markdown("### Welcome to Ludo!")
        st.markdown("""
        Ludo is a classic board game where players race their four tokens from start to finish according to dice rolls.
        
        **Rules:**
        - Each player has 4 tokens
        - Roll a 6 to move a token out of the starting area
        - Move your tokens around the board based on dice rolls
        - Roll a 6 to get an extra turn
        - The first player to get all their tokens to the center wins!
        """)
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("### Game Setup")
        
        # Player selection
        col1, col2 = st.columns([1, 1])
        with col1:
            st.session_state.num_players_input = st.slider("Number of Players", min_value=2, max_value=4, value=4)
        
        # Player names
        st.markdown("### Enter Player Names")
        cols = st.columns(2)
        for i in range(st.session_state.num_players_input):
            color_name = PLAYER_NAMES[i]
            color_hex = PLAYER_COLORS[i]
            
            with cols[i % 2]:
                # Display colored circle with player info using markdown
                st.markdown(f"<div><span class='colored-circle' style='background-color: {color_hex};'></span> Player {i+1} ({color_name})</div>", unsafe_allow_html=True)
                
                # Input for player name
                st.text_input(
                    f"Enter name for Player {i+1}",
                    key=f"player_{i}_name",
                    value=f"Player {i+1}"
                )
        
        # Start the game
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("Start Game", use_container_width=True):
                start_game()
    
    # Game board and controls
    else:
        # Display notification if any
        if st.session_state.notification:
            notification_type = st.session_state.notification_type
            st.markdown(f"<div class='notification {notification_type}'>{st.session_state.notification}</div>", unsafe_allow_html=True)
        
        # Display winner if game is over
        if st.session_state.game_over:
            st.markdown(f"<h2 class='winner-text'>🏆 {st.session_state.winner} wins! 🏆</h2>", unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("Play Again", use_container_width=True):
                    restart_game()
                
            return
        
        # Game controls
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Create the base board
            board_image = create_board_image()
            
            # Draw tokens on the board
            board_with_tokens = draw_player_tokens(board_image, st.session_state.player_tokens)
            
            # Convert to base64 for displaying
            encoded_image = base64.b64encode(board_with_tokens).decode()
            
            # Display the board
            st.markdown(
                f'<div class="board-container"><img src="data:image/png;base64,{encoded_image}" style="max-width: 100%; border: 3px solid #333; border-radius: 10px;" /></div>',
                unsafe_allow_html=True
            )
            
        with col2:
            # Display current player
            current_player_idx = st.session_state.current_player
            player_name = st.session_state.player_names[current_player_idx]
            player_color = PLAYER_COLORS[current_player_idx]
            
            st.markdown(f"## Current Player")
            st.markdown(f"<div class='player-box active-player'><span class='colored-circle' style='background-color: {player_color};'></span> <b>{player_name}</b></div>", unsafe_allow_html=True)
            
            # Dice roll
            if st.session_state.show_dice:
                dice_face = DICE_FACES[st.session_state.dice_value]
                st.markdown(f"<div class='dice'>{dice_face}</div>", unsafe_allow_html=True)
                st.markdown(f"<p style='text-align: center;'>You rolled a {st.session_state.dice_value}</p>", unsafe_allow_html=True)
            
            # Game controls
            st.markdown("### Game Controls")
            
            # Roll dice button
            if not st.session_state.token_moved:
                if st.button("Roll Dice", use_container_width=True):
                    roll_dice()
            
            # Token selection
            if st.session_state.show_dice and not st.session_state.token_moved:
                st.markdown("### Select Token to Move")
                
                # Get current player's tokens
                current_player_color = PLAYER_COLORS[current_player_idx]
                tokens = st.session_state.player_tokens[current_player_color]
                
                # Create token grid
                cols = st.columns(2)
                
                for i, position in enumerate(tokens):
                    # Only show buttons for tokens that can be moved
                    # If token is in home (-1), need a 6 to move out
                    # If token is on board, can't move past the end
                    can_move = False
                    button_col = cols[i % 2]
                    
                    if position == -1 and st.session_state.dice_value == 6:
                        can_move = True
                        label = f"Token {i+1} (Home)"
                    elif position >= 0 and position + st.session_state.dice_value < len(PATH[PLAYER_NAMES[current_player_idx]]):
                        can_move = True
                        if position == len(PATH[PLAYER_NAMES[current_player_idx]]) - st.session_state.dice_value - 1:
                            label = f"Token {i+1} (To Finish!)"
                        else:
                            label = f"Token {i+1} (Pos: {position})"
                    else:
                        label = f"Token {i+1} (Can't Move)"
                    
                    with button_col:
                        if can_move:
                            if st.button(label, key=f"token_{i}", use_container_width=True):
                                move_token(i)
                        else:
                            st.button(label, key=f"token_{i}", use_container_width=True, disabled=True)
            
            # Next turn button
            if st.session_state.token_moved or (st.session_state.show_dice and not any(pos + st.session_state.dice_value < len(PATH[PLAYER_NAMES[current_player_idx]]) for pos in st.session_state.player_tokens[PLAYER_COLORS[current_player_idx]] if pos >= 0) and not (st.session_state.dice_value == 6 and -1 in st.session_state.player_tokens[PLAYER_COLORS[current_player_idx]])):
                if st.button("Next Turn", use_container_width=True):
                    next_turn()
            
            # Restart game button
            st.markdown("---")
            if st.button("Restart Game", use_container_width=True):
                restart_game()
            
            # Game stats
            st.markdown("### Game Statistics")
            
            # Show tokens in home and finished for each player
            for i in range(st.session_state.num_players):
                player_name = st.session_state.player_names[i]
                player_color = PLAYER_COLORS[i]
                tokens = st.session_state.player_tokens.get(player_color, [-1, -1, -1, -1])
                
                tokens_home = sum(1 for pos in tokens if pos == -1)
                tokens_finished = sum(1 for pos in tokens if pos == len(PATH[PLAYER_NAMES[i]]) - 1)
                tokens_playing = 4 - tokens_home - tokens_finished
                
                # Create progress bar
                progress_html = f"""
                <div style="margin-bottom: 10px;">
                    <div style="display: flex; align-items: center; margin-bottom: 5px;">
                        <span class='colored-circle' style='background-color: {player_color};'></span>
                        <b>{player_name}</b>
                    </div>
                    <div style="display: flex; width: 100%; height: 20px; border-radius: 5px; overflow: hidden;">
                        <div style="width: {tokens_home/4*100}%; background-color: #f0f0f0; display: flex; justify-content: center; align-items: center;">
                            {tokens_home}
                        </div>
                        <div style="width: {tokens_playing/4*100}%; background-color: {player_color}; display: flex; justify-content: center; align-items: center; color: white;">
                            {tokens_playing}
                        </div>
                        <div style="width: {tokens_finished/4*100}%; background-color: #4CAF50; display: flex; justify-content: center; align-items: center; color: white;">
                            {tokens_finished}
                        </div>
                    </div>
                    <div style="display: flex; width: 100%; font-size: 0.8em; margin-top: 2px;">
                        <div style="width: {tokens_home/4*100}%;">Home</div>
                        <div style="width: {tokens_playing/4*100}%;">Playing</div>
                        <div style="width: {tokens_finished/4*100}%;">Finished</div>
                    </div>
                </div>
                """
                st.markdown(progress_html, unsafe_allow_html=True)

# Run the main app
if __name__ == "__main__":
    main()
