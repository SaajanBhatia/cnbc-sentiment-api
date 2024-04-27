import asyncio
import datetime
import logging
import os
from typing import List

from fastapi import FastAPI, WebSocket
from transformers import (AutoModelForSequenceClassification, AutoTokenizer,
                          pipeline)

from src import WebSocketManager, RssReader

app = FastAPI(
    title="Sentiment WS Producer from RSS Headlines",
    version='0.1.2'
)

socket_manager = WebSocketManager()
rss_reader = RssReader()

# Define the model name and the path for the locally saved model
model_name = "distilbert-base-uncased-finetuned-sst-2-english"
local_model_path = "./models/distilbert"


def text_producer() -> List[str]:
    # Loads an array of text from an RSS feed
    try:
        text_arr = rss_reader.get_rss_news()
        return text_arr
    except Exception as e:
        logging.error(f'Error fetching news headlines: {str(e)}')


# Function to load or download the model
def load_model():
    if os.path.exists(local_model_path):
        logging.info("Loading model from local directory.")
        model = AutoModelForSequenceClassification.from_pretrained(
            local_model_path)
        tokenizer = AutoTokenizer.from_pretrained(local_model_path)
    else:
        logging.info("Downloading and saving model for the first time.")
        os.makedirs(local_model_path, exist_ok=True)
        model = AutoModelForSequenceClassification.from_pretrained(model_name)
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model.save_pretrained(local_model_path)
        tokenizer.save_pretrained(local_model_path)
    return pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)


classifier = load_model()


async def sentiment_analyzer(websocket: WebSocket):
    while True:
        text_arr = text_producer()

        results = [classifier(text) for text in text_arr]
        score_total = 0

        for result in results:

            # Parse the result
            sentiment_score = result[0]['score'] if result[0]['label'] == 'POSITIVE' else 1 - \
                result[0]['score']
            score_total += sentiment_score

        sentiment_data = {
            "sentiment": score_total / len(text_arr),
            "time": datetime.datetime.now().isoformat()
        }

        # Send sentiment data to the client
        await websocket.send_json(sentiment_data)
        await asyncio.sleep(100)  # Wait for 100 seconds


@app.get("/")
async def get():
    return {'version': app.version, 'message': 'Welcome to the Sentiment Websocket API'}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await socket_manager.connect(websocket)
    try:
        while True:
            await sentiment_analyzer(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        socket_manager.disconnect(websocket)