import pandas as pd
import json
import re
from collections import Counter

# https://gist.github.com/sebleier/554280
stopwords = {"above","a","after","again","against","all","am","an","and","any","are","as","at","be","because","been","about","before","being","below","between","both","but","by","can","did","do","does","doing","don","down","during","each","few","for","from","further","had","has","have","having","he","her","here","hers","herself","him","himself","his","how","i","if","in","into","is","it","its","itself","just","me","more","most","my","myself","no","nor","not","now","of","off","on","once","only","or","other","our","ours","ourselves","out","over","own","s","same","she","should","so","some","such","t","than","that","the","their","theirs","them","themselves","then","there","these","they","this","those","through","to","too","under","until","up","very","was","we","were","what","when","where","which","while","who","whom","why","will","with","you","your","yours","yourself","yourselves"}

# https://github.com/improbabilitea/names-go/blob/main/filters/profanity/profanity.go
slurs = {"anal","anus","arse","ass","bastard","bitch","bollocks","boob","boobs","bugger","cock","crap","cunt","dick","dildo","dyke","fag","faggot","fuck","fucker","jizz","nigga","nigger","penis","piss","prick","pube","pussy","queer","rape","rapist","retard","scrotum","semen","shit","slut","spastic","tits","turd","twat","vagina","wank","whore"}

print("Loading data for analysis...")
df_reviews = pd.read_csv('data/processed/Final_Search_Corpus.csv.gz', compression='gzip')

with open('data/processed/final_games.json', 'r', encoding='utf-8') as f:
    games_data = json.load(f)

print("\n=== DATASET CHARACTERIZATION ===")
print(f"Total Unique Games: {len(games_data)}")
print(f"Total Review Documents: {len(df_reviews)}")

# Source distribution
source_counts = df_reviews['source'].value_counts()
print(f"\nDocuments by Source:")
print(f" - Steam: {source_counts.get('Steam', 0)}")
print(f" - Metacritic: {source_counts.get('Metacritic', 0)}")

# Term Metrics (Word counts)
def tokenize(text): return re.findall(r"\b[\w']+\b", str(text).lower())
df_reviews['word_count'] = df_reviews['review'].apply(lambda x: len(tokenize(x)))
df_reviews['stopword_count'] = df_reviews['review'].apply(lambda x: sum(word in stopwords for word in tokenize(x)))
df_reviews['stopword_ratio'] = df_reviews['stopword_count'] / df_reviews['word_count']
df_reviews['slur_count'] = df_reviews['review'].apply(lambda x: sum(word in slurs for word in tokenize(x)))
df_reviews['slur_ratio'] = df_reviews['slur_count'] / df_reviews['word_count']

print(f"\nTerm Metrics (Review Length):")

unique_words = [word for review in df_reviews['review'] for word in tokenize(review)]
word_counts = Counter(unique_words)

print(f" - Total words across all reviews: {df_reviews['word_count'].sum():.1f}")
print(f" - Total unique words across all reviews: {len({word for review in df_reviews['review'] for word in tokenize(review)}):.1f}")
print(f" - Total words that appear exactly once (hapax legomena): {sum(count == 1 for count in word_counts.values()):.1f}")

print(f"\n - Average words per review: {df_reviews['word_count'].mean():.1f}")
print(f" - Median words per review: {df_reviews['word_count'].median():.1f}")
print(f" - Max words in a single review: {df_reviews['word_count'].max()}")

print(f"\n - Total stopword proportion: {(df_reviews['stopword_count'].sum()/df_reviews['word_count'].sum()):.2%}")
print(f" - Average stopword proportion: {(df_reviews['stopword_ratio'].mean()):.2%}")
print(f" - Total slur proportion: {(df_reviews['slur_count'].sum()/df_reviews['word_count'].sum()):.2%}")
print(f" - Average slur proportion: {(df_reviews['slur_ratio'].mean()):.2%}")

# Playtime characteristics (Steam only)
steam_reviews = df_reviews[df_reviews['source'] == 'Steam']
print(f"\nSteam Playtime Characteristics:")
print(f" - Average playtime at review time: {steam_reviews['playtime'].mean():.1f} minutes")

# Metascore characteristics
meta_reviews = df_reviews[df_reviews['source'] == 'Metacritic']
print(f"\nMetacritic Curated Scores:")
print(f" - Average Metascore: {meta_reviews['metascore'].mean():.1f}")

userscores = pd.Series(pd.to_numeric([game.get('userscore') for game in games_data.values()],errors='coerce'))
print(f" - Average Userscore: {userscores.mean():.1f}")
