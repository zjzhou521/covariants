import json5
import os

THIS_DIR = os.path.dirname(os.path.realpath(__file__))

PATH_TO_BAD_SEQUENCES_JSON = os.path.join(THIS_DIR, "bad_sequences.json5")


def get_bad_sequences():
    with open(PATH_TO_BAD_SEQUENCES_JSON, "r") as f:
        return json5.load(f)


if __name__ == '__main__':
    bad_sequences = get_bad_sequences()
    print(bad_sequences)
