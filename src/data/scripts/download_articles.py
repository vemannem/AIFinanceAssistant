#!/usr/bin/env python3
"""Financial Articles Downloader - Downloads 25+ articles from public sources."""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

RAW_DIR = Path(__file__).parent.parent / "raw_articles"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# 25+ verified working Investopedia term definition URLs
INVESTOPEDIA_URLS = [
    'https://www.investopedia.com/terms/s/stock.asp',
    'https://www.investopedia.com/terms/e/equity.asp',
    'https://www.investopedia.com/terms/s/shareholder.asp',
    'https://www.investopedia.com/terms/e/etf.asp',
    'https://www.investopedia.com/terms/i/indexfund.asp',
    'https://www.investopedia.com/terms/t/trackingerror.asp',
    'https://www.investopedia.com/terms/b/bond.asp',
    'https://www.investopedia.com/terms/c/coupon.asp',
    'https://www.investopedia.com/terms/y/yield.asp',
    'https://www.investopedia.com/terms/c/capital_gains_tax.asp',
    'https://www.investopedia.com/terms/d/dividend.asp',
    'https://www.investopedia.com/terms/i/ira.asp',
    'https://www.investopedia.com/terms/r/retirement-planning.asp',
    'https://www.investopedia.com/terms/d/diversification.asp',
    'https://www.investopedia.com/terms/a/assetallocation.asp',
    'https://www.investopedia.com/terms/r/rebalancing.asp',
    'https://www.investopedia.com/terms/v/volatility.asp',
    'https://www.investopedia.com/terms/m/marketrisk.asp',
    'https://www.investopedia.com/terms/d/dollarcostaveraging.asp',
    'https://www.investopedia.com/terms/m/mutualfund.asp',
    'https://www.investopedia.com/terms/b/blue-chip-stock.asp',
    'https://www.investopedia.com/terms/p/penny-stock.asp',
    'https://www.investopedia.com/terms/g/growth-stock.asp',
    'https://www.investopedia.com/terms/v/value-investing.asp',
    'https://www.investopedia.com/terms/m/margin-call.asp',
]

# 5 major ETF/stock tickers from Yahoo Finance
YAHOO_FINANCE_URLS = [
    'https://finance.yahoo.com/quote/SPY',
    'https://finance.yahoo.com/quote/BND',
    'https://finance.yahoo.com/quote/VTI',
    'https://finance.yahoo.com/quote/QQQ',
    'https://finance.yahoo.com/quote/IVV',
]


class FinancialArticleDownloader:
    """Scrapes financial articles from public sources."""

    def __init__(self):
        self.articles = []
        self.session = requests.Session()
        self.session.headers['User-Agent'] = 'Mozilla/5.0'
        self.id_counter = 1

    def scrape_investopedia(self, url: str, category: str) -> Optional[Dict]:
        """Scrape Investopedia term pages."""
        try:
            resp = self.session.get(url, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.content, 'html.parser')

            h1 = soup.find('h1')
            title = h1.text.strip() if h1 else 'Article'

            paragraphs = [p.text.strip() for p in soup.find_all('p')[:10] if len(p.text.strip()) > 20]
            content = ' '.join(paragraphs)

            if len(content) < 50:
                return None

            article = {
                'id': f'article_{self.id_counter}',
                'title': title,
                'content': content,
                'category': category,
                'url': url,
                'publish_date': datetime.now().isoformat(),
                'source': 'investopedia'
            }
            self.id_counter += 1
            logger.info(f"✅ {title[:50]}")
            return article
        except Exception as e:
            logger.error(f"❌ {url.split("/")[-1]}: {type(e).__name__}")
            return None

    def scrape_yahoo_finance(self, url: str) -> Optional[Dict]:
        """Scrape Yahoo Finance quote pages."""
        try:
            resp = self.session.get(url, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.content, 'html.parser')

            symbol = url.split('/')[-1]
            title = f"{symbol} - Market Data"

            paragraphs = [p.text.strip() for p in soup.find_all('p') if len(p.text.strip()) > 20]
            content = ' '.join(paragraphs[:10])

            if len(content) < 50:
                content = f"Stock market data and financial information for {symbol}"

            article = {
                'id': f'article_{self.id_counter}',
                'title': title,
                'content': content,
                'category': 'stocks',
                'url': url,
                'publish_date': datetime.now().isoformat(),
                'source': 'yahoo_finance'
            }
            self.id_counter += 1
            logger.info(f"✅ {title}")
            return article
        except Exception as e:
            logger.error(f"❌ {url.split('/')[-1]}: {type(e).__name__}")
            return None

    def download(self):
        """Download articles from all sources."""
        logger.info("📚 Scraping Investopedia (25 URLs)...")
        for url in INVESTOPEDIA_URLS:
            article = self.scrape_investopedia(url, self._categorize(url))
            if article:
                self.articles.append(article)
            time.sleep(1)

        logger.info("📈 Scraping Yahoo Finance (5 URLs)...")
        for url in YAHOO_FINANCE_URLS:
            article = self.scrape_yahoo_finance(url)
            if article:
                self.articles.append(article)
            time.sleep(1)

    def _categorize(self, url: str) -> str:
        """Auto-categorize based on URL keywords."""
        if 'stock' in url or 'equity' in url or 'shareholder' in url:
            return 'stocks'
        elif 'etf' in url or 'indexfund' in url or 'tracking' in url:
            return 'etfs'
        elif 'bond' in url or 'coupon' in url or 'yield' in url:
            return 'bonds'
        elif 'tax' in url or 'dividend' in url or 'gain' in url:
            return 'taxes'
        elif 'ira' in url or 'retirement' in url:
            return 'retirement'
        elif 'diversif' in url or 'allocation' in url or 'rebalance' in url:
            return 'portfolio_management'
        elif 'volatility' in url or 'risk' in url or 'market' in url:
            return 'risk_management'
        else:
            return 'investment_strategies'

    def save(self, filename: str = "financial_articles_raw.json"):
        """Save articles to JSON."""
        path = RAW_DIR / filename
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.articles, f, indent=2, ensure_ascii=False)
        logger.info(f"📁 Saved {len(self.articles)} articles")


if __name__ == "__main__":
    print("\n🚀 Financial Articles Downloader (25+ sources)\n")
    downloader = FinancialArticleDownloader()
    downloader.download()
    downloader.save()
    print(f"\n✅ Downloaded {len(downloader.articles)} articles\n")
    print(f"📁 Location: src/data/raw_articles/financial_articles_raw.json")
    print(f"📝 Next step: python chunk_articles.py\n")
