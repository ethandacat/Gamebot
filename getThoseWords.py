# This file was written by AI

import csv
import re

import gensim.downloader as api
import nltk
from nltk.corpus import wordnet as wn
from spacy.lang.en.stop_words import STOP_WORDS  # no spaCy model needed
from tqdm import tqdm
from wordfreq import top_n_list, zipf_frequency

# =========================
# CONFIGURATION
# =========================

MODEL_NAME = "glove-wiki-gigaword-50"

SCAN_DEPTH = 400_000        # how many wordfreq entries to scan (highest frequency first)
MIN_ZIPF = 2.5
MIN_WORD_LENGTH = 3         # drops 2-letter junk (tv, dc, pm...). Use 2 if you want "go", "up", etc.
MAX_WORD_LENGTH = 20
TARGET_SIZE = 20000
REMOVE_STOP_WORDS = True    # set False to keep words like "make", "name", "show"

OUTPUT_TXT = "english_words.txt"
OUTPUT_CSV = "english_words.csv"

POS_MAP = {"n": "NOUN", "v": "VERB", "a": "ADJ", "s": "ADJ", "r": "ADV"}

# =========================
# LOAD RESOURCES
# =========================

print("Loading GloVe...")
model = api.load(MODEL_NAME)
glove_index = model.key_to_index  # word -> rank; the ONLY source of truth for "is this word allowed"
print(f"GloVe vocabulary: {len(glove_index):,}")

nltk.download("wordnet", quiet=True)

# =========================
# FILTERS
# =========================

ALPHA = re.compile(r"[a-z]+")


def basic_filter(word):
    if not ALPHA.fullmatch(word):
        return False
    if not (MIN_WORD_LENGTH <= len(word) <= MAX_WORD_LENGTH):
        return False
    if REMOVE_STOP_WORDS and word in STOP_WORDS:
        return False
    return True


def wordnet_pos(word):
    """POS tags for which `word` is a real lowercase WordNet lemma.

    WordNet keeps proper nouns capitalized ("London"), so requiring an exact
    lowercase lemma match drops names and places without any POS guessing.
    """
    tags = set()
    for syn in wn.synsets(word):
        if any(lemma.name() == word for lemma in syn.lemmas()):
            tags.add(POS_MAP[syn.pos()])
    return tags


# =========================
# BUILD
# =========================

valid_words = []
not_in_glove = 0

for word in tqdm(top_n_list("en", SCAN_DEPTH), desc="Scanning"):
    # GloVe gate comes first: a word that isn't in GloVe is never considered further.
    if word not in glove_index:
        not_in_glove += 1
        continue

    if not basic_filter(word):
        continue

    zipf = zipf_frequency(word, "en")
    if zipf < MIN_ZIPF:
        continue

    pos = wordnet_pos(word)
    if not pos:
        continue

    valid_words.append({
        "word": word,
        "frequency": zipf,
        "pos": "/".join(sorted(pos)),
        "glove_rank": glove_index[word],
    })

print(f"Skipped (not in GloVe): {not_in_glove:,}")
print(f"Passed all filters: {len(valid_words):,}")

# =========================
# RANK AND EXPORT
# =========================

valid_words.sort(key=lambda x: (-x["frequency"], x["glove_rank"]))
valid_words = valid_words[:TARGET_SIZE]

# Hard guarantee: nothing outside GloVe can be written.
assert all(item["word"] in glove_index for item in valid_words)

with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
    f.write("\n".join(item["word"] for item in valid_words) + "\n")

with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["word", "frequency", "pos", "glove_rank"])
    writer.writeheader()
    writer.writerows(valid_words)

# =========================
# SUMMARY
# =========================

print("\nVocabulary generated!")
print(f"Total words: {len(valid_words):,}")
print(f"TXT: {OUTPUT_TXT}")
print(f"CSV: {OUTPUT_CSV}")
print("\nFirst 50 words:")
print([x["word"] for x in valid_words[:50]])