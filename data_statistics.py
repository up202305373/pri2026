import pandas as pd
import json

print("Loading data for analysis...")
df_reviews = pd.read_csv('data/processed/Final_Search_Corpus_4.csv.gz', compression='gzip')

with open('data/processed/final_games_4.json', 'r', encoding='utf-8') as f:
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
df_reviews['word_count'] = df_reviews['review'].apply(lambda x: len(str(x).split()))
print(f"\nTerm Metrics (Review Length):")
print(f" - Average words per review: {df_reviews['word_count'].mean():.1f}")
print(f" - Median words per review: {df_reviews['word_count'].median():.1f}")
print(f" - Max words in a single review: {df_reviews['word_count'].max()}")

# Playtime characteristics (Steam only)
steam_reviews = df_reviews[df_reviews['source'] == 'Steam']
print(f"\nSteam Playtime Characteristics:")
print(f" - Average playtime at review time: {steam_reviews['playtime'].mean():.1f} minutes")

# Metascore characteristics
meta_reviews = df_reviews[df_reviews['source'] == 'Metacritic']
print(f"\nMetacritic Curated Scores:")
print(f" - Average Metascore: {meta_reviews['metascore'].mean():.1f}")