import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv
import random

load_dotenv()
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
redirect_uri = os.getenv("REDIRECT_URI")
scope = os.getenv("SCOPE")

# functions
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id,
                                               client_secret=client_secret,
                                               redirect_uri=redirect_uri,
                                               scope=scope))


def intro():
    print('\nWelcome to the Spotify API Recommendation Tool!')
    print('\nSelect feature:')
    print(' 1. Show my top songs')
    print(' 2. Show my top artists')
    print(' 3. Show my recent songs')
    print(' 4. Show my recent artists')
    print(' 5. Give me recommendations')
    feature = str(input('\nEnter number (1-5): '))
    return feature


def remote_auth():
    sp_oauth = SpotifyOAuth(client_id, client_secret, redirect_uri, scope)
    authorize_url = sp_oauth.get_authorize_url()
    # getting authorization through spotify URL to acquire access token

    print(f'Go to this URL to authorize: {authorize_url}')

    access_token = sp_oauth.get_cached_token()

    # change authorization to access token
    sp_oauth = spotipy.Spotify(auth=access_token)

    return sp_oauth


def get_recent_tracks_df():
    track_name = []
    artist = []
    album = []
    release_date = []
    popularity = []
    duration = []

    # accessing recently played tracks
    recently_played = sp.current_user_recently_played()

    # for the last 50 tracks in user's recently played, collect these pieces of info
    # and put them in a dataframe
    for track in recently_played['items']:
        track_name.append(track['track']['name'])
        artist.append(", ".join([artist['name'] for artist in track['track']['artists']]))
        album.append(track['track']['album']['name'])
        release_date.append(track['track']['album']['release_date'])
        popularity.append(track['track']['popularity'])
        duration.append(track['track']['duration_ms'])

    recent_tracks_df = pd.DataFrame({'track': track_name, 'artist': artist, 'album': album,
                                     'release_date': release_date, 'popularity': popularity,
                                     'duration_ms': duration})
    # changing release date column to release year for consistency
    recent_tracks_df['release_date'] = recent_tracks_df['release_date'].str[:4]
    recent_tracks_df = recent_tracks_df.rename(columns={'release_date': 'release_year'})

    return recent_tracks_df


def get_recent_tracks(recently_played: dict):
    """Dictionary of recent tracks and their id."""
    recent_tracks_id = {track['track']['name']: track['track']['id'] for track in recently_played['items']}
    return recent_tracks_id


def get_recent_artists(recently_played: dict):
    """Dictionary of recent artists and their id."""
    recent_artists_id = {}
    for track in recently_played['items']:
        for artist in track['track']['artists']:
            name = artist['name']
            artist_id = artist['id']
            recent_artists_id[name] = artist_id
    return recent_artists_id


def get_top_artists(time_period: str):
    """Returns dictionary of most listened to artists based on period of time defined by user."""
    top_artists = sp.current_user_top_artists(time_range=time_period)
    # dictionaries of top artists/tracks mapped to their id
    top_artists_id = {artist['name']: artist['id'] for artist in top_artists['items']}
    return top_artists_id


def get_top_tracks(time_period: str):
    """Returns dictionary of most listened to tracks based on period of time defined by user."""
    top_tracks = sp.current_user_top_tracks(time_range=time_period)
    top_tracks_id = {f"{track['name']} - {', '.join(artist['name'] for artist in track['artists'])}":
                     track['id'] for track in top_tracks['items']}
    return top_tracks_id


def generate_rec_seeds(seed, id_dict: dict, id_dict2=None):
    """Generates seed artists/tracks/both from random samples from top artists/tracks."""
    if seed == 'artists':
        seed_artists = []
        for artist in range(5):
            seed_artists.append(random.choice(list(id_dict.values())))
        return seed_artists
    elif seed == 'songs':
        seed_tracks = []
        for track in range(5):
            seed_tracks.append(random.choice(list(id_dict.values())))
        return seed_tracks
    elif seed == 'both':
        seed_both_tracks = []
        seed_both_artists = []
        for track in range(2):
            seed_both_tracks.append(random.choice(list(id_dict.values())))
        for artist in range(3):
            seed_both_artists.append(random.choice(list(id_dict2.values())))
        return seed_both_artists, seed_both_tracks


def genre_seeds():
    """Generates seeds for recommendations based on genre."""
    approved_genres = sp.recommendation_genre_seeds()['genres']
    # creating list of genres from user input as long as they exist in approved genres
    seed_genres = []
    user_genres = str(input(
        'Enter up to 5 genres such as classical, latin, or heavy-metal (enter stop to stop): ')).lower()

    # collect up to 5 genres from user input
    while user_genres != 'stop' and len(seed_genres) < 5:
        if user_genres not in approved_genres:
            print('Uncrecognized genre, please try again.')
            user_genres = str(input(
                'Enter up to 5 genres such as classical, latin, or heavy-metal (enter stop to stop): '
            )).lower()
            continue
        seed_genres.append(user_genres)
        user_genres = str(input(
            'Enter up to 5 genres such as classical, latin, or heavy-metal (enter stop to stop): '
        )).lower()
    return seed_genres


def rec(recommendations: dict):
    """Dictionary of recommended songs and artists as key and id as value."""
    rec_dict = {}
    for track in recommendations['tracks']:
        rec_name = track['name']
        rec_artist = ", ".join([artist['name'] for artist in track['artists']])
        rec_id = track['id']
        rec_dict[f"{rec_name} - {rec_artist}"] = rec_id
    return rec_dict


def make_rec_playlist(visibility: bool, rec_dict):
    """Access id of current user and create new playlist of recommendations."""
    user_id = sp.me()['id']
    rec_playlist = sp.user_playlist_create(user=user_id,
                                           name='Spotify API Recommendations',
                                           public=visibility,
                                           description='Playlist of recommendations '
                                                       'generated for you by Spotify API.')
    sp.playlist_add_items(playlist_id=rec_playlist['id'], items=list(rec_dict.values()))
    print('Playlist "Spotify API Recommendations" created.')


def main():
    feature = intro()
    while feature not in ['1', '2', '3',
                          '4', '5', '6']:
        print('Answer not recognized. Please try again.')
        feature = intro()
    sp = remote_auth()
    if feature == '1':
        # show top songs
        time_period = str(input('Show top songs from which time period '
                                '(past month, 6 months, all time?)?: ')).lower()
        while time_period not in ['past month', 'month', 'past 6 months',
                                  '6 months', 'all time', 'all-time']:
            print('Answer not recognized. Please try again.')
            time_period = str(input('Show top songs from which time period '
                                    '(past month, 6 months, all time?)?: ')).lower()
        if time_period in ['past month', 'month']:
            time_period = 'short_term'
        elif time_period in ['past 6 months', '6 months']:
            time_period = 'medium_term'
        else:
            time_period = 'long_term'

        top_tracks = get_top_tracks(time_period).keys()
        for track in top_tracks:
            print(track)

    elif feature == '2':
        # show top artists



main()
