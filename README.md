# 🎬 Nebulous Cinema — AI-Powered Movie Recommender

**Nebulous Cinema** is a smart, TMDB-powered movie recommendation web app built with Flask, JavaScript, and TF-IDF-based NLP. It helps users discover, explore, and enjoy movies with intelligent search, random picks, and AI recommendations — all served through a fast, responsive frontend and a secure Python backend.

![Built with Flask](https://img.shields.io/badge/Built%20With-Flask-blue?logo=flask&logoColor=white)
![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

---

## Features

-  **Smart Search**: Find movies by title, actor, genre, director, or keywords
-  **Random Picks**: Infinite scroll browsing with surprise selections
-  **Watch Trailers**: Launch trailers via YouTube integration
-  **AI Recommendations**: Based on TF-IDF & NLP vector similarity
-  **Movie Details**: Cast, genres, ratings, overview & more
-  **Secure Backend**: All TMDB calls are server-side, your key stays hidden

---

## 🚀 Try It Now

Here's a quick look at **Nebulous Cinema** in action:

<p align="center">
  <img src="https://github.com/user-attachments/assets/41d76e86-ccfc-4e6a-b986-40c6250ee4c3" alt="Nebulous Cinema Screenshot" style="border-radius: 12px; max-width: 90%;"/>
</p>

<p align="center">
  <em>Lights. Camera. Launch your own Nebulous Cinema experience today!</em>
</p>

<p align="center">
  <a href="https://render.com/deploy" target="_blank">
    <img src="https://render.com/images/deploy-to-render-button.svg" alt="Deploy to Render" height="33" style="margin-right: 20px;"/>
  </a>
  <a href="https://nebulous-cinema.onrender.com/" target="_blank">
    <img src="https://img.shields.io/badge/Launch-Nebulous%20Cinema-brightgreen?style=for-the-badge&logo=rocket" alt="Visit Nebulous Cinema" height="33">
  </a>
</p>

---

##  Render Secret File Setup

After deployment, go to your **Render Dashboard**, then:

1. Navigate to your service → **Environment > Secret Files**
2. Add a secret file:
   - **Name**: `tmdb_api_key`
   - **Content**: your TMDB API key
   - **Mount Path**: `/etc/secrets/tmdb_api_key`

---

##  Tech Stack

| Layer      | Tech Used                      |
|------------|--------------------------------|
| Backend    | Flask, NLTK, Scikit-learn      |
| Frontend   | HTML5, CSS3, JavaScript (vanilla) |
| Data       | TMDB API                       |
| NLP Engine | TF-IDF + Cosine Similarity     |
| Hosting    | [Render](https://render.com)   |

---

##  Project Structure

```
nebulous-cinema/
├── app.py
├── optimized_movie_recommender.py
├── requirements.txt
├── render.yaml
├── templates/
│   └── index.html
└── static/
    ├── css/styles.css
    └── js/script.js
```

---

##  Local Development

```bash
# Clone the repo
git clone https://github.com/your-username/nebulous-cinema.git
cd nebulous-cinema

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# (Optional) Export your API key for local testing
export TMDB_API_KEY=your_key_here

# Run the app
python app.py
```

---

##  Screenshots

 ![Screenshot 2025-04-19 203225](https://github.com/user-attachments/assets/f6263411-0dde-4d2b-90f5-1108091e1aec)

 ![Screenshot 2025-04-19 203148](https://github.com/user-attachments/assets/d3d93aeb-637d-4c42-b9ad-bead84cc82fb)

---

##  License

Licensed under the **GNU General Public License v3.0**.

> You are free to use, modify, and distribute the project as long as derived works are also open-source under GPL-3.

 See the full [LICENSE](LICENSE) file for details.

---

##  Contributing

Pull requests and ideas are welcome!  
Have an idea for a feature or improvement? Open an issue or fork the repo.

---

##  Credits

- [TMDB](https://www.themoviedb.org/) — Movie data API  
- [NLTK](https://www.nltk.org/) — Natural Language Toolkit  
- [Render](https://render.com/) — Fast, free Python hosting

---

##  Like the project?

Star ⭐ the repo, share it, and help others discover **Nebulous Cinema** — the AI-powered movie matcher!
