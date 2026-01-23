import markovify
from pathlib import Path
import asyncio


folder = Path("data_holder/markov_studies")
files_dict = {
	int(f.stem): f.read_text(encoding="utf-8")
	for f in folder.iterdir()
	if f.is_file() and f.suffix == ".txt"
}


def markov_learner(text: str, guild: int):
	text = text.replace("<@953258800759070720> ", "")
	files_dict[guild] = f"{files_dict[guild]}\n{text}"


async def markov_saver():
	while True:
		await asyncio.sleep(300)
		for guild in files_dict:
			with open(f"data_holder/markov_studies/{guild}.txt", "w") as f:
				f.write(files_dict[guild])


# noinspection SpellCheckingInspection
def markovifier(guild: int):
	text = files_dict[guild]

	markov_chain_model = markovify.Text(text)
	return markov_chain_model.make_short_sentence(50, 20, tries = 20)
