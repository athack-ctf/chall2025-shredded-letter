# Solution

**NOTE:** There is no single way of solving this challenge. However, I am providing one working solution demonstrating
that it is solvable indeed.

## Dependencies

- Let's have a fresh venv and install all python requirements
    ```
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```
- We will also have to install `tesseract-ocr`
    ```
    apt install tesseract-ocr
    ```

## Shreds

Make sure to have a copy of all shreds placed in `./shreds` directory (at the root of the solution project).

## Notebooks

Gluing back the shreds will be done in 3 steps, and we'll have one notebook for each of step.

1. **merging shred pairs:** using an ad-hoc distance to calculate the similarity between two shreds, and then merging
   them.
    - Notebook: [01_merging_shred_pairs.ipynb](./01_merging_shred_pairs.ipynb)
2. *converting each column (shred pair) into a column of letters:* using an OCR library to identify all letters within
   merged shred pairs (aka columns).
    - Notebook: [02_converting_to_a_letters_matrix.ipynb](./02_converting_to_a_letters_matrix.ipynb)
3. **reconstructing dr. dexter's letter:**
   using a backtracking algorithm and prefix matching
   (based on [words_alpha.txt](https://github.com/dwyl/english-words/blob/master/words_alpha.txt) as a wordlist)
   to reconstruct the letter.
    - Notebook: [03_reconstructing_letter.ipynb](03_reconstructing_letter.ipynb)
