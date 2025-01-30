import json
import os
import random

from PIL import Image, ImageDraw, ImageFont
import re
import requests
import tempfile

# Monospace font to be used
FONT_PATH = "monospace-fonts/UbuntuMono-Bold.ttf"

# Space taken by each letter (in pixels)
LETTER_WIDTH = 16
HALF_OF_LETTER_WIDTH = int(LETTER_WIDTH / 2)
LETTER_HEIGHT = 28

# Max letters per line
MAX_CHARS_PER_LINE = 100

# Number of lines
LINES_COUNT = 32


def load_text(file_path, upper_case=True):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
            if upper_case:
                text = text.upper()
        return text
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except IOError as e:
        raise IOError(f"Error reading file {file_path}: {e}")


def load_words_alpha_corpus():
    url = "https://github.com/dwyl/english-words/raw/refs/heads/master/words_alpha.txt"

    with requests.get(url, stream=True) as response:
        response.raise_for_status()  # Ensure successful download
        with tempfile.NamedTemporaryFile(delete=False, mode='w+', encoding='utf-8') as tmp_file:
            for chunk in response.iter_content(chunk_size=8192):
                tmp_file.write(chunk.decode())  # Decode bytes to string

            english_words_file = tmp_file.name  # Save file path before closing

    # Load corpus directly
    with open(english_words_file, 'r', encoding='utf-8') as file:
        wordlist = [line.strip() for line in file.readlines()]

    return set(wordlist)


WORDS_ALPHA_CORPUS = load_words_alpha_corpus()


def split_text_into_lines(text, max_letters=MAX_CHARS_PER_LINE):
    lines = []
    for paragraph in text.splitlines():
        current_line = ""
        for word in re.split(r'(\s+)', paragraph):
            if len(current_line) + len(word) <= max_letters:
                current_line += word
            else:
                if current_line:
                    lines.append(current_line.strip())
                if len(word.strip()) > max_letters:
                    # Handle cases where a single word exceeds max_letters
                    while len(word) > max_letters:
                        lines.append(word[:max_letters])
                        word = word[max_letters:]
                current_line = word
        if current_line:
            lines.append(current_line.strip())
    return lines


def is_valid_text(text, corpus=WORDS_ALPHA_CORPUS):
    text = text.upper()

    # Make sure that we are only using characters within the allowed alphabet
    allowed_pattern = r'^[A-Z., \n]*$'
    if not bool(re.fullmatch(allowed_pattern, text)):
        print("Text is not within the allowed grammar")
        return False

    # Checking if all words are in the wordlist
    words = set()
    words.update(re.split(r'[ .,\n]+', text))
    words.discard('')

    for w in words:
        if w.lower() not in corpus:
            print(f"Out of corpus word: {w}")
            return False

    # Making sure that the number of lines is correct
    lines = split_text_into_lines(text)
    # print("\n".join(lines))
    if len(lines) != LINES_COUNT:
        print(f"Wrong number of lines. Required {32}. Found {len(lines)}")
        return False

    max_line = max(lines, key=len)
    if len(max_line) != MAX_CHARS_PER_LINE:
        print(f"The longest line has to be exactly {MAX_CHARS_PER_LINE}. Found {len(max_line)}")
        return False

    # Making sure the first word of every line has at least 4 characters
    for line in lines:
        first_wrd = line.replace(".", " ").replace(",", " ").split(" ")[0]
        if len(first_wrd) < 4:
            print(f"First word of a line is too short. {first_wrd}")
            return False

    return True


def generate_bmp_from_text(text,
                           output_path,
                           letter_width=LETTER_WIDTH,
                           letter_height=LETTER_HEIGHT,
                           max_chars_per_line=MAX_CHARS_PER_LINE,
                           font_path=FONT_PATH):
    # Define the font size to match the letter size
    # font_size = LETTER_WIDTH
    font_size = letter_height
    font = ImageFont.truetype(font_path, font_size)

    # Determine the dimensions of the image
    lines = split_text_into_lines(text, max_chars_per_line)

    # Calculating dimensions
    width = max_chars_per_line * letter_width
    height = int(len(lines) * letter_height)

    # Create a blank white image
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    # Draw each character at the correct position
    for y, line in enumerate(lines):
        for x, char in enumerate(line):
            draw.text((x * letter_width, y * letter_height), char, font=font, fill="black")

    # Save the image
    image.save(output_path, format="BMP")


def generate_shuffling_map(num_shreds, do_not_shuffle=False):
    # Create the original array
    original_array = list(range(num_shreds))

    # Create a copy and shuffle it
    shuffled_array = original_array[:]
    random.shuffle(shuffled_array)

    if do_not_shuffle:
        shuffled_array = original_array[:]

    # Create the mapping dictionary
    shuffling_map = {original: shuffled for original, shuffled in zip(original_array, shuffled_array)}

    return shuffling_map


def shred_image(image_path, shred_width, shreds_dir_path, shreds_map_path, do_not_shuffle=False):
    # Open the image
    image = Image.open(image_path)

    # Get image dimensions
    width, height = image.size

    # Check if the width is divisible by the shred width
    if width % shred_width != 0:
        return f"Error: The image width ({width}px) is not divisible by the shred width ({shred_width}px)."

    # Calculate the number of shreds
    num_shreds = width // shred_width

    # Shuffled dict
    shreds_map = generate_shuffling_map(num_shreds, do_not_shuffle=do_not_shuffle)

    # Slice the image into shreds
    for i in range(num_shreds):
        left = i * shred_width
        right = (i + 1) * shred_width
        column_image = image.crop((left, 0, right, height))

        # Save the shred
        shuffled_idx = shreds_map[i]
        column_image_path = f"{shreds_dir_path}/shred_{shuffled_idx}.bmp"
        column_image.save(column_image_path, format="BMP")

    # Saving shuffling dict
    with open(shreds_map_path, 'w', encoding='utf-8') as f:
        json.dump(shreds_map, f, indent=4)


def generate_flag(text, key_words_idx):
    # Define a regex pattern to split paragraphs
    paragraphs = text.split('.\n')

    # To store the 13th words
    key_words = []

    for paragraph in paragraphs:
        # Remove punctuation and split words by spaces
        words = re.split(r'[ ,.?]+', paragraph.strip())
        # Filter out empty strings resulting from multiple spaces or punctuation
        words = [word for word in words if word]

        # Get the key_letter_idx word (if it exists)
        if len(words) >= key_words_idx:
            # -1 because list indices are zero-based
            key_words.append(words[key_words_idx - 1])

    # Return the concatenated string of 13th words
    flag_val = "_".join(key_words)
    return f"ATHACKCTF{{{flag_val}}}"


def generate_artifacts(text_path, output_base_path, do_not_generate_flag=False):
    # Making dir
    os.makedirs(output_base_path, exist_ok=True)

    # Image path (for the letter)
    letter_img_path = os.path.join(output_base_path, "full_letter.bmp")

    # Directory for shred
    shreds_dir = os.path.join(output_base_path, "shreds")
    os.makedirs(shreds_dir, exist_ok=True)

    # Json file for map of shreds
    shreds_dict_path = os.path.join(output_base_path, "shreds-map.json")

    # Load text
    txt = load_text(file_path=text_path)

    # Checking if the text is valid for the challenge
    if not is_valid_text(txt):
        raise Exception("Invalid text")

    # Generate image
    generate_bmp_from_text(txt, letter_img_path)

    # Shredding it
    shred_image(
        letter_img_path,
        HALF_OF_LETTER_WIDTH,
        shreds_dir, shreds_dict_path,
        do_not_shuffle=do_not_generate_flag
    )

    if not do_not_generate_flag:
        # Generate flag (6th letter of each paragraph)
        flag = generate_flag(text=txt, key_words_idx=1)

        # flag path
        flag_path = os.path.join(output_base_path, "flag.txt")

        with open(flag_path, 'w', encoding='utf-8') as f:
            f.write(flag)


if __name__ == '__main__':
    generate_artifacts(
        text_path="./letters/letter-to-roger-with-flag.txt",
        output_base_path="./letter-to-roger-with-flag",
    )

    generate_artifacts(
        text_path="./letters/letter-to-zain-without-flag.txt",
        output_base_path="./letter-to-zain-without-flag",
        do_not_generate_flag=True
    )
