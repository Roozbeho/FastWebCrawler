# Asynchronous Web Crawler

This **asynchronous web crawler** is built with Python using **asyncio** and **aiohttp** to enable high-performance, concurrent web scraping. It efficiently fetches web pages, extracts links for further crawling, and stores the scraped data (URLs and text content) in a CSV file. Designed for scalability, it provides configurable limits on concurrency, crawl depth, and error handling to ensure smooth and efficient operation it’s perfect for data collection, research, web exploration or building datasets to create your own custom GPT model.

## Requirements

- Python 3.9+
- aiohttp
- aiofiles
- beautifulsoup4
- tldextract

## Installation


1. Clone the repository:
```bash
 git clone https://github.com/Roozbeho/FastWebCrawler.git

 cd web-crawler
```

2. Install dependencies:
```bash
 pip install -r requirements.txt
```


## Usage

```bash
 python main.py https://example.com --crawl-count 50
```
### Command Line Options
| Option                  | Description               | Default              |
|-------------------------|---------------------------|----------------------|
| `urls`                  | Starting URLs             | Required             |
| `-f, --file`            | File containing seed URLs | None                 |
| `-d, --domain`          | Target domain filter      | None                 |
| `-sd, --subdomain`      | Target subdomain filter   | None                 |
| `-c, --crawl-count`     | Max URLs to crawl         | 20                   |
| `-r, --retries`         | Request retry attempts    | 5                    |
| `-mc, --max-connection` | Concurrent connections    | 10                   |
| `-t, --timeout`         | Request timeout (seconds) | 1                    |
| `--output-file`         | Output CSV path           | data/scrape_data.csv |
| `--log-level`           | Log verbosity             | INFO                 |


## How It Works

1. **Initialization**:
   - The crawler starts with a list of URLs, optional domain/subdomain filters, and settings for crawl count, concurrency, retries, and timeouts.

2. **URL Filtering**:
   - URLs are validated and filtered to exclude unwanted types (e.g., `.jpg`, `.mp3`) and paths (e.g., `/login/`, `/admin/`).

3. **Asynchronous Crawling**:
   - Uses `asyncio` and a semaphore to limit concurrent requests based on the `max_connection` setting.
   - Fetches HTML content, extracts links, and processes text concurrently.

4. **Text Extraction**:
   - Parses HTML with `BeautifulSoup` to extract readable text, stripping out scripts, styles, and metadata.

5. **Output**:
   - Writes each URL and its extracted text to a CSV file, ensuring thread-safe file access with a lock.

6. **Error Handling**:
   - Retries failed requests up to the specified limit and logs errors (e.g., timeouts, network issues).

## Contributing
 
Contributions are welcome! If you'd like to contribute to this project, please fork the repository and submit a pull request. 