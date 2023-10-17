import markovify


def markov_learner(text: str):
    text = text.replace("@Dice God ", "")
    with open("data_holder/markov_studies.txt", "a") as f:
        f.write(text)


# noinspection SpellCheckingInspection
def markovifier():
    with open("data_holder/markov_studies.txt", "r") as f:
        text = f.read()

    markov_chain_model = markovify.Text(text)
    return markov_chain_model.make_sentence()
