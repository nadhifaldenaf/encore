from flask import Flask, redirect, request, session, render_template, send_file
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
from generate_image import generate_story
from io import BytesIO
import spotipy
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

sp_oauth = SpotifyOAuth(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
    redirect_uri=os.getenv("REDIRECT_URI", "http://127.0.0.1:5000/callback"),
    scope="user-top-read user-read-recently-played"
)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login")
def login():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route("/callback")
def callback():
    code = request.args.get("code")
    token_info = sp_oauth.get_access_token(code)
    session["token"] = token_info["access_token"]
    return redirect("/customize")

@app.route("/customize")
def customize():
    token = session.get("token")
    if not token:
        return redirect("/")
    sp = spotipy.Spotify(auth=token)
    user_info = sp.current_user()
    user_name = user_info["display_name"]
    user_image = user_info["images"][0]["url"] if user_info["images"] else None
    return render_template("customize.html", user_name=user_name, user_image=user_image)

def get_receipt_data(sp, time_range, show, length):
    time_range_label = {
        "short_term": "Last Month",
        "medium_term": "Last 6 Months",
        "long_term": "All Time"
    }

    user_info = sp.current_user()
    user_name = user_info["display_name"]
    user_image = user_info["images"][0]["url"] if user_info["images"] else None

    # Top Tracks
    tracks = []
    if show in ["tracks", "both"]:
        hasil_tracks = sp.current_user_top_tracks(limit=length, time_range=time_range)
        for item in hasil_tracks["items"]:
            tracks.append({
                "title": item["name"],
                "artist": item["artists"][0]["name"],
                "url": item["external_urls"]["spotify"],
            })

    # Top Artists
    artists = []
    artist_cover = None
    hasil_artists = sp.current_user_top_artists(limit=length, time_range=time_range)
    for i, item in enumerate(hasil_artists["items"]):
        if show in ["artists", "both"]:
            artists.append({
                "name": item["name"],
                "url": item["external_urls"]["spotify"],
            })
        if i == 0 and item["images"]:
            artist_cover = item["images"][0]["url"]

    # Most Repeated Artist
    artist_count = {}
    for track in tracks:
        artist = track["artist"]
        artist_count[artist] = artist_count.get(artist, 0) + 1
    most_repeated = max(artist_count, key=artist_count.get) if artist_count else "-"
    most_repeated_count = artist_count.get(most_repeated, 0)

    if most_repeated_count >= 3:
        loyalty_badge = f"Ride or Die: {most_repeated}"
    elif most_repeated_count == 2:
        loyalty_badge = f"Big Fan: {most_repeated}"
    else:
        loyalty_badge = "Explorer"

    # Listening Personality
    semua_artist = " ".join([track["artist"].lower() for track in tracks])
    if any(a in semua_artist for a in ["mgk", "killswitch", "avenged", "lil peep"]):
        personality = "The Dark Horse"
        personality_desc = "Intense dan penuh emosi. Musik buat kamu bukan hiburan — ini terapi."
    elif any(a in semua_artist for a in ["axwell", "alan walker", "swedish house", "alesso"]):
        personality = "The Festival Kid"
        personality_desc = "EDM, drop, dan crowd — kamu hidup di momen itu."
    elif any(a in semua_artist for a in ["cigarettes after sex", "the 1975", "sting"]):
        personality = "The Hopeless Romantic"
        personality_desc = "Kamu dengerin musik sambil ngelamun. Lirik lebih penting dari beat."
    elif any(a in semua_artist for a in ["don toliver", "harry styles", "dua lipa"]):
        personality = "The Vibe Curator"
        personality_desc = "Playlist kamu selalu enak didengerin."
    else:
        personality = "The Eclectic Listener"
        personality_desc = "Taste musik kamu susah ditebak — dan itu keren."

    # #1 All Time
    hasil_alltime = sp.current_user_top_artists(limit=1, time_range="long_term")
    top_artist_alltime = hasil_alltime["items"][0]["name"] if hasil_alltime["items"] else "Unknown"

    # Unique Artists
    unique_artists = list(set([track["artist"] for track in tracks]))
    total_unique_artists = len(unique_artists)

    # Consistency
    hasil_short = sp.current_user_top_artists(limit=5, time_range="short_term")
    hasil_long = sp.current_user_top_artists(limit=5, time_range="long_term")
    short_names = set([a["name"] for a in hasil_short["items"]])
    long_names = set([a["name"] for a in hasil_long["items"]])
    overlap_count = len(short_names.intersection(long_names))

    if overlap_count >= 3:
        consistency = "Consistent Listener"
        consistency_desc = "Artis favoritmu tidak banyak berubah."
    elif overlap_count >= 1:
        consistency = "Balanced Explorer"
        consistency_desc = "Punya selera tetap, tapi masih suka eksplor."
    else:
        consistency = "True Explorer"
        consistency_desc = "Taste musikmu terus berkembang."

    return {
        "user_name": user_name,
        "user_image": user_image,
        "tracks": tracks,
        "artists": artists,
        "artist_cover": artist_cover,
        "personality": personality,
        "personality_desc": personality_desc,
        "loyalty_badge": loyalty_badge,
        "most_repeated": most_repeated,
        "most_repeated_count": most_repeated_count,
        "time_range": time_range,
        "time_range_label": time_range_label,
        "top_artist_alltime": top_artist_alltime,
        "total_unique_artists": total_unique_artists,
        "consistency": consistency,
        "consistency_desc": consistency_desc,
        "show": show,
        "length": length,
    }

@app.route("/receipt")
def receipt():
    token = session.get("token")
    if not token:
        return redirect("/")

    time_range = request.args.get("time_range", "short_term")
    show = request.args.get("show", "both")
    length = int(request.args.get("length", 10))

    sp = spotipy.Spotify(auth=token)
    data = get_receipt_data(sp, time_range, show, length)

    return render_template("receipt.html", **data)

@app.route("/download")
def download():
    token = session.get("token")
    if not token:
        return redirect("/")

    time_range = request.args.get("time_range", "short_term")
    show = request.args.get("show", "both")
    length = int(request.args.get("length", 10))

    sp = spotipy.Spotify(auth=token)
    data = get_receipt_data(sp, time_range, show, length)

    img = generate_story(data)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    return send_file(buf, mimetype="image/png", as_attachment=True, download_name="encore-receipt.png")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)