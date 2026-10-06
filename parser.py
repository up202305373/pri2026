import pandas as pd
import json
import glob
import math

print("Step 1: Loading Metacritic dataset...")
df_meta = pd.read_csv('data/raw/Metacritic/dataset_metacritic_scraper_2025-02-15.csv', low_memory=False)
meta_cols = ['title', 'genres/0', 'metascore', 'releaseDate', 'summary', 'userscore']

avail_meta_cols = [col for col in meta_cols if col in df_meta.columns]
df_meta = df_meta[avail_meta_cols]

df_meta = df_meta.rename(columns={
    'genres/0': 'Meta_Genre',
    'releaseDate': 'Meta_ReleaseDate',
    'summary': 'Meta_Summary'
})

print("Step 2: Loading Steam games dataset...")
with open('data/raw/Steam/games.json', 'r', encoding='utf-8') as f:
    steam_data = json.load(f)

steam_rows = []
for app_id, info in steam_data.items():
    steam_rows.append({
        'App_ID': str(app_id),
        'Steam_Title': info.get('name', '')
    })
df_steam = pd.DataFrame(steam_rows)

print("Step 3: Merging basic metadata to find overlap...")
df_meta['match_title'] = df_meta['title'].astype(str).str.lower().str.strip()
df_steam['match_title'] = df_steam['Steam_Title'].astype(str).str.lower().str.strip()

df_game_info = pd.merge(df_steam, df_meta, on='match_title', how='inner')
df_game_info = df_game_info.drop(columns=['match_title'])

# Create a dictionary to easily map App_ID to userscore later
userscore_map = dict(zip(df_game_info['App_ID'].astype(str), df_game_info['userscore']))

print("Step 4: Extracting Metacritic summaries as independent reviews...")
meta_reviews = []
for idx, row in df_game_info.iterrows():
    if pd.notna(row.get('Meta_Summary')) and len(str(row['Meta_Summary']).strip()) > 10:
        meta_reviews.append({
            'App_ID': str(row['App_ID']),
            'user': 'Metacritic_Critic',
            'playtime': None,
            'post_date': row.get('Meta_ReleaseDate', ''),
            'helpfulness': None,
            'review': row['Meta_Summary'],
            'recommend': None,
            'metascore': row.get('metascore', None),
            'source': 'Metacritic'
        })

print("Step 5: Loading and filtering Steam review data...")
all_reviews = []
review_cols_to_keep = ['user', 'playtime', 'post_date', 'helpfulness', 'review', 'recommend']

total_reviews_processed = 0
total_reviews_kept = 0

def is_latin_ascii(text):
    if not isinstance(text, str) or len(text) == 0:
        return False
    text_no_spaces = text.replace(" ", "").replace("\n", "").replace("\r", "")
    if len(text_no_spaces) == 0:
         return False

    ascii_count = sum(1 for c in text_no_spaces if c.isascii() and c.isalnum())
    percentage = (ascii_count / len(text_no_spaces)) * 100
    return percentage > 85

for app_id in df_game_info['App_ID']:
    matching_files = glob.glob(f"data/raw/Steam/Game Reviews/{app_id}_*.csv")

    if matching_files:
        target_file = matching_files[0]
        try:
            df_reviews = pd.read_csv(target_file)

            initial_count = len(df_reviews)
            total_reviews_processed += initial_count

            avail_review_cols = [col for col in review_cols_to_keep if col in df_reviews.columns]
            df_reviews = df_reviews[avail_review_cols]

            if 'review' in df_reviews.columns:
                df_reviews = df_reviews.dropna(subset=['review'])
                df_reviews['review'] = df_reviews['review'].astype(str)

                # Convert Date Format
                if 'post_date' in df_reviews.columns:
                    df_reviews['post_date'] = pd.to_datetime(df_reviews['post_date'], errors='coerce').dt.strftime('%d/%m/%Y')

                # Filters
                df_reviews = df_reviews.drop_duplicates(subset=['review'])
                df_reviews = df_reviews[df_reviews['review'].str.len() > 300]
                df_reviews = df_reviews[df_reviews['review'].str.split().str.len() >= 40]
                df_reviews = df_reviews[df_reviews['review'].apply(is_latin_ascii)]

            # Sample limit
            if len(df_reviews) > 500:
                df_reviews = df_reviews.sample(n=500, random_state=42)

            total_reviews_kept += len(df_reviews)

            df_reviews['App_ID'] = str(app_id)
            df_reviews['source'] = 'Steam'
            all_reviews.append(df_reviews)

        except Exception as e:
            print(f"Error reading {target_file}: {e}")

print(f"\n--- FILTERING SUMMARY ---")
print(f"Steam Reviews processed initially: {total_reviews_processed}")
print(f"Steam Reviews kept after filtering: {total_reviews_kept}")
print(f"Metacritic Curated Reviews added: {len(meta_reviews)}")
print(f"-------------------------\n")

# 6. Combine and export ONLY the reviews (No Game Metadata)
df_combined_reviews = pd.DataFrame()
if all_reviews or meta_reviews:
    print("Step 6: Creating the lean relational review dataset...")

    if all_reviews:
        df_all_steam_reviews = pd.concat(all_reviews, ignore_index=True)
    else:
        df_all_steam_reviews = pd.DataFrame()

    df_meta_reviews = pd.DataFrame(meta_reviews)
    df_combined_reviews = pd.concat([df_all_steam_reviews, df_meta_reviews], ignore_index=True)

    print("Exporting reviews to compressed CSV archive...")
    df_combined_reviews.to_csv('data/processed/Final_Search_Corpus_4.csv.gz', index=False, compression='gzip')
    print(f"Reviews exported successfully! ({len(df_combined_reviews)} rows)")
else:
    print("No reviews were found or all reviews were filtered out.")

# 7. Generate final_games.json using ONLY the games that survived the pipeline
if not df_combined_reviews.empty:
    print("Step 7: Generating final_games_4.json...")

    # Get the unique App IDs that have at least one valid review in our final corpus
    valid_app_ids = set(df_combined_reviews['App_ID'].astype(str).unique())

    final_games_dict = {}
    for app_id in valid_app_ids:
        if app_id in steam_data:
            game_obj = steam_data[app_id].copy()

            # Retrieve the Metacritic userscore we mapped earlier
            u_score = userscore_map.get(app_id)

            # Convert pandas NaN/NaT to Python None so it writes a valid JSON "null"
            if pd.isna(u_score):
                u_score = None

            game_obj['userscore'] = u_score
            final_games_dict[app_id] = game_obj

    # Export to JSON
    with open('data/processed/final_games_4.json', 'w', encoding='utf-8') as f:
        json.dump(final_games_dict, f, indent=4)

    print(f"Metadata exported to 'final_games_4.json' for {len(final_games_dict)} games!")