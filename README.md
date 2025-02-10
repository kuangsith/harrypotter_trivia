# 🧙‍♂️ Harry Potter Trivia Game  

A Flask-based Harry Potter trivia game that generates quiz questions using **Google Gemini AI** and stores scores in **Google BigQuery**. Players answer **10 questions**, submit their name, and view **daily/weekly leaderboards**.  

🔗 **Try playing the game:**  
[https://harry-potter-trivia-195813819523.us-west1.run.app](https://harry-potter-trivia-195813819523.us-west1.run.app)  

## 🚀 Features  
- **Dynamic Quiz Generation** – Questions generated via **Google Gemini AI**  
- **Flexible Answer Matching** – Handles misspellings and synonyms using **LLM embeddings**  
- **Leaderboard System** – Stores scores in **Google BigQuery**  
- **Cloud Deployment** – Runs on **Google Cloud Run** using **Docker**  

## 🛠️ Installation  
```bash
# Clone the repository
git clone https://github.com/kuangsith/harrypotter_trivia.git
cd harrypotter_trivia

# Install dependencies
pip install -r requirements.txt

# Run the app locally
python app.py

# Open in browser
http://127.0.0.1:5000
