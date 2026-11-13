<<<<<<< HEAD
# This file was written by AI

import csv
import re

import gensim.downloader as api
import nltk
from nltk.corpus import wordnet as wn
from spacy.lang.en.stop_words import STOP_WORDS  # no spaCy model needed
from tqdm import tqdm
from wordfreq import top_n_list, zipf_frequency
=======

import re
import csv
import spacy
import gensim.downloader as api

from wordfreq import zipf_frequency
from tqdm import tqdm
>>>>>>> 59740a5 (ToolRemote checkpoint - 2026-11-07 14:08)

# =========================
# CONFIGURATION
# =========================

<<<<<<< HEAD
MODEL_NAME = "glove-wiki-gigaword-50"

SCAN_DEPTH = 400_000        # how many wordfreq entries to scan (highest frequency first)
MIN_ZIPF = 2.5
MIN_WORD_LENGTH = 3         # drops 2-letter junk (tv, dc, pm...). Use 2 if you want "go", "up", etc.
MAX_WORD_LENGTH = 20
TARGET_SIZE = 20000
REMOVE_STOP_WORDS = True    # set False to keep words like "make", "name", "show"
=======
MODEL_NAME = "glove-wiki-gigaword-100"

MIN_ZIPF = 2.5
MAX_WORD_LENGTH = 20
TARGET_SIZE = 20000
>>>>>>> 59740a5 (ToolRemote checkpoint - 2026-11-07 14:08)

OUTPUT_TXT = "english_words.txt"
OUTPUT_CSV = "english_words.csv"

<<<<<<< HEAD
POS_MAP = {"n": "NOUN", "v": "VERB", "a": "ADJ", "s": "ADJ", "r": "ADV"}
=======
ALLOWED_POS = {"NOUN", "VERB", "ADJ", "ADV"}
>>>>>>> 59740a5 (ToolRemote checkpoint - 2026-11-07 14:08)

# =========================
# LOAD RESOURCES
# =========================

print("Loading GloVe...")
model = api.load(MODEL_NAME)
<<<<<<< HEAD
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
=======

print("Loading spaCy...")
nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])

print(f"GloVe vocabulary: {len(model.key_to_index):,}")

# =========================
# FILTERING
# =========================

def basic_filter(word):
    word = word.lower()

    if not word.isascii():
        return False

    if not re.fullmatch(r"[a-z]+", word):
        return False

    if len(word) < 2 or len(word) > MAX_WORD_LENGTH:
        return False

    if word in nlp.Defaults.stop_words:
        return False

    return True


# Preserve GloVe's original vocabulary order for tie-breaking
candidates = [
    word for word in model.key_to_index
    if basic_filter(word)
]

print(f"After basic filtering: {len(candidates):,}")

# =========================
# FREQUENCY FILTER
# =========================

frequency_scores = {}

for word in tqdm(candidates, desc="Checking frequency"):
    score = zipf_frequency(word, "en")

    if score >= MIN_ZIPF:
        frequency_scores[word] = score

print(f"After frequency filtering: {len(frequency_scores):,}")

# =========================
# PART OF SPEECH FILTER
# =========================

valid_words = []

for word, doc in zip(
    frequency_scores.keys(),
    nlp.pipe(frequency_scores.keys(), batch_size=1024)
):
    if not doc:
        continue

    token = doc[0]

    if token.pos_ not in ALLOWED_POS:
        continue

    # Exclude proper nouns when detected
    if token.pos_ == "PROPN":
>>>>>>> 59740a5 (ToolRemote checkpoint - 2026-11-07 14:08)
        continue

    valid_words.append({
        "word": word,
<<<<<<< HEAD
        "frequency": zipf,
        "pos": "/".join(sorted(pos)),
        "glove_rank": glove_index[word],
    })

print(f"Skipped (not in GloVe): {not_in_glove:,}")
print(f"Passed all filters: {len(valid_words):,}")

=======
        "frequency": frequency_scores[word],
        "pos": token.pos_,
        "glove_rank": model.key_to_index[word]
    })

>>>>>>> 59740a5 (ToolRemote checkpoint - 2026-11-07 14:08)
# =========================
# RANK AND EXPORT
# =========================

<<<<<<< HEAD
valid_words.sort(key=lambda x: (-x["frequency"], x["glove_rank"]))
valid_words = valid_words[:TARGET_SIZE]

# Hard guarantee: nothing outside GloVe can be written.
assert all(item["word"] in glove_index for item in valid_words)

with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
    f.write("\n".join(item["word"] for item in valid_words) + "\n")

with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["word", "frequency", "pos", "glove_rank"])
=======
valid_words.sort(
    key=lambda x: (
        -x["frequency"],
        x["glove_rank"]
    )
)

valid_words = valid_words[:TARGET_SIZE]

with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
    f.write("\n".join(item["word"] for item in valid_words))

with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["word", "frequency", "pos", "glove_rank"]
    )
>>>>>>> 59740a5 (ToolRemote checkpoint - 2026-11-07 14:08)
    writer.writeheader()
    writer.writerows(valid_words)

# =========================
# SUMMARY
# =========================

print("\nVocabulary generated!")
print(f"Total words: {len(valid_words):,}")
print(f"TXT: {OUTPUT_TXT}")
print(f"CSV: {OUTPUT_CSV}")
<<<<<<< HEAD
print("\nFirst 50 words:")
print([x["word"] for x in valid_words[:50]])
=======

print("\nFirst 50 words:")
print([x["word"] for x in valid_words[:50]])
>>>>>>> 59740a5 (ToolRemote checkpoint - 2026-11-07 14:08)
