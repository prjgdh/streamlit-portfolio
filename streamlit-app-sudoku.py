import streamlit as st
import numpy as np
import time
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import base64
from io import BytesIO

# Set page config
st.set_page_config(
    page_title="Streamoku - Sudoku Solver & Game",
    page_icon="🧩",
    layout="wide"
)

# Custom CSS styles
st.markdown("""
<style>
    .main-header {
        font-size: 3rem !important;
        font-weight: 700 !important;
        color: #4527A0 !important;
        text-align: center !important;
        margin-bottom: 20px !important;
    }
    .subheader {
        font-size: 1.5rem !important;
        font-weight: 500 !important;
        color: #5E35B1 !important;
        text-align: center !important;
        margin-bottom: 30px !important;
    }
    .stButton>button {
        background-color: #5E35B1;
        color: white;
        border: none;
        font-weight: bold;
        padding: 0.5rem 1rem;
        border-radius: 0.3rem;
    }
    .stButton>button:hover {
        background-color: #4527A0;
    }
    .description {
        text-align: center;
        padding: 10px;
        border-radius: 5px;
        background-color: #F3E5F5;
        margin-bottom: 20px;
    }
    .small-text {
        font-size: 0.8rem;
        color: #757575;
    }
    .solution-box {
        background-color: #E8EAF6;
        padding: 20px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    .red-text {
        color: #D32F2F;
        font-weight: bold;
    }
    .green-text {
        color: #388E3C;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# App title
st.markdown("<h1 class='main-header'>🧩 Streamoku</h1>", unsafe_allow_html=True)
st.markdown("<h2 class='subheader'>A Streamlit Sudoku Solver & Game</h2>", unsafe_allow_html=True)

# Function to check if a number can be placed in a given position
def is_valid(grid, row, col, num):
    # Check row
    for x in range(9):
        if grid[row][x] == num:
            return False

    # Check column
    for x in range(9):
        if grid[x][col] == num:
            return False

    # Check 3x3 box
    start_row, start_col = 3 * (row // 3), 3 * (col // 3)
    for i in range(3):
        for j in range(3):
            if grid[i + start_row][j + start_col] == num:
                return False

    return True

# Function to solve Sudoku using backtracking
def solve_sudoku(grid):
    empty = find_empty(grid)
    if not empty:
        return True
    
    row, col = empty
    
    for num in range(1, 10):
        if is_valid(grid, row, col, num):
            grid[row][col] = num
            
            if solve_sudoku(grid):
                return True
            
            grid[row][col] = 0
    
    return False

# Function to find an empty cell
def find_empty(grid):
    for i in range(9):
        for j in range(9):
            if grid[i][j] == 0:
                return (i, j)
    return None

# Function to generate a Sudoku puzzle
def generate_sudoku(difficulty):
    # Start with a solved Sudoku puzzle
    grid = [[0 for _ in range(9)] for _ in range(9)]
    solve_sudoku(grid)
    
    # Keep track of the solution
    solution = [row[:] for row in grid]
    
    # Remove numbers based on difficulty
    if difficulty == "Easy":
        squares_to_remove = 30
    elif difficulty == "Medium":
        squares_to_remove = 40
    elif difficulty == "Hard":
        squares_to_remove = 50
    else:  # Very Hard
        squares_to_remove = 55
    
    # Randomly remove numbers
    cells = [(i, j) for i in range(9) for j in range(9)]
    np.random.shuffle(cells)
    
    for i, j in cells[:squares_to_remove]:
        grid[i][j] = 0
    
    return grid, solution

# Function to create an image of the Sudoku grid
def create_sudoku_image(grid, solution=None, highlight_cells=None):
    cell_size = 50
    grid_size = cell_size * 9
    image = Image.new('RGB', (grid_size, grid_size), color='white')
    draw = ImageDraw.Draw(image)
    
    try:
        # Try to load a nice font, fall back to default if not available
        font = ImageFont.truetype("Arial", 24)
    except IOError:
        font = ImageFont.load_default()
    
    # Draw grid lines
    for i in range(10):
        line_width = 3 if i % 3 == 0 else 1
        # Horizontal lines
        draw.line([(0, i * cell_size), (grid_size, i * cell_size)], fill='black', width=line_width)
        # Vertical lines
        draw.line([(i * cell_size, 0), (i * cell_size, grid_size)], fill='black', width=line_width)
    
    # Fill in numbers
    for i in range(9):
        for j in range(9):
            if grid[i][j] != 0:
                # Determine text color
                text_color = 'black'
                if highlight_cells and (i, j) in highlight_cells:
                    text_color = 'red'  # Highlight incorrect cells
                elif solution and grid[i][j] == solution[i][j]:
                    text_color = 'blue'  # Correct numbers from solution
                    
                # Draw number
                x = j * cell_size + cell_size // 3
                y = i * cell_size + cell_size // 6
                draw.text((x, y), str(grid[i][j]), fill=text_color, font=font)
    
    # Convert to base64 for displaying in Streamlit
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}"

# Function to check if a Sudoku grid is solved correctly
def is_solved(grid):
    # Check if grid is filled (no zeros)
    for i in range(9):
        for j in range(9):
            if grid[i][j] == 0:
                return False
    
    # Check rows
    for row in grid:
        if sorted(row) != list(range(1, 10)):
            return False
    
    # Check columns
    for j in range(9):
        col = [grid[i][j] for i in range(9)]
        if sorted(col) != list(range(1, 10)):
            return False
    
    # Check 3x3 boxes
    for box_i in range(3):
        for box_j in range(3):
            box = []
            for i in range(3):
                for j in range(3):
                    box.append(grid[3*box_i+i][3*box_j+j])
            if sorted(box) != list(range(1, 10)):
                return False
    
    return True

# Function to convert string input to grid
def parse_grid_input(input_str):
    # Remove any whitespace and split into rows
    rows = input_str.strip().split('\n')
    
    # Check if there are 9 rows
    if len(rows) != 9:
        return None, "Input must have exactly 9 rows."
    
    grid = []
    for row in rows:
        # Remove any spaces or other separators
        row = ''.join(c for c in row if c.isdigit() or c in ['.', '0'])
        
        # Replace '.' with '0'
        row = row.replace('.', '0')
        
        # Check if there are 9 columns
        if len(row) != 9:
            return None, f"Each row must have exactly 9 numbers. Row: {row}"
        
        # Convert to integers
        try:
            row_nums = [int(c) for c in row]
            grid.append(row_nums)
        except ValueError:
            return None, "Input must contain only digits 0-9 or dots."
    
    return grid, None

# Navigation
st.sidebar.title("Navigation")
app_mode = st.sidebar.selectbox("Choose Mode", ["Sudoku Solver", "Play Sudoku", "About"])

# Sudoku Solver section
if app_mode == "Sudoku Solver":
    st.markdown("<h3>🔍 Sudoku Solver</h3>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class='description'>
        Enter your Sudoku puzzle below. You can input it in the text area (use 0 or . for empty cells), or select from a provided sample puzzle.
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        input_method = st.radio("Input Method", ["Text Input", "Sample Puzzles"])
        
        if input_method == "Text Input":
            grid_input = st.text_area("Enter your Sudoku puzzle (use 0 or . for empty cells):", 
                                    height=200,
                                    placeholder="5 3 0 0 7 0 0 0 0\n"
                                                "6 0 0 1 9 5 0 0 0\n"
                                                "0 9 8 0 0 0 0 6 0\n"
                                                "8 0 0 0 6 0 0 0 3\n"
                                                "4 0 0 8 0 3 0 0 1\n"
                                                "7 0 0 0 2 0 0 0 6\n"
                                                "0 6 0 0 0 0 2 8 0\n"
                                                "0 0 0 4 1 9 0 0 5\n"
                                                "0 0 0 0 8 0 0 7 9")
            
            # Parse grid input
            if grid_input:
                grid, error_msg = parse_grid_input(grid_input)
                if error_msg:
                    st.error(error_msg)
        else:
            # Sample puzzles
            sample_puzzles = {
                "Easy": [
                    "530070000\n600195000\n098000060\n800060003\n400803001\n700020006\n060000280\n000419005\n000080079"
                ],
                "Medium": [
                    "009000400\n000051070\n000000902\n000030000\n158000000\n607000043\n000300608\n004070031\n000800000"
                ],
                "Hard": [
                    "100007090\n030020008\n009600500\n005300900\n010080002\n600004000\n300000010\n040000007\n007000300"
                ]
            }
            
            difficulty = st.selectbox("Select Difficulty", list(sample_puzzles.keys()))
            selected_puzzle = st.selectbox("Select Puzzle", 
                                        [f"Puzzle {i+1}" for i in range(len(sample_puzzles[difficulty]))],
                                        key="sample_puzzle")
            
            puzzle_idx = int(selected_puzzle.split()[1]) - 1
            grid_input = sample_puzzles[difficulty][puzzle_idx]
            
            # Display the selected puzzle
            st.text_area("Selected Puzzle:", value=grid_input, height=200, disabled=True)
            
            # Parse grid input
            grid, error_msg = parse_grid_input(grid_input)
            if error_msg:
                st.error(error_msg)
    
    with col2:
        if 'grid' in locals() and grid is not None:
            st.markdown("### Preview")
            img_data = create_sudoku_image(grid)
            st.markdown(f"<img src='{img_data}' style='width: 100%;'>", unsafe_allow_html=True)
    
    # Solve button
    if 'grid' in locals() and grid is not None:
        if st.button("Solve Sudoku"):
            # Create a copy of the grid to solve
            solve_grid = [row[:] for row in grid]
            
            # Measure solving time
            start_time = time.time()
            solved = solve_sudoku(solve_grid)
            end_time = time.time()
            
            if solved:
                st.markdown("<h3 class='green-text'>✅ Solution Found!</h3>", unsafe_allow_html=True)
                st.markdown(f"Solved in {end_time - start_time:.4f} seconds")
                
                # Display solution
                st.markdown("### Solution")
                solution_img = create_sudoku_image(solve_grid)
                st.markdown(f"<img src='{solution_img}' style='width: 70%;'>", unsafe_allow_html=True)
                
                # Display solution as text
                st.markdown("### Solution as Text")
                solution_text = "\n".join([" ".join(map(str, row)) for row in solve_grid])
                st.text_area("Copy this solution:", value=solution_text, height=200)
                
            else:
                st.markdown("<h3 class='red-text'>❌ No Solution Found</h3>", unsafe_allow_html=True)
                st.write("This puzzle doesn't have a valid solution. Please check your input.")

# Play Sudoku section
elif app_mode == "Play Sudoku":
    st.markdown("<h3>🎮 Play Sudoku</h3>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class='description'>
        Play a Sudoku game generated with your chosen difficulty level. Click 'New Game' to start!
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize or reset the game
    if "game_grid" not in st.session_state or st.button("New Game"):
        difficulty = st.selectbox("Select Difficulty", ["Easy", "Medium", "Hard", "Very Hard"])
        st.session_state.game_grid, st.session_state.solution = generate_sudoku(difficulty)
        st.session_state.original_grid = [row[:] for row in st.session_state.game_grid]
        st.session_state.game_start_time = time.time()
        st.session_state.game_complete = False
        st.session_state.hints_used = 0
        
        # Rerun to update the UI
        st.experimental_rerun()
    
    # Game interface
    if "game_grid" in st.session_state:
        # Display timer if game is in progress
        if not st.session_state.game_complete:
            elapsed_time = time.time() - st.session_state.game_start_time
            st.markdown(f"### ⏱️ Time: {int(elapsed_time // 60):02d}:{int(elapsed_time % 60):02d}")
        
        col1, col2 = st.columns([3, 2])
        
        with col1:
            # Display the current puzzle as a table for input
            st.markdown("### Your Game")
            
            # Create a DataFrame for the grid
            df = pd.DataFrame(st.session_state.game_grid)
            
            # Allow editing only for cells that were originally empty
            for i in range(9):
                cols = st.columns(9)
                for j in range(9):
                    with cols[j]:
                        if st.session_state.original_grid[i][j] == 0:
                            value = st.number_input("", 
                                                min_value=0, 
                                                max_value=9, 
                                                value=st.session_state.game_grid[i][j],
                                                key=f"cell_{i}_{j}",
                                                label_visibility="collapsed")
                            st.session_state.game_grid[i][j] = value
                        else:
                            st.markdown(f"<h3 style='text-align:center;'>{st.session_state.original_grid[i][j]}</h3>", 
                                      unsafe_allow_html=True)
            
            # Check if the puzzle is solved
            if not st.session_state.game_complete and is_solved(st.session_state.game_grid):
                st.session_state.game_complete = True
                elapsed_time = time.time() - st.session_state.game_start_time
                st.markdown(f"<h2 class='green-text'>🎉 Puzzle Solved!</h2>", unsafe_allow_html=True)
                st.markdown(f"<p>Time taken: {int(elapsed_time // 60):02d}:{int(elapsed_time % 60):02d}</p>", 
                          unsafe_allow_html=True)
                st.markdown(f"<p>Hints used: {st.session_state.hints_used}</p>", unsafe_allow_html=True)
        
        with col2:
            # Hint button
            if not st.session_state.game_complete and st.button("Get Hint"):
                # Find an empty cell
                empty_cells = [(i, j) for i in range(9) for j in range(9) 
                              if st.session_state.game_grid[i][j] == 0]
                
                if empty_cells:
                    # Randomly choose an empty cell
                    i, j = empty_cells[np.random.randint(0, len(empty_cells))]
                    # Fill with correct value
                    st.session_state.game_grid[i][j] = st.session_state.solution[i][j]
                    st.session_state.hints_used += 1
                    st.experimental_rerun()
                else:
                    st.warning("No empty cells left to give hints for!")
            
            # Check progress
            if not st.session_state.game_complete and st.button("Check Progress"):
                incorrect_cells = []
                for i in range(9):
                    for j in range(9):
                        if (st.session_state.game_grid[i][j] != 0 and 
                            st.session_state.game_grid[i][j] != st.session_state.solution[i][j]):
                            incorrect_cells.append((i, j))
                
                if incorrect_cells:
                    st.markdown(f"<p class='red-text'>You have {len(incorrect_cells)} incorrect cells.</p>", 
                              unsafe_allow_html=True)
                else:
                    st.markdown("<p class='green-text'>All filled cells are correct so far!</p>", 
                              unsafe_allow_html=True)
                    
                    # Count remaining cells
                    empty_cells = sum(1 for i in range(9) for j in range(9) 
                                     if st.session_state.game_grid[i][j] == 0)
                    if empty_cells > 0:
                        st.markdown(f"<p>You have {empty_cells} cells left to fill.</p>", 
                                  unsafe_allow_html=True)
            
            # Show solution (give up)
            if not st.session_state.game_complete and st.button("Show Solution (Give Up)"):
                st.session_state.game_grid = [row[:] for row in st.session_state.solution]
                st.session_state.game_complete = True
                st.experimental_rerun()

# About section
else:  # About
    st.markdown("<h3>ℹ️ About Streamoku</h3>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class='description'>
        Streamoku is a Streamlit application that demonstrates interactive web app development capabilities.
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    ### Features
    
    - **Sudoku Solver**: Input any valid Sudoku puzzle and get the solution
    - **Play Sudoku**: Play Sudoku games of varying difficulty
    - **Interactive UI**: Fully interactive web interface built with Streamlit
    
    ### Technical Details
    
    This application demonstrates:
    
    - Algorithm implementation (backtracking for Sudoku solving)
    - Interactive web development with Streamlit
    - Dynamic image generation
    - Session state management for game progress
    - User input handling and validation
    
    ### About the Developer
    
    This application was developed as part of a portfolio demonstrating Python and Streamlit expertise.
    
    ### Technologies Used
    
    - Python
    - Streamlit
    - NumPy
    - Pandas
    - PIL (Python Imaging Library)
    """)

# Footer
st.markdown("""
<div class='small-text' style='text-align: center; margin-top: 50px;'>
    © 2025 Streamoku | Built with Streamlit | Python Showcase Project
</div>
""", unsafe_allow_html=True)
