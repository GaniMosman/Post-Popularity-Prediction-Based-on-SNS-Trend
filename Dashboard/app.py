from flask import Flask, render_template, request
import os
import pandas as pd
import emoji
import numpy as np
import re
import string
import enchant
import nltk
import csv
from nltk.corpus import stopwords
from operator import itemgetter
from textblob import TextBlob
import tweepy
import joblib as jb
import glob


#flask part
app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

#Setting punctuation and stop words
punct = string.punctuation
stop_words = set(stopwords.words('english') + ['us','all','hey','yeah','ya','yeap',"this"])
#Initializing lemmatizer and stemmer
lemma = nltk.WordNetLemmatizer()
stem = nltk.PorterStemmer()
d = enchant.Dict("en_US")

#Variables that contains the user credentials to access Twitter API
access_token = "1335210384928559105-BoIqcmTJLHeG2W9wytHhQjrRr2bBNQ"
access_token_secret = "fJwvaMxyA2ZzzNKIdkLOZQbhO3O85Cx8attYbb1gPXHnT"
consumer_key = "mkFdQ26iT2RfrDrtlqoAW4Uea"
consumer_secret = "MxQqz3CI16Xz5ZWHfwyXxzA6FCKkssfncRg4wkWj6T8XbJd9k9"

# authentication
auth = tweepy.AppAuthHandler(consumer_key, consumer_secret)
#auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth,wait_on_rate_limit=True,wait_on_rate_limit_notify = True)


# Function for cleaning text of tweets
def clean_text_topic_selection(text):
    # Removing URL
    text = re.sub(r"http\S+", "", text)
    # Removing emoji/stickers
    text = re.sub(emoji.get_emoji_regexp(), r"", text)
    # Removing punctuation and tokenizing
    text_token = "".join([x.lower() for x in text if x not in punct]).split()
    # Removing stop words
    text_removed_sw = [x for x in text_token if x not in stop_words]
    # Lemmatizing and stemming
    cleaned_text = [stem.stem(x) if x.endswith("ing") else lemma.lemmatize(x) for x in text_removed_sw]

    return cleaned_text


# Function for cleaning text of tweets
def clean_text(text):
    # Removing URL
    text = re.sub(r"http\S+", "", text)
    # Removing emoji/stickers
    text = re.sub(emoji.get_emoji_regexp(), r"", text)
    # Removing punctuation and tokenizing
    text_token = "".join([x.lower() for x in text if x not in punct]).split()
    # Removing non english word
    clean_text = [x for x in text_token if d.check(x) == True]
    # Lemmatizing and stemming
    cleaned_text = [stem.stem(x) if x.endswith("ing") else lemma.lemmatize(x) for x in clean_text]

    return cleaned_text


# Function for returning tweet type
def classify_tweet(tweet):
    sentence = str(tweet)
    analysis = TextBlob(sentence)
    polarity = analysis.sentiment.polarity
    if polarity > 0.1:
        return 'Positive tweet'

    elif polarity < 0:
        return 'Negative tweet'

    else:
        return 'Neutral tweet'



@app.route('/', methods=["POST", "GET"])
def show_profile():
    if request.method == "POST":

        tweet = request.form['tweet']
        username = request.form['username']
        clean_tweet = clean_text(tweet)
        tweet_type = classify_tweet(clean_tweet)
        print(tweet_type)

        try:
            user = api.get_user(screen_name=username)
            follower = user.followers_count
            friends = user.friends_count
            status = user.statuses_count
            listed = user.listed_count
            favorites = user.favourites_count
            Avg_favorites_per_user = favorites / status
            follower_listed_ratio = listed / follower
            follower_following_ratio = follower / friends
        except tweepy.error.TweepError as e:
            return "Inavlid username!"

        sentence = clean_text_topic_selection(tweet)

        all_match = []
        for path in glob.iglob("bag_of_words/*.csv"):
            count = 0
            data = pd.read_csv(path)
            file = path.split('\\')
            file = file[1]
            bow = data['word']
            bow = bow.to_numpy().tolist()
            for x in sentence:
                if x in bow:
                    count = count + 1
            match = {'file': file, 'count': count}
            all_match.append(match)

        all_match.sort(key=itemgetter('count'), reverse=True)
        file = all_match[0]['file']
        file = file.split('.')
        path = "saved_model\\" + file[0]




        #features
        follower = np.log1p(follower)
        listed = np.log1p(listed)
        Avg_favorites_per_user = np.log1p(Avg_favorites_per_user)
        follower_following_ratio = np.log1p(follower_following_ratio)
        follower_listed_ratio = np.log1p(follower_listed_ratio)

        if tweet_type == "Positive tweet":
            features = [follower, listed, Avg_favorites_per_user, follower_following_ratio, follower_listed_ratio,1,0]
        elif tweet_type == "Negative tweet":
            features = [follower, listed, Avg_favorites_per_user, follower_following_ratio, follower_listed_ratio,0,1]
        else:
            features = [follower, listed, Avg_favorites_per_user, follower_following_ratio, follower_listed_ratio,0,0]

        model = jb.load(path)
        result = model.predict([features])
        if result == 1:
            prediction = "Popular"
        else:
            prediction = "Not Popular"

        text = ('%20').join(tweet.split(' '))
        return render_template("profile.html", text = text, prediction = prediction, tweet_type = tweet_type)

    else:

        return render_template("form.html")


if __name__ == '__main__':
    app.run(debug=True)
