import pandas as pd

# Step 1: Read the dataset
df = pd.read_csv('spotify_songs.csv', low_memory=False)  # Specify low_memory=False to handle mixed types warning

# Strip whitespace from column names
df.columns = df.columns.str.strip()

# Ensure 'track_popularity' column is numeric
df['track_popularity'] = pd.to_numeric(df['track_popularity'], errors='coerce').astype('Int64')

# The query
query = "What are the current top 3 most popular songs?"

# Function to find top songs
def find_top_songs(df):
    # Sort dataframe by 'track_popularity' in descending order
    df_sorted = df.sort_values(by='track_popularity', ascending=False)
    # Take top 3 rows after sorting
    top_songs = []
    for rank in range(3):
        song_title = df_sorted.iloc[rank]['track_name']
        artist_name = df_sorted.iloc[rank]['track_artist']
        track_genre = df_sorted.iloc[rank]['playlist_genre']
        popularity = df_sorted.iloc[rank]['track_popularity']
        top_songs.append((popularity, f"{song_title} - {artist_name} ({track_genre})"))
    return top_songs

# Querying all data
top_songs = find_top_songs(df)

# Output the final results and performance metrics
print(f"Query: {query}")

print()

print("The top 3 most popular songs are:")
for idx, (popularity, song) in enumerate(top_songs):
    print(f"{idx + 1}. {song} with popularity {popularity}")

print()

