# app.py
from flask import Flask, render_template, request
import pickle
import numpy as np
import pandas as pd

app = Flask(__name__)

# Load model
with open('model.pkl', 'rb') as f:
    model, scaler, features = pickle.load(f)

# Load teams from CSV
df = pd.read_csv('elo_features.csv')
all_teams = sorted(set(df['home_team'].unique()) | set(df['away_team'].unique()))

@app.route('/', methods=['GET', 'POST'])
def home():
    prediction = None
    
    if request.method == 'POST':
        home = request.form['home_team']
        away = request.form['away_team']
        
        # Get average feature values for this matchup from dataset
        home_rows = df[df['home_team'] == home]
        away_rows = df[df['away_team'] == away]
        
        if len(home_rows) == 0 or len(away_rows) == 0:
            prediction = {"error": "No historical data for this matchup!"}
        else:
            # Use average of past matches
            elo_diff = home_rows['elo_diff_before'].mean()
            expected = home_rows['expected_home_win'].mean()
            goal_factor = home_rows['goal_margin_factor'].mean()
            rank_diff = home_rows['rank_diff'].mean()
            
            X = np.array([[elo_diff, expected, goal_factor, rank_diff]])
            X_scaled = scaler.transform(X)
            
            prob = model.predict_proba(X_scaled)[0]
            pred = model.predict(X_scaled)[0]
            
            winner = "Draw" if pred == 0 else home if pred == 1 else away
            
            prediction = {
                'home': home, 'away': away,
                'winner': winner,
                'home_win': round(prob[1] * 100, 1),
                'draw': round(prob[0] * 100, 1),
                'away_win': round(prob[2] * 100, 1)
            }
    
    return render_template('index.html', teams=all_teams, prediction=prediction)

if __name__ == '__main__':
    app.run(debug=True)
