import markovify
import pandas as pd
from itertools import chain


def markov_learner(text: str):
    text = text.replace("@Dice God", "")
    with open("data_holder/markov_studies.txt", "a") as f:
        f.write(text)


pass
