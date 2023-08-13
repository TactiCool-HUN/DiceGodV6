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


# Function to convert into UwU text
def generate_uwu(input_text):
	# the length of the input text
	length = len(input_text)

	# variable declaration for the output text
	output_text = ''

	# check the cases for every individual character
	for i in range(length):

		# initialize the variables
		current_char = input_text[i]
		previous_char = '&# 092;&# 048;'

		# assign the value of previous_char
		if i > 0:
			previous_char = input_text[i - 1]

		# change 'L' and 'R' to 'W'
		if current_char == 'L' or current_char == 'R':
			output_text += 'W'

		# change 'l' and 'r' to 'w'
		elif current_char == 'l' or current_char == 'r':
			output_text += 'w'

		# if the current character is 'o' or 'O'
		# also check the previous character
		elif current_char == 'O' or current_char == 'o':
			if previous_char == 'N' or previous_char == 'n' or previous_char == 'M' or previous_char == 'm':
				output_text += "yo"
			else:
				output_text += current_char

		# if no case match, write it as it is
		else:
			output_text += current_char

	return output_text


pass
