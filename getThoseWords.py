
import re
import csv
import spacy
import gensim.downloader as api

from wordfreq import zipf_frequency
from tqdm import tqdm

# =========================
# CONFIGURATION
# =========================

MODEL_NAME = "glove-wiki-gigaword-100"

MIN_ZIPF = 2.5
MAX_WORD_LENGTH = 20
TARGET_SIZE = 20000

OUTPUT_TXT = "english_words.txt"
OUTPUT_CSV = "english_words.csv"

ALLOWED_POS = {"NOUN", "VERB", "ADJ", "ADV"}

# =========================
# LOAD RESOURCES
# =========================

print("Loading GloVe...")
model = api.load(MODEL_NAME)

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
        continue

    valid_words.append({
        "word": word,
        "frequency": frequency_scores[word],
        "pos": token.pos_,
        "glove_rank": model.key_to_index[word]
    })

# =========================
# RANK AND EXPORT
# =========================

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
