import markovify


def markov_learner(text: str):
    text = text.replace("<@953258800759070720> ", "")
    with open("data_holder/markov_studies.txt", "a") as f:
        f.write(f"{text}\n")


# noinspection SpellCheckingInspection
def markovifier():
    with open("data_holder/markov_studies.txt", "r") as f:
        text = f.readlines()
    text = "\n".join(text)

    markov_chain_model = markovify.Text(text)
    return markov_chain_model.make_short_sentence(50, 20, tries = 20)
