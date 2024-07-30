import pandas as pd
import pickle
import os
import matplotlib.pyplot as plt
import textwrap

# Define a custom exception for exceeding client count
class ClientCountError(Exception):
    pass

def distribute_data(df, num_clients):
    total_rows = len(df)
    rows_per_client = total_rows // num_clients
    client_data = []
    dataset_sizes = {}

    # Create directory if it doesn't exist
    os.makedirs('client_models', exist_ok=True)

    # Distribute rows to clients
    start_idx = 0
    for client_id in range(1, num_clients + 1):
        end_idx = min(start_idx + rows_per_client, total_rows)
        client_df = df.iloc[start_idx:end_idx].copy()  # Copy to avoid modifying the original df
        client_filename = f'client_models/client_data_{client_id}.pkl'
        with open(client_filename, 'wb') as f:
            pickle.dump(client_df, f)
        client_data.append(client_df)
        dataset_sizes[client_id] = len(client_df)  # Track size
        start_idx = end_idx

    # Handle remaining rows if any
    if start_idx < total_rows:
        last_client_df = pd.concat([client_data[-1], df.iloc[start_idx:]])
        client_data[-1] = last_client_df
        dataset_sizes[num_clients] = len(last_client_df)  # Update size for the last client

    return client_data, dataset_sizes

def find_top_songs(client_df):
    client_df['track_popularity'] = pd.to_numeric(client_df['track_popularity'], errors='coerce').astype('Int64')
    top_indices = client_df['track_popularity'].nlargest(3).index
    top_songs = []
    for idx in top_indices:
        song_title = client_df.loc[idx, 'track_name']
        artist_name = client_df.loc[idx, 'track_artist']
        track_genre = client_df.loc[idx, 'playlist_genre']
        popularity = client_df.loc[idx, 'track_popularity']
        top_songs.append((popularity, f"{song_title} - {artist_name} ({track_genre})"))
    return top_songs

def plot_song_popularity(song_popularity, basename):
    if not song_popularity:
        print("No song popularity data to plot.")
        return

    plt.figure(figsize=(12, 8))

    if len(song_popularity) == 0:
        print("No data available for plotting.")
        plt.close()
        return

    songs, popularities = zip(*song_popularity)
    
    # Create a bar graph
    bars = plt.bar(songs, popularities, color='skyblue', align='center')

    # Set the maximum width of x-tick labels to wrap them
    max_label_width = 20  # Adjust this value based on your needs

    # Wrap x-tick labels
    wrapped_labels = [textwrap.fill(song, width=max_label_width) for song in songs]

    # Set x-tick labels
    plt.xticks(ticks=range(len(songs)), labels=wrapped_labels, rotation=0, ha='center', fontsize=12)

    # Add labels (song names) centered on the bars
    for bar in bars:
        width = bar.get_width()
        x = bar.get_x() + width / 2  # Calculate the x position to center the text
        height = bar.get_height()
        # Place text at the top of each bar
        plt.text(x, height + 0.5, f'{height:.2f}', ha='center', va='bottom', color='black', fontsize=14)

    # Set font size for x and y labels and title
    plt.xlabel('Songs', fontsize=16)
    plt.ylabel('Average Popularity', fontsize=16)
    plt.title('Aggregated Popularity of Top Songs', fontsize=16)
    
    plt.yticks(fontsize=16)
    
    plt.tight_layout()
    
    # Save the figure with basename
    plt.savefig(f'{basename}_aggregated_song_popularity.png')
    plt.close()

def main():
    # Read datasets
    df = pd.read_csv('spotify_songs.csv', low_memory=False)   
    results_filename = '0.5_fa_ns3_results.csv'			 # The filename for results CSV and output graph
    results_df = pd.read_csv(results_filename)

    # Strip whitespace from column names
    df.columns = df.columns.str.strip()
    results_df.columns = results_df.columns.str.strip()

    # Extract basename from results CSV file for plotting
    results_basename = os.path.splitext(os.path.basename(results_filename))[0]

    # Number of clients for fixed distribution
    num_clients = len(results_df['Client'].unique())
    min_limit = 0.25  # values: 0, 0.25, 0.5, 0.75, 1
    selected_clients = abs(min_limit)

    # Validate number of clients
    if num_clients <= 0:
        print("Error: Number of clients must be greater than 0.")
        return

    # Distribute data to clients
    client_data, dataset_sizes = distribute_data(df, num_clients)
    
    # Print dataset sizes for each client
    #print("\nDataset size for each client:")
    #for client_id in range(1, num_clients + 1):
     #   print(f"Client ID {client_id}: {dataset_sizes.get(client_id, 0)} rows")

    #print()

    # Filter clients based on Rx_Packets and Tx_Packets condition
    filtered_clients = results_df[results_df['Rx_Packets'] >= selected_clients * results_df['Tx_Packets']]
    reliable_client_ids = filtered_clients['Client'].unique()

    if len(reliable_client_ids) == 0:
        print("Error: All clients failed to transmit")
        return

    try:
        # Ensure reliable_client_ids does not exceed num_clients
        if len(reliable_client_ids) > num_clients:
            raise ClientCountError(f"Error: Number of selected clients ({len(reliable_client_ids)}) exceeds the total number of clients ({num_clients}).")

        # Initialize counters and lists
        successful_client_count = 0
        successful_client_ids = []
        results_from_clients = []

        # Load data from clients and query
        for client_id in reliable_client_ids:
            client_filename = f'client_models/client_data_{client_id}.pkl'
            if os.path.exists(client_filename):
                with open(client_filename, 'rb') as f:
                    client_df = pickle.load(f)
                top_songs = find_top_songs(client_df)
                results_from_clients.extend(top_songs)
                successful_client_count += 1
                successful_client_ids.append(client_id)

        if not results_from_clients:
            print("No song popularity data available from clients.")
            return

        # Aggregate results from all clients by averaging popularity
        song_popularity = {}
        song_counts = {}
        for popularity, song in results_from_clients:
            if song not in song_popularity:
                song_popularity[song] = 0
                song_counts[song] = 0
            song_popularity[song] += popularity
            song_counts[song] += 1

        # Calculate average popularity
        for song in song_popularity:
            song_popularity[song] /= song_counts[song]

        # Sort songs by their average popularity in descending order
        sorted_songs = sorted(song_popularity.items(), key=lambda x: -x[1])

        # Get the top 3 songs
        final_top_songs = sorted_songs[:3]

        # Plot the averaged popularity of top songs
        plot_song_popularity(final_top_songs, results_basename)

        # Output the final results and performance metrics
        print(f"\nTotal number of clients: {num_clients}")
        print(f"Number of selected Clients: {len(reliable_client_ids)}")
        print(f"\nQuery: What are the current top 3 most popular songs?")

        print("\nThe aggregated top 3 most popular songs are:")
        for idx, (song, popularity) in enumerate(final_top_songs, start=1):
            print(f"{idx}. {song} with averaged popularity {popularity:.2f}")
        print()
    except ClientCountError as e:
        print(e)

if __name__ == "__main__":
    main()

