import pandas as pd
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

data = {
    "review": [
        "This product is amazing and works perfectly",
        "Worst product ever waste of money",
        "Excellent quality highly recommended",
        "Fake product do not buy",
        "Very good and useful item",
        "Totally bad and useless"
    ],
    "label": [0, 1, 0, 1, 0, 1]
}

df = pd.DataFrame(data)

vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(df["review"])
y = df["label"]

model = LogisticRegression()
model.fit(X, y)

pickle.dump(model, open("model.pkl", "wb"))
pickle.dump(vectorizer, open("vectorizer.pkl", "wb"))

print("Model Ready 🎉")