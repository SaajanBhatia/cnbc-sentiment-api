import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

import feedparser

# Example RSS Feeds from CNBC
RSS_FEEDS = [
    {
        "name": "Technology",
        "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=19854910",
    },
    {
        "name": "World News",
        "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100727362",
    },
    {
        "name": "Top News",
        "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114",
    },
    {
        "name": "Economy",
        "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=20910258",
    },
    {
        "name": "Finance",
        "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664",
    }
]


class RssReader:
    def __init__(self):
        self.feeds = RSS_FEEDS
        self.day_time_lag = 3

    def fetch_rss(self, rss_url: str) -> Dict[str, Any]:
        try:
            return feedparser.parse(rss_url)
        except Exception as e:
            logging.error(f"Error parsing URL '{rss_url}': {str(e)}")
            return {}

    def validate_published_data(self, date: str, lag: int) -> bool:
        try:
            published_date = datetime.strptime(
                date, "%a, %d %b %Y %H:%M:%S GMT")
            threshold_date = datetime.today() - timedelta(days=lag)
            return published_date >= threshold_date

        except ValueError as e:
            raise ValueError(f"Invalid date format or value: {e}")

    def get_rss_news(self) -> List[str]:
        text_entries = []
        for feed in self.feeds:
            res = self.fetch_rss(rss_url=feed['url'])
            entries = (res['entries'])

            for entry in entries:
                valid_recency = self.validate_published_data(
                    date=entry['published'],
                    lag=self.day_time_lag
                )

                if valid_recency:
                    if "title" in entry:
                        text_entries.append(entry['title'])

        if not text_entries:
            logging.error('No News Headlines')

        return text_entries
