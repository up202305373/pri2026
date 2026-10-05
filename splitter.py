import pandas as pd
import math

print("Loading the massive dataset...")
df = pd.read_csv('data/processed/Final_Search_Corpus_4.csv.gz', compression='gzip')

print("Splitting into 3 parts...")
num_chunks = 3
chunk_size = math.ceil(len(df) / num_chunks)

for i in range(num_chunks):
    start = i * chunk_size
    end = min((i + 1) * chunk_size, len(df))

    chunk = df.iloc[start:end]

    filename = f'data/processed/Final_Search_Corpus_part_{i+1}.csv.gz'
    print(f"Exporting {filename} with {len(chunk)} rows...")
    chunk.to_csv(filename, index=False, compression='gzip')

print("Done! You can now commit the 3 split files.")