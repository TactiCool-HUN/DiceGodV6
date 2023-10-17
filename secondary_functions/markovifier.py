import markovify
import random


def markov_learner(text: str):
    text = text.replace("@Dice God ", "")
    with open("data_holder/markov_studies.txt", "a") as f:
        f.write(f"{text}\n")


# noinspection SpellCheckingInspection
def markovifier():
    with open("data_holder/markov_studies.txt", "r") as f:
        text = f.readlines()
    text = " ".join(text)

    markov_chain_model = markovify.Text(text)
    return markov_chain_model.make_short_sentence(70, 20, tries = 20)
