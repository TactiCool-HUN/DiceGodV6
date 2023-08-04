from random import randint as rand

# noinspection SpellCheckingInspection
alphabet = list("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")


def uwuify(text):
	converted_sentence = []
	for word in text.split(" "):
		converted = ""
		double_t = double_t_presence = th_presence = False

		for j in range(len(word)):
			if double_t or th_presence:
				double_t = th_presence = False
				continue
			elif (word[j].lower() == "l" and not double_t_presence) or (word[j].lower() == "r"):
				converted += "W" if word[j].isupper() else "w"
			elif (word[j].lower() == "t") and (word[j + (1 if j + 1 < len(word) else 0)].lower() == "t"):
				converted += (("D" if word[j].isupper() else "d") + ("D" if word[j + 1].isupper() else "d")) if j + 1 < len(word) else "t"
				double_t = double_t_presence = True if j + 1 < len(word) else False
			elif (word[j].lower() == "t") and (word[j + (1 if j + 1 < len(word) else 0)].lower() == "h"):
				converted += ("F" if word[j].isupper() else "f") if j + 2 == len(word) else "t"
				th_presence = True if j + 2 == len(word) else False
			else:
				converted += word[j]
		if len(word) > 0 and (word[0] != ":" or word[-1] != ":"):
			converted_sentence.append((converted[0] + "-" + converted[0:]) if (rand(1, 10) == 1 and converted[0] in alphabet) else converted)
		else:
			converted_sentence.append(word)

	return " ".join(converted_sentence)


pass
