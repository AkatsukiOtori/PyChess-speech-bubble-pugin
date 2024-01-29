import chess
import chess.svg
import xml.etree.ElementTree as ET
import svgwrite
import textwrap
import sys

initial_board_size = 390
initial_line_width = 15
initial_block_size = 45
scale = 3
zoom_factor = 3
canvas_size = zoom_factor * initial_board_size
board_height = canvas_size / scale * (scale - 1)
board_width = canvas_size / scale * (scale - 1)
line_width = board_width / (initial_board_size / initial_line_width)
block_width = initial_block_size * (zoom_factor - 1)


def create_blank_svg(width, height):
    blank = svgwrite.Drawing(size=(width, height))
    blank = blank.tostring()
    return blank


def combine_two_svg(width, height, x, y, new_svg, old_svg, svg_type):

    old_tree = ET.ElementTree(ET.fromstring(old_svg))
    old_root = old_tree.getroot()

    if svg_type == "svg":
        new_svg_tree = ET.parse(new_svg)
    else:
        new_svg_tree = ET.ElementTree(ET.fromstring(new_svg))
    new_svg_root = new_svg_tree.getroot()

    width = str(width) + 'px'
    height = str(height) + 'px'

    new_svg_root.set('width', str(width))
    new_svg_root.set('height', str(height))

    new_svg_root.set('x', str(x))
    new_svg_root.set('y', str(y))

    old_root.append(new_svg_root)

    combined_svg = ET.tostring(old_root, encoding='unicode')
    return combined_svg


def generate_new_board():
    blank_tree = ET.ElementTree(ET.fromstring(create_blank_svg(canvas_size, canvas_size)))
    blank_root = blank_tree.getroot()

    board = chess.Board()
    chessboard_svg = chess.svg.board(board)
    chessboard_tree = ET.ElementTree(ET.fromstring(chessboard_svg))
    chessboard_root = chessboard_tree.getroot()

    board_x = int(board_width / (scale + 1))
    board_y = int(board_height / (scale + 1))

    this_board_width = str(board_width) + 'px'
    this_board_height = str(board_height) + 'px'

    chessboard_root.set('width', this_board_width)
    chessboard_root.set('height', this_board_height)

    chessboard_root.set('x', str(board_x))
    chessboard_root.set('y', str(board_y))

    blank_root.append(chessboard_root)

    combined_svg = ET.tostring(blank_root, encoding='unicode')
    return combined_svg


def fit_text_in_bubble(max_height, max_width, text, font_family="Arial", line_spacing=1.2):
    # Constants
    min_font_size = 20

    def wrap_text(this_text, this_font_size, this_max_width):
        # Create a Drawing to estimate text size
        temp_dwg = svgwrite.Drawing()
        temp_dwg.add(temp_dwg.text(this_text, insert=(0, 0), font_size=this_font_size, font_family=font_family))
        wrapped_lines = textwrap.wrap(text, width=this_max_width)
        this_text_height = font_size * line_spacing * len(wrapped_lines)
        return wrapped_lines, this_text_height

    font_size = min_font_size
    max_line_length = int(max_width // (font_size * 0.6))  # Estimate line length
    lines, text_height = wrap_text(text, font_size, max_line_length)

    # Check if text exceeds the maximum height
    if text_height > max_height:
        return False

    # Increase font size if there's more space available
    while text_height < max_height:
        font_size += 1
        max_line_length = int(max_width // (font_size * 0.6))
        new_lines, new_text_height = wrap_text(text, font_size, max_line_length)
        if new_text_height > max_height:
            # If the new size exceeds the max height, revert to the previous size
            font_size -= 1
            break
        else:
            lines, text_height = new_lines, new_text_height

    # Create the final SVG with wrapped text
    dwg = svgwrite.Drawing(size=(max_width, max_height))
    y_position = (max_height - text_height) / 2 + font_size  # Center text vertically

    for line in lines:
        dwg.add(dwg.text(line, insert=(0, y_position), font_size=font_size, font_family=font_family))
        y_position += font_size * line_spacing

    text_blank = create_blank_svg(max_width, max_height)
    text_svg = combine_two_svg(max_width, max_height, 0, 0,dwg.tostring(), text_blank, 'str')

    return text_svg


def generate_bubble(shape, text):

    initial_bubble_width = int(block_width * 2)
    bubble_width = initial_bubble_width
    bubble_height = int(block_width * 2)
    text_width = int(bubble_width * 1.2)
    text_height = int(bubble_height * 0.65)

    result = fit_text_in_bubble(text_height, text_width, text)

    if result is False:
        # Increase the width and try again
        bubble_width = int(bubble_width * 1.4)
        text_width = int(bubble_width * 1.3)
        result = fit_text_in_bubble(text_height, text_width, text)

        if result is False:
            return None
        else:
            text_svg = result
    else:
        text_svg = result

    if shape == 'speak':
        shape_svg = 'texture/speak.svg'
    elif shape == 'surprise':
        shape_svg = 'texture/surprise.svg'
    elif shape == 'think':
        shape_svg = 'texture/think.svg'
    else:
        print('The shape is not recognized.')
        return None

    blank_bubble = create_blank_svg(bubble_width, bubble_height)
    shape_x = int(bubble_width - initial_bubble_width) * 0.64
    shape_y = 0
    speech_bubble = combine_two_svg(bubble_width, bubble_height, shape_x * 0.5, shape_y, shape_svg, blank_bubble, 'svg')
    if shape_x > 0:
        new_blank_bubble = create_blank_svg(shape_x, bubble_height)
        crop_bubble_path = 'texture/crop.svg'
        crop_bubble = combine_two_svg(bubble_width, bubble_height, 0,0, crop_bubble_path, new_blank_bubble, 'svg')
        speech_bubble = combine_two_svg(bubble_width, bubble_height, shape_x * (-1.9), shape_y, crop_bubble, speech_bubble, 'str')
        text_x = bubble_height / 15
    else:
        text_x = bubble_height / 20
    text_y = bubble_height / 20
    combined_svg = combine_two_svg(bubble_width, bubble_height, text_x, text_y, text_svg, speech_bubble, 'str')
    combined_list = [combined_svg, bubble_width, bubble_height, shape_x]
    with open("speech_bubble.svg", "w") as file:
        file.write(combined_svg)
    return combined_list


def square_to_coordinates(square_name):
    """
    Convert a chess square name (e.g., 'e4') to pixel coordinates.

    :param square_name: String, name of the chess square (e.g., 'e4').
    :param board_size: Tuple (width, height) of the chessboard image in pixels.
    :return: Tuple (x, y) coordinates in pixels.
    """
    # Mapping from letter to x-coordinate (a=0, b=1, ..., h=7)
    letter_to_x = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}
    # Extract the letter and number from the square name
    letter = square_name[0]
    number = int(square_name[1])

    # Convert the letter and number to x and y coordinates
    x = letter_to_x[letter] * ((board_width - line_width * 2) / 8) + board_width / (scale + 1) + line_width
    y = (8 - number) * ((board_height - line_width * 2) / 8) + board_height / (scale + 1) + line_width

    position = [x, y]
    return position


def generate_board_with_speech_bubble(text, shape, chess_location):
    board = generate_new_board()
    if generate_bubble(shape, text) is None or len(text) > 130:
        sys.exit("Text is too long or shape is not recognized. Try again.")
    text_bubble = generate_bubble(shape, text)[0]
    bubble_width = generate_bubble(shape, text)[1]
    bubble_height = generate_bubble(shape, text)[2]
    shape_width = generate_bubble(shape, text)[3]
    chess_x = square_to_coordinates(chess_location)[0]
    chess_y = square_to_coordinates(chess_location)[1]
    bubble_x = chess_x - bubble_width / 2 - shape_width
    bubble_y = chess_y - bubble_height * 0.9
    final_board = combine_two_svg(bubble_width, bubble_height, bubble_x, bubble_y, text_bubble, board, 'str')
    print(board_width, chess_x, chess_y, line_width)
    with open("combined_chessboard_and_speech_bubble.svg", "w") as file:
        file.write(final_board)


# Example use
generate_board_with_speech_bubble('Hello', 'think', "h1")