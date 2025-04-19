# 🎬 Nebulous Cinema — AI-Powered Movie Recommender

**Nebulous Cinema** is a smart, TMDB-powered movie recommendation web app built with Flask, JavaScript, and TF-IDF-based NLP. It helps users discover, explore, and enjoy movies with intelligent search, random picks, and recommendations — all styled with a responsive frontend and a secure, private backend.

![Built with Flask](https://img.shields.io/badge/Built%20With-Flask-blue?logo=flask&logoColor=white)
![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

---

## 🌟 Features

- 🔍 **Smart Search**: Find movies by title, actor, genre, director, or keywords
- 🎲 **Random Suggestions**: Infinite scroll browsing with surprise picks
- 🎬 **Watch Trailers**: Launch trailers directly from YouTube
- 🧠 **AI Recommendations**: Based on NLP (TF-IDF) similarity
- 🧩 **Movie Metadata**: View cast, genre, language, rating, and overview
- 🔐 **Secure Backend**: API key hidden server-side via Render Secret File

---

## 🛠️ Tech Stack

- **Backend**: Flask, NLTK, Scikit-learn, TMDB API
- **Frontend**: HTML5, CSS3, JavaScript (vanilla)
- **Deployment**: Render.com
- **Search**: TF-IDF Vectorizer + Cosine Similarity

---

## 🚀 Live Demo & Instant Deploy

You can deploy this app with **your own TMDB API key** in under a minute using:

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

### 🔐 After Deploying:
1. Go to your **Render Dashboard**
2. Navigate to your service → **Environment > Secret Files**
3. Add:
   - **Name**: `tmdb_api_key`
   - **Content**: your TMDB API key
   - **Mount Path**: `/etc/secrets/tmdb_api_key`

---

## 📦 Project Structure

```
nebulous-cinema/
├── app.py
├── optimized_movie_recommender.py
├── requirements.txt
├── render.yaml                  # Optional for Render auto-deploy
├── templates/
│   └── index.html
└── static/
    ├── css/styles.css
    └── js/script.js
```

---

## 💻 Local Development

```bash
# Clone the repo
git clone https://github.com/your-username/nebulous-cinema.git
cd nebulous-cinema

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# (Optional) Create a file at /etc/secrets/tmdb_api_key or export the variable
export TMDB_API_KEY=your_key_here

# Run the app
python app.py
```

---

## 📸 Screenshots (optional)

_Add your screenshots here to show off the app UI._

---

## 📄 License

This project is licensed under the **GNU General Public License v3.0**.

You are free to:

- Use, modify, and distribute this software
- Keep it open-source and give proper credit  
- Maintain derivative works under the same license (GPL-3 compatible)

📄 See [`LICENSE`](LICENSE) for full terms.

---

## 🤝 Contributing

Pull requests, issues, and suggestions are always welcome!

> If you'd like to add new features (like genre filters or login support), feel free to fork and build on this.

---

## 🙌 Credits

- [TMDB API](https://www.themoviedb.org/) for movie data
- [NLTK](https://www.nltk.org/) for natural language processing
- [Render.com](https://render.com/) for simple app hosting

---

### 🧠 Like the project?

Star ⭐ the repo or share it with friends. Let Nebulous Cinema help everyone find their next favorite movie!

---

## ✅ Next Steps

1. Create a file named `README.md` in your repo
2. Paste the content above
3. Push to GitHub:

```bash
git add README.md
git commit -m "Add polished README with GPL-3 and Deploy button"
git push
```

---

### 🧠 Like the project?

Star ⭐ the repo or share it with friends.  
Let **Nebulous Cinema** help everyone find their next favorite movie!

