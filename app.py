
import pickle
import random
from pathlib import Path

import requests
import streamlit as st


# ==================================================
# 1. CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="CineMatch | Movie Discovery",
    page_icon="🎬",
    layout="wide",
)

TMDB_API_KEY = TMDB_API_KEY = st.secrets.get("TMDB_API_KEY", "")

MOVIES_FILE = "movies_dict (5).pkl"
SIMILARITY_FILE = "similarity (5).pkl"

POSTER_BASE = "https://image.tmdb.org/t/p/w500"


# ==================================================
# 2. CLEAN CINEMATIC STYLING
# ==================================================

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');

    .stApp {
        background:
            radial-gradient(ellipse at 5% 0%, #38233d 0%, transparent 35%),
            radial-gradient(ellipse at 95% 5%, #202c50 0%, transparent 38%),
            linear-gradient(135deg, #171824, #111522 55%, #1c1728);
        color: #f6f6fc;
        font-family: 'DM Sans', sans-serif;
    }

    #MainMenu, footer {
        visibility: hidden;
    }

    header[data-testid="stHeader"] {
        background: transparent;
    }

    .block-container {
        max-width: 1380px;
        padding-top: 1.5rem;
        padding-bottom: 4rem;
    }

    h1, h2, h3 {
        font-family: 'Space Grotesk', sans-serif !important;
        letter-spacing: -0.6px;
    }

    .brand {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 28px;
        font-weight: 700;
        margin-bottom: 36px;
    }

    .brand-accent {
        color: #ff5a80;
    }

    .eyebrow {
        color: #ff91aa;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 2.5px;
    }

    .hero-copy {
        color: #bdc0d2;
        font-size: 15px;
        line-height: 1.8;
        max-width: 650px;
    }

    .section-caption {
        color: #b7b9cb;
        font-size: 13px;
    }

    div[data-baseweb="select"] > div {
        background: #252638;
        border: 1px solid #45465b;
        border-radius: 12px;
        min-height: 48px;
    }

    div[data-baseweb="select"] > div:hover {
        border-color: #ff5a80;
    }

    div[data-testid="stButton"] > button {
        min-height: 43px;
        border-radius: 12px;
        font-weight: 600;
        border: 1px solid #414257;
        background: #252638;
        color: #ffffff;
        transition: all .2s ease;
    }

    div[data-testid="stButton"] > button:hover {
        transform: translateY(-2px);
        border-color: #ff6688;
        box-shadow: 0 7px 22px rgba(255, 80, 120, .18);
        color: white;
    }

    div[data-testid="stButton"] > button[kind="primary"] {
        background: linear-gradient(110deg, #ff426b, #d63883);
        border: none;
    }

    div[data-testid="stButton"] > button[kind="primary"]:hover {
        background: linear-gradient(110deg, #ff6080, #eb4995);
    }

    div[data-testid="stImage"] {
        overflow: hidden;
        border-radius: 17px;
        border: 1px solid rgba(255,255,255,.10);
        background: #27283a;
        box-shadow: 0 8px 24px rgba(0,0,0,.18);
    }

    div[data-testid="stImage"] img {
        display: block;
        border-radius: 17px;
        transition: transform .3s ease, filter .3s ease;
    }

    div[data-testid="stImage"]:hover img {
        transform: scale(1.045);
        filter: brightness(1.08);
    }

    div[data-testid="stMetric"] {
        background: rgba(43, 44, 64, .85);
        border: 1px solid rgba(255,255,255,.10);
        padding: 13px;
        border-radius: 14px;
    }

    div[data-testid="stMetricLabel"] {
        color: #c2c3d4;
    }

    div[data-testid="stMetricValue"] {
        color: #ffffff;
    }

    hr {
        border-color: rgba(255,255,255,.12);
        margin-top: 30px;
        margin-bottom: 30px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ==================================================
# 3. LOAD THE EXISTING ML MODEL
# ==================================================

@st.cache_resource
def load_data():
    folder = Path(__file__).resolve().parent

    movies_path = folder / MOVIES_FILE
    similarity_path = folder / SIMILARITY_FILE

    if not movies_path.exists():
        raise FileNotFoundError(f"Missing {MOVIES_FILE}")

    if not similarity_path.exists():
        raise FileNotFoundError(f"Missing {SIMILARITY_FILE}")

    with open(movies_path, "rb") as file:
        movies_data = pickle.load(file)

    with open(similarity_path, "rb") as file:
        similarity_data = pickle.load(file)

    if "title" not in movies_data.columns:
        raise ValueError("Movies data must contain a title column.")

    if len(movies_data) != len(similarity_data):
        raise ValueError(
            "The movies and similarity files do not match."
        )

    return movies_data.reset_index(drop=True), similarity_data


try:
    movies, similarity = load_data()
except Exception as error:
    st.error(f"Could not load model: {error}")
    st.stop()


movie_titles = (
    movies["title"]
    .dropna()
    .astype(str)
    .drop_duplicates()
    .tolist()
)

if not movie_titles:
    st.error("No movie titles found.")
    st.stop()


# ==================================================
# 4. SESSION STATE AND BUTTON CALLBACKS
# ==================================================

if "movie_picker" not in st.session_state:
    st.session_state.movie_picker = movie_titles[0]

if st.session_state.movie_picker not in movie_titles:
    st.session_state.movie_picker = movie_titles[0]

if "detail_movie" not in st.session_state:
    st.session_state.detail_movie = None


def surprise_movie():
    current = st.session_state.movie_picker

    choices = [
        title for title in movie_titles
        if title != current
    ]

    if choices:
        st.session_state.movie_picker = random.choice(choices)

    st.session_state.detail_movie = None


def show_details(title):
    st.session_state.detail_movie = title


def close_details():
    st.session_state.detail_movie = None


# ==================================================
# 5. RECOMMENDATION FUNCTION
# ==================================================

def recommend(movie):
    matching = movies.index[
        movies["title"].astype(str).str.casefold()
        == str(movie).casefold()
    ].tolist()

    if not matching:
        return []

    movie_index = matching[0]

    scores = list(enumerate(similarity[movie_index]))
    scores.sort(key=lambda item: item[1], reverse=True)

    results = []

    for index, score in scores[1:]:
        title = str(movies.iloc[index]["title"])

        if title.casefold() == str(movie).casefold():
            continue

        if title not in results:
            results.append(title)

        if len(results) == 5:
            break

    return results


# ==================================================
# 6. FETCH TMDB DETAILS
# ==================================================

@st.cache_data(ttl=3600, show_spinner=False)
def get_movie_details(title):
    if (
        not TMDB_API_KEY
        or TMDB_API_KEY == "PASTE_YOUR_TMDB_API_KEY_HERE"
    ):
        return None

    try:
        response = requests.get(
            "https://api.themoviedb.org/3/search/movie",
            params={
                "api_key": TMDB_API_KEY,
                "query": title,
                "include_adult": False,
            },
            timeout=10,
        )
        response.raise_for_status()

        results = response.json().get("results", [])

        if not results:
            return None

        movie = next(
            (
                item for item in results
                if item.get("title", "").casefold()
                == title.casefold()
            ),
            results[0],
        )

        movie_id = movie.get("id")

        if movie_id:
            detail_response = requests.get(
                f"https://api.themoviedb.org/3/movie/{movie_id}",
                params={"api_key": TMDB_API_KEY},
                timeout=10,
            )

            if detail_response.ok:
                return detail_response.json()

        return movie

    except (requests.RequestException, ValueError):
        return None


def get_poster(details):
    if not details:
        return None

    poster_path = details.get("poster_path")

    if poster_path:
        return f"{POSTER_BASE}{poster_path}"

    return None


# ==================================================
# 7. HERO - NATIVE STREAMLIT TEXT, NO HTML HERO
# ==================================================

st.markdown(
    '<div class="brand">🎬 Cine<span class="brand-accent">Match</span></div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="eyebrow">YOUR PERSONAL MOVIE DISCOVERY APP</div>',
    unsafe_allow_html=True,
)

st.title("Your next favourite movie is waiting.")

st.markdown(
    """
    <div class="hero-copy">
        Explore movies, discover hidden gems, and find your next
        watch with recommendations powered by machine learning.
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("")


# ==================================================
# 8. SEARCH AND SURPRISE
# ==================================================

st.subheader("Find your movie")

st.markdown(
    '<div class="section-caption">Choose a movie you love, or let CineMatch surprise you.</div>',
    unsafe_allow_html=True,
)

search_col, surprise_col = st.columns([4, 1.25], gap="medium")

with search_col:
    st.selectbox(
        "Search movie titles",
        options=movie_titles,
        key="movie_picker",
    )

with surprise_col:
    st.write("")
    st.write("")

    st.button(
        "🎲 Surprise me",
        key="surprise_button",
        use_container_width=True,
        on_click=surprise_movie,
    )

selected_movie = st.session_state.movie_picker

button_col, empty_col = st.columns([1.7, 4])

with button_col:
    if st.button(
        "✨ Discover similar movies",
        type="primary",
        use_container_width=True,
    ):
        st.session_state.detail_movie = None
        st.rerun()


# ==================================================
# 9. SELECTED MOVIE
# ==================================================

selected_details = get_movie_details(selected_movie)
selected_poster = get_poster(selected_details)

st.divider()
st.subheader("Movie spotlight")
st.caption("A closer look at your selected movie.")

poster_col, info_col = st.columns([1, 2.15], gap="large")

with poster_col:
    if selected_poster:
        st.image(selected_poster, use_container_width=True)
    else:
        st.info("Poster unavailable. Check your TMDB API key.")

with info_col:
    st.markdown(
        '<div class="eyebrow">NOW IN THE SPOTLIGHT</div>',
        unsafe_allow_html=True,
    )

    st.header(selected_movie)

    if selected_details:
        rating = selected_details.get("vote_average", 0) or 0
        votes = selected_details.get("vote_count", 0) or 0

        release_date = selected_details.get("release_date", "")
        year = release_date[:4] if release_date else "N/A"

        overview = selected_details.get(
            "overview",
            "No overview available.",
        )

        metric1, metric2, metric3 = st.columns(3)

        metric1.metric("⭐ TMDB Rating", f"{rating:.1f}/10")
        metric2.metric("Release Year", year)
        metric3.metric("TMDB Votes", f"{votes:,}")

        genres = selected_details.get("genres", [])

        if genres:
            st.write(
                "**Genres:** "
                + " · ".join(
                    genre.get("name", "")
                    for genre in genres
                )
            )

        st.write(overview)

        if release_date:
            st.caption(f"Release date: {release_date}")

    else:
        st.info(
            "Details unavailable. Check your TMDB API key and internet connection."
        )


# ==================================================
# 10. RECOMMENDATIONS
# ==================================================

st.divider()
st.subheader("Picked for you ✨")
st.caption(f"Movies similar to {selected_movie}")

recommended_movies = recommend(selected_movie)

if not recommended_movies:
    st.warning("No similar movies found for this title.")
else:
    columns = st.columns(5, gap="medium")

    for index, title in enumerate(recommended_movies):
        details = get_movie_details(title)

        poster = get_poster(details)

        rating = (
            details.get("vote_average", 0) or 0
            if details else 0
        )

        votes = (
            details.get("vote_count", 0) or 0
            if details else 0
        )

        release_date = (
            details.get("release_date", "")
            if details else ""
        )

        year = release_date[:4] if release_date else "N/A"

        overview = (
            details.get("overview", "")
            if details else ""
        )

        with columns[index]:
            if poster:
                st.image(poster, use_container_width=True)
            else:
                st.info("Poster unavailable")

            st.markdown(f"**{title}**")
            st.caption(f"⭐ {rating:.1f}/10  ·  {year}")

            if overview:
                short_overview = overview[:130].strip()

                if len(overview) > 130:
                    short_overview += "..."

                st.write(short_overview)
            else:
                st.write("No description available.")

            st.caption(f"{votes:,} TMDB votes")

            st.button(
                "View details ↗",
                key=f"details_{index}",
                use_container_width=True,
                on_click=show_details,
                args=(title,),
            )


# ==================================================
# 11. MOVIE DETAILS
# ==================================================

detail_title = st.session_state.detail_movie

if detail_title:
    details = get_movie_details(detail_title)

    st.divider()
    st.subheader(f"Movie details: {detail_title}")

    detail_poster_col, detail_info_col = st.columns(
        [1, 2],
        gap="large",
    )

    with detail_poster_col:
        poster = get_poster(details)

        if poster:
            st.image(poster, use_container_width=True)
        else:
            st.info("Poster unavailable.")

    with detail_info_col:
        if details:
            rating = details.get("vote_average", 0) or 0
            votes = details.get("vote_count", 0) or 0

            st.metric("TMDB Rating", f"{rating:.1f}/10")
            st.write(
                "**Release date:** "
                + details.get("release_date", "Not available")
            )
            st.write(f"**TMDB votes:** {votes:,}")

            genres = details.get("genres", [])

            if genres:
                st.write(
                    "**Genres:** "
                    + ", ".join(
                        genre.get("name", "")
                        for genre in genres
                    )
                )

            st.write(
                details.get("overview", "No overview available.")
            )

            homepage = details.get("homepage", "")

            if homepage.startswith("https://"):
                st.link_button(
                    "Visit official movie website ↗",
                    homepage,
                )
        else:
            st.info("Additional details are unavailable.")

    st.button(
        "← Close details",
        on_click=close_details,
    )


# ==================================================
# 12. FOOTER
# ==================================================

st.divider()

st.caption(
    "CineMatch · Movie metadata and ratings provided by TMDB. "
    "This product uses the TMDB API but is not endorsed or certified by TMDB."
)
