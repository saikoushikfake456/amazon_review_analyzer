from flask import Flask, request, render_template_string
import pandas as pd
from textblob import TextBlob
from collections import Counter
import re
import os

app = Flask(__name__)

# ---------------- LOAD DATASET ---------------- #

data = pd.read_csv(os.path.join(os.path.dirname(__file__), "amazon_reviews.csv"))

if "reviewText" in data.columns:
    data["review"] = data["reviewText"]

data = data.dropna(subset=["review"])

# ---------------- FEATURE EXTRACTION ---------------- #

def extract_features(reviews):
    words = []

    for review in reviews:
        review = str(review).lower()
        review = re.sub(r'[^a-zA-Z ]', '', review)
        words.extend(review.split())

    stopwords = set([
        "the","is","and","a","to","of","it","this","that",
        "in","for","on","with","as","was","are","but","very",
        "good","bad","product","use","used","buy","bought"
    ])

    filtered = [w for w in words if w not in stopwords and len(w) > 3]

    common = Counter(filtered).most_common(4)

    return dict(common)

# ---------------- SENTIMENT ---------------- #

def get_sentiment(review):
    polarity = TextBlob(str(review)).sentiment.polarity
    if polarity > 0:
        return "Positive"
    elif polarity < 0:
        return "Negative"
    return "Neutral"

# ---------------- HTML ---------------- #

html_page = """<!DOCTYPE html>
<html>
<head>
<title>Amazon Review Analyzer</title>

<script>
const sentimentChart = new Chart(document.getElementById('sentimentChart'), {
    type: 'pie',
    data: {
        labels: ['Positive', 'Negative'],
        datasets: [{
            data: [{{ positive }}, {{ negative }}]
        }]
    }
});

const featureChart = new Chart(document.getElementById('featureChart'), {
    type: 'bar',
    data: {
        labels: {{ features.keys() | list | tojson }},
        datasets: [{
            label: 'Mentions',
            data: {{ features.values() | list | tojson }}
        }]
    }
});
</script>

<style>
body {
    background: linear-gradient(135deg,#141e30,#243b55);
    color:white;
    text-align:center;
    font-family: Arial;
}

input, button {
    padding:10px;
    border-radius:20px;
    border:none;
}

button { background:#ff9900; font-weight:bold; }

.card {
    background:#1f2a40;
    margin:30px auto;
    padding:20px;
    width:420px;
    border-radius:15px;
}

.feature-card {
    background:#2e3b55;
    padding:10px;
    border-radius:10px;
    margin:8px 0;
    display:flex;
    justify-content:space-between;
}
</style>
</head>

<body>

<h1>🛒 Amazon Review Analyzer</h1>

<form method="POST">
<input type="text" name="product" placeholder="Search product" required>
<button type="submit">Search</button>
</form>

{% if product %}
<div class="card">

<h2>{{ product }}</h2>

<a href="https://www.amazon.in/s?k={{ product }}" target="_blank">
<button>View on Amazon</button>
</a>

<h3>Sentiment Analysis</h3>
<canvas id="sentimentChart"></canvas>

<h3>Feature Analysis</h3>
<canvas id="featureChart"></canvas>

{% for key, value in features.items() %}
<div class="feature-card">
<span>{{ key }}</span>
<span>{{ value }}</span>
</div>
{% endfor %}

</div>

<script>
const sentimentChart = new Chart(document.getElementById('sentimentChart'), {
    type: 'pie',
    data: {
        labels: ['Positive', 'Negative'],
        datasets: [{
            data: [{{ positive }}, {{ negative }}]
        }]
    }
});

const featureChart = new Chart(document.getElementById('featureChart'), {
    type: 'bar',
    data: {
        labels: {{ features.keys() | list }},
        datasets: [{
            label: 'Mentions',
            data: {{ features.values() | list }}
        }]
    }
});
</script>

{% endif %}

</body>
</html>"""

# ---------------- ROUTE ---------------- #

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        product = request.form["product"]

        reviews = data.sample(min(200, len(data)))

        pos = neg = 0

        for review in reviews["review"]:
            s = get_sentiment(review)
            if s == "Positive":
                pos += 1
            elif s == "Negative":
                neg += 1

        total = len(reviews)
        positive = int((pos/total)*100) if total else 0
        negative = int((neg/total)*100) if total else 0

        features = extract_features(reviews["review"])

        return render_template_string(html_page,
            product=product,
            positive=positive,
            negative=negative,
            features=features
        )

    return render_template_string(html_page)

# ---------------- RUN ---------------- #

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
