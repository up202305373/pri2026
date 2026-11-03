import os
import re
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter

def tokenize(text): return re.findall(r"\b[\w']+\b", str(text).lower())

def dist_review_lengths():
    df = pd.read_csv("data/processed/Final_Search_Corpus.csv.gz",compression="gzip")
    reviews = df["review"].dropna()
    word_counts = reviews.apply(lambda x: len(tokenize(x)))

    plt.figure(figsize=(10, 6))
    plt.hist(word_counts, bins=50, edgecolor="black")
    plt.yscale("function", functions=(lambda x: x**0.5, lambda x: x**2))

    plt.axvline(word_counts.median(),linestyle=":",linewidth=2,label=f"Median = {word_counts.median():.0f} words")
    plt.axvline(word_counts.mean(),linestyle="--",linewidth=2,label=f"Mean = {word_counts.mean():.1f} words")

    plt.xlabel("Words per review")
    plt.ylabel("Number of reviews")
    plt.title("Distribution of Review Lengths")
    plt.legend()
    plt.tight_layout()

    os.makedirs("images", exist_ok=True)
    plt.savefig("images/reviewLengthDistribution.png",
                dpi=300, bbox_inches="tight")

def stopwords_by_review_length():
    df = pd.read_csv("data/processed/Final_Search_Corpus.csv.gz",compression="gzip")
    reviews = df["review"].dropna()
    stopwords = {"above","a","after","again","against","all","am","an","and","any","are","as","at","be","because","been","about","before","being","below","between","both","but","by","can","did","do","does","doing","don","down","during","each","few","for","from","further","had","has","have","having","he","her","here","hers","herself","him","himself","his","how","i","if","in","into","is","it","its","itself","just","me","more","most","my","myself","no","nor","not","now","of","off","on","once","only","or","other","our","ours","ourselves","out","over","own","s","same","she","should","so","some","such","t","than","that","the","their","theirs","them","themselves","then","there","these","they","this","those","through","to","too","under","until","up","very","was","we","were","what","when","where","which","while","who","whom","why","will","with","you","your","yours","yourself","yourselves"}
    results = []

    for review in reviews:
        tokens = tokenize(review)

        if not tokens: continue

        length = len(tokens)
        stopword_count = sum(1 for token in tokens if token in stopwords)

        results.append({"length": length,"stopword_percentage": 100 * stopword_count / length})

    stats = pd.DataFrame(results)
    average_review_percentage = stats["stopword_percentage"].mean()

    print(f"Average per-review stopword percentage: {average_review_percentage:.2f}%")

    bins = [0, 100, 200, 500, 1000, float("inf")]
    labels = ["1–100", "101–200", "201–500", "501–1000", "1000+"]

    stats["length_group"] = pd.cut(stats["length"],bins=bins,labels=labels)
    grouped = stats.groupby("length_group",observed=False)["stopword_percentage"]

    means = grouped.mean()
    medians = grouped.median()
    counts = grouped.count()
    q25 = grouped.quantile(0.25)
    q75 = grouped.quantile(0.75)

    summary = pd.DataFrame({"Reviews": counts,"Mean (%)": means,"Median (%)": medians,"25th percentile (%)": q25,"75th percentile (%)": q75})

    print("\nStopword percentages by review length:")
    print(summary.round(2).to_string())

    x = range(len(labels))

    plt.figure(figsize=(11, 6))
    plt.plot(x,means,marker="o",linewidth=2,label="Mean per-review percentage")
    plt.fill_between(x,q25,q75,alpha=0.2,label="25th–75th percentile")
    plt.axhline(average_review_percentage,linestyle=":",linewidth=2,label=f"Overall per-review mean ({average_review_percentage:.2f}%)")

    plt.xticks(x, labels)
    plt.xlabel("Review length (number of tokens)")
    plt.ylabel("Stopwords (% of tokens per review)")
    plt.title("Stopword Proportion by Review Length")
    plt.legend()
    plt.tight_layout()

    os.makedirs("images", exist_ok=True)
    plt.savefig("images/stopwordsByReviewLength.png",dpi=300,bbox_inches="tight")
    plt.close()

    print("\nSaved: images/stopwordsByReviewLength.png")

def slurs_by_review_length():
    df = pd.read_csv("data/processed/Final_Search_Corpus.csv.gz",compression="gzip")
    reviews = df["review"].dropna()
    slurs = {"anal","anus","arse","ass","bastard","bitch","bollocks","boob","boobs","bugger","cock","crap","cunt","dick","dildo","dyke","fag","faggot","fuck","fucker","jizz","nigga","nigger","penis","piss","prick","pube","pussy","queer","rape","rapist","retard","scrotum","semen","shit","slut","spastic","tits","turd","twat","vagina","wank","whore"}
    results = []

    for review in reviews:
        tokens = tokenize(review)

        if not tokens:
            continue

        length = len(tokens)
        slur_count = sum(1 for token in tokens if token in slurs)

        results.append({"length": length,"slur_count": slur_count,"slur_percentage": 100 * slur_count / length,"contains_slur": slur_count > 0})

    stats = pd.DataFrame(results)

    total_tokens = sum(len(tokenize(review)) for review in reviews)
    total_slurs = stats["slur_count"].sum()

    corpus_percentage = ( 100 * total_slurs / total_tokens if total_tokens else 0)
    average_review_percentage = stats["slur_percentage"].mean()

    print(f"Corpus-wide slur percentage: {corpus_percentage:.4f}%")
    print(f"Average per-review slur percentage: {average_review_percentage:.4f}%")
    print(f"Total flagged tokens: {total_slurs:,}")
    print(f"Reviews containing at least one flagged word: "
          f"{stats['contains_slur'].sum():,} "
          f"({100 * stats['contains_slur'].mean():.4f}%)")

    bins = [0, 100, 200, 500, 1000, float("inf")]
    labels = ["1–100", "101–200", "201–500", "501–1000", "1000+"]

    stats["length_group"] = pd.cut(stats["length"],bins=bins,labels=labels)
    grouped = stats.groupby("length_group",observed=False)

    summary = grouped.agg(
        Reviews=("length", "count"),
        Flagged_tokens=("slur_count", "sum"),
        Mean_percentage=("slur_percentage", "mean"),
        Reviews_with_slurs=("contains_slur", "sum")
    )

    summary["Reviews_with_slurs (%)"] = (100 * summary["Reviews_with_slurs"] / summary["Reviews"])

    print("\nSlur statistics by review length:")
    print(summary.round(4).to_string())

    print("\nSlur statistics by review length:")
    print(summary.round(4).to_string())

    table_data = summary.round(4).reset_index()
    table_data.columns = ["Review\nlength","Reviews","Flagged\ntokens","Mean flagged\n(%)","Reviews with\nflagged terms","Reviews with flagged\nterms (%)"]

    fig, ax = plt.subplots(figsize=(12, 2.2))
    ax.axis("off")

    table = ax.table(cellText=table_data.values,colLabels=table_data.columns,cellLoc="center",loc="center",colWidths=[0.13, 0.12, 0.14, 0.14, 0.22, 0.25])
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.8)

    fig.canvas.draw()
    bbox = table.get_window_extent(fig.canvas.get_renderer())
    bbox = bbox.transformed(fig.dpi_scale_trans.inverted())

    plt.savefig("images/slurStatisticsTable.png",dpi=300,bbox_inches=bbox,pad_inches=0.02)
    plt.close()

    print("Saved: images/slurStatisticsTable.png")

def recommendation_by_playtime():
    df = pd.read_csv("data/processed/Final_Search_Corpus.csv.gz",compression="gzip")

    playtime_col = "playtime"
    recommendation_col = "recommend"
    df = df.dropna(subset=[playtime_col, recommendation_col]).copy()

    df["playtime_hours"] = df[playtime_col] / 60

    bins = [0, 1, 5, 20, 50, 100, float("inf")]
    labels = ["0–1", "1–5", "5–20","20–50", "50–100", "100+"]

    df["playtime_group"] = pd.cut(df["playtime_hours"],bins=bins,labels=labels,include_lowest=True)
    df = df.dropna(subset=["playtime_group"])
    counts = pd.crosstab(df["playtime_group"],df[recommendation_col])

    print("\nReview counts by playtime:")
    print(counts)

    recommendation_rate = (df.groupby("playtime_group", observed=False)[recommendation_col].apply(lambda x: (x == "Recommended").mean() * 100))
    print("\nRecommendation rate by playtime (%):")
    print(recommendation_rate.round(2))

    os.makedirs("images", exist_ok=True)

    ax = recommendation_rate.plot(kind="bar",figsize=(10, 6))

    ax.set_xlabel("Playtime (hours)")
    ax.set_ylabel("Recommended reviews (%)")
    ax.set_title("Steam Recommendation Rate by Playtime")
    ax.set_ylim(0, 100)

    plt.xticks(rotation=0)
    plt.tight_layout()

    plt.savefig("images/recommendationByPlaytime.png",dpi=300,bbox_inches="tight")
    plt.close()

    print("\nSaved: images/recommendationByPlaytime.png")

def vocabulary_analysis():
    df = pd.read_csv("data/processed/Final_Search_Corpus.csv.gz",compression="gzip")

    word_counts = Counter()
    for review in df["review"].dropna(): word_counts.update(tokenize(review))

    unique_words = len(word_counts)
    hapax = [word for word, count in word_counts.items() if count == 1]

    frequency_ranges = [
        ("Once", 1, 1),
        ("Twice", 2, 2),
        ("3–5 times", 3, 5),
        ("6–10 times", 6, 10),
        ("11–100 times", 11, 100),
        ("101–1,000 times", 101, 1000),
        ("Over 1,000 times", 1001, float("inf"))
    ]

    frequency_summary = []

    for label, lower, upper in frequency_ranges:
        count = sum(
            lower <= frequency <= upper
            for frequency in word_counts.values()
        )

        frequency_summary.append({
            "Frequency": label,
            "Unique_words": count,
            "Vocabulary_percentage": (
                100 * count / unique_words
                if unique_words else 0
            )
        })

    frequency_df = pd.DataFrame(frequency_summary)

    print("\nVocabulary frequency distribution:")
    print(frequency_df.round(2).to_string(index=False))

    os.makedirs("images", exist_ok=True)

    table_data = frequency_df.round(2)

    fig, ax = plt.subplots()
    ax.axis("off")

    table = ax.table(cellText=table_data.values,colLabels=table_data.columns,cellLoc="center",loc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.5)

    fig.canvas.draw()
    bbox = table.get_window_extent(fig.canvas.get_renderer())
    bbox = bbox.transformed(fig.dpi_scale_trans.inverted())

    plt.savefig("images/vocabularyFrequencyTable.png",dpi=300,bbox_inches=bbox,pad_inches=0.02)
    plt.close()

    print("\nSaved: images/vocabularyFrequencyTable.png")

    print("\nSample of 100 hapax legomena:")

    for word in sorted(hapax)[:100]: print(word)

    digit_words = [
        word for word in word_counts
        if any(char.isdigit() for char in word)]

    long_words = [
        word for word in word_counts
        if len(word) >= 20]

    print("\nPotentially unusual vocabulary:")
    print(f"Words containing digits: {len(digit_words):,}")
    print(f"Words with 20+ characters: {len(long_words):,}")

    print("\nExamples of words containing digits:")
    print(", ".join(sorted(digit_words)[:50]))

    print("\nExamples of words with 20+ characters:")
    print(", ".join(sorted(long_words)[:50]))

def main():
    options = {
        "1": ("Distribution of review lengths", dist_review_lengths),
        "2": ("Stopword proportion by review length",stopwords_by_review_length),
        "3": ("Slur proportion by review length", slurs_by_review_length),
        "4": ("Steam recommendations by playtime", recommendation_by_playtime),
        "5": ("Vocabulary and word frequency analysis", vocabulary_analysis),
    }

    print("Choose a plot to generate:")
    for key, (description, _) in options.items():
        print(f"{key}. {description}")

    choice = input("Enter your choice: ")

    if choice in options:
        options[choice][1]()
    else:
        print("Invalid choice.")

if __name__ == "__main__":
    main()
