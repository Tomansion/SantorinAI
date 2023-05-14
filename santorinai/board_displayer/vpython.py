import PySimpleGUI as sg

def draw_2Dcube(window, x, y, size, color):
    """
    Draw a 2D cube on the given window.
    :param window: The PySimpleGUI window object to draw on.
    :param x: The x-coordinate of the cube.
    :param y: The y-coordinate of the cube.
    :param size: The size of the cube.
    :param color: The color of the cube.
    """
    graph = window["-GRAPH-"]
    graph.draw_rectangle((x, y), (x + size, y + size), fill_color=color, line_color=color)

def draw_board(window, grid, size):
    """
    Draw the grid in a fake 3D isometric view on the given window.
    :param window: The PySimpleGUI window object to draw on.
    :param grid: The 2D grid to draw.
    :param size: The size of each cube in the grid.
    """
    rows, cols = len(grid), len(grid[0])

    for i in range(rows):
        for j in range(cols):
            x = (j - i) * size
            y = (j + i) * size
            draw_2Dcube(window, x, y, size, grid[i][j])

    # Refresh the window to update the drawing
    window.refresh()

# Example usage
grid = [
    ['red', 'blue', 'green'],
    ['yellow', 'purple', 'orange'],
    ['pink', 'cyan', 'brown']
]

cube_size = 50
window_width = len(grid[0]) * cube_size + cube_size
window_height = len(grid) * cube_size + cube_size

# Create the PySimpleGUI window
layout = [
    [sg.Text("Game Board", font=("Helvetica", 20), justification="center")],
    [sg.Graph((800, 600), (0, 0), (800, 600), key="-GRAPH-", change_submits=True)],
]
window = sg.Window("Game Board", layout, finalize=True)

# Draw the initial board
draw_board(window, grid, cube_size)

# Event loop to handle window events
while True:
    event, values = window.read()
    if event == sg.WINDOW_CLOSED:
        break

# Close the window when done
window.close()
