import markovify
import pandas as pd
from itertools import chain


def markov_learner(text):
    with open("data_holder/markov_studies.txt", "a") as f:
        f.write(text)


pass
