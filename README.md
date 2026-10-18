# CineMatch 🎬

A content-based movie recommendation app built with Python and
Streamlit. CineMatch uses text features and cosine similarity to
recommend movies, and the TMDB API to fetch available movie details and
posters.

## 🔗 Project Links

-   **Live App:** [Add your deployed app link
    here](https://cinematch-movie-recommender-9p7nl5suemxhq8rocvlzym.streamlit.app/)
-   **GitHub Repository:**[ [Add your repository link
    here](https://github.com/Prafful9999/cinematch-movie-recommender/blob/main/app.py)
]
## 📸 Screenshots

```{=html}
<!-- Add your screenshots below when ready. -->
```
![CineMatch Home Page](screenshots/home.png) ![Movie
Recommendations](screenshots/recommendations.png)

## 🛠️ Tech Stack

-   Python, Streamlit, Pandas
-   CountVectorizer and PorterStemmer
-   Cosine Similarity
-   TMDB API

## ⚙️ Run Locally

``` bash
git clone PASTE_GITHUB_REPOSITORY_URL_HERE
cd cinematch-movie-recommender
pip install -r requirements.txt
streamlit run app.py
```

## 🔑 TMDB API Key

Configure `TMDB_API_KEY` in `.streamlit/secrets.toml` for local use or
in Streamlit Community Cloud **Settings → Secrets**. Never commit your
API key or `secrets.toml` to GitHub.
