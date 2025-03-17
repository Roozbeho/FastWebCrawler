import os
import asyncio
import logging
import argparse
import aiofiles
from crawler import Crawler

async def read_urls_from_file(file_path):
    try:
        async with aiofiles.open(file_path, 'r') as file:
            lines = await file.readlines()
            return [line.strip() for line in lines]
    except FileNotFoundError as e:
        logging.error(f"File not found: {file_path}")
        return []
    except Exception as e:
        logging.error(f"Error reading URLs file {file_path}: {e}")
        return []


async def main():
    parser = argparse.ArgumentParser(description="Async Web Crawler")
    parser.add_argument("urls", nargs="*", type=str, help="The Websites URLs to scrape")
    parser.add_argument("-f", "--file", type=str, help="file path to read URL from")
    parser.add_argument("-d", "--domain", type=str, default="", help="URLs domain to search for")
    parser.add_argument("-sd", "--subdomain", type=str, default="", help="URLs subdomain to search for")
    parser.add_argument("-c", "--crawl-count", type=int, default=20, help="Maximum Number of URLs to scrape")
    parser.add_argument("-r", "--retries", type=int, default=5, help="Number of retries when request fails")
    parser.add_argument("-mc", "--max-connection", type=int, default=10,
                        help="Maximum number of concurrent requests")
    parser.add_argument("-t", "--timeout", type=float, default=1, 
                        help="Timeout for each request in seconds",)
    parser.add_argument("--output-file", type=str, default="../data/scrape_data.csv",
                        help="File path to store scraped data")
    parser.add_argument("--log-level", type=str, default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        help="Logging level")
    
    args = parser.parse_args()

    
    logging.basicConfig(
        format="{asctime} - {levelname} - {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M",
        level=getattr(logging, args.log_level.upper(), logging.INFO),
    )

    # Read urls from file if filepath provided
    if args.file:
        file_urls = await read_urls_from_file(args.file)
        args.urls.extend(file_urls)

    #  Check output path
    output_dir = os.path.dirname(args.output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    crawler = Crawler(
        urls=args.urls,
        domain=args.domain,
        subdomain=args.subdomain,
        crawl_count=args.crawl_count,
        max_connection=args.max_connection,
        retries=args.retries,
        timeout=args.timeout,
        output_file=args.output_file,
    )

    try:
        logging.info(f"Starting crawl of {len(args.urls)} URLs with crawl limit {args.crawl_count}")
        await crawler.run()
        logging.info("Crawling completed successfully")
    except KeyboardInterrupt:
        logging.info("Crawling interrupted by user")
    except Exception as e:
        logging.error(f"Crawling failed: {str(e)}")
        # raise


if __name__ == '__main__':
    asyncio.run(main())
