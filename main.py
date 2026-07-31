import asyncio, requests, aiohttp, logging
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from logging.handlers import RotatingFileHandler
from pathlib import Path
from bs4 import BeautifulSoup
from collections import Counter


main_path = Path(__file__).parent / "LOG"
if not main_path.exists():
    try:
        main_path.mkdir()
        print(f"All Logs are stored in: {main_path}")
    except (PermissionError, OSError) as e:
        print(f"Something went wrong while creating LOG Directory: {e}")
        main_path = Path(__file__).parent
        print(f"logs will be stored in {main_path}")

main_path_log = main_path / f"{Path(__file__).stem}.log"
log_handle = RotatingFileHandler(
    main_path_log,
    maxBytes=5*1024*1024,
    encoding="utf-8",
    backupCount=3
)

log_handle.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
logging.basicConfig(level=logging.DEBUG,
                    handlers=[log_handle])

async def fetch_url_async(session, url, max_retry, semaphore):
    async with semaphore:
        logging.debug(f"Fetching url: {url}")

        for i in range(max_retry):
            try:
                async with session.get(url) as response:
                    if not response.status == 200:
                        if i < (max_retry - 1):
                            await asyncio.sleep(1)
                        else:
                            logging.error(
                                f"Aysncio Scraping Failed on [{url}] | Error: Invalid Status Code:{response.status}\n")
                            return {"url": url, "success": False, "content": f"Invalid Status Code:{response.status}"}

                    else:
                        if "text" in response.headers.get("Content-Type"):
                            web_content = await response.text()

                            logging.info(f"Aysncio Scraping Successful on [{url}] | Content-Type: html/text ")
                            return {"url": url,
                                    "success": True,
                                    "content": web_content,
                                    "type": response.headers["Content-Type"]
                                    }

                        elif "json" in response.headers.get("Content-Type"):
                            web_content = await response.json()

                            logging.info(f"Aysncio Scraping Successful on [{url}] | Content-Type: Application/json ")
                            return {"url": url,
                                    "success": True,
                                    "content": web_content,
                                    "type": response.headers["Content-Type"]
                                    }
                        logging.info(f"Returning Content-type\n")

            except aiohttp.ClientConnectorError as cce:
                if i < (max_retry - 1):
                    await asyncio.sleep(1)
                else:
                    logging.error(f"Aysncio Scraping Failed on [{url}] | Error: {cce}\n")
                    return {"url": url, "success": False, "content": cce}

            except aiohttp.ClientHttpProxyError as chpe:
                if i < (max_retry - 1):
                    await asyncio.sleep(1)
                else:
                    logging.error(f"Aysncio Scraping Failed on [{url}] | Error: {chpe}\n")
                    return {"url": url, "success": False, "content": chpe}

            except aiohttp.ServerDisconnectedError as sde:
                if i < (max_retry - 1):
                    await asyncio.sleep(1)
                else:
                    logging.error(f"Aysncio Scraping Failed on [{url}] | Error: {sde}\n")
                    return {"url": url, "success": False, "content": sde}

            except aiohttp.ClientPayloadError as cpe:
                if i < (max_retry - 1):
                    await asyncio.sleep(1)
                else:
                    logging.error(f"Aysncio Scraping Failed on [{url}] | Error: {cpe}\n")
                    return {"url": url, "success": False, "content": cpe}

            except asyncio.TimeoutError as te:
                if i < (max_retry - 1):
                    await asyncio.sleep(1)
                else:
                    logging.error(f"Aysncio Scraping Failed on [{url}] | Error: {te}\n")
                    return {"url": url, "success": False, "content": te}

            except Exception as e:
                if i < max_retry - 1:
                    await asyncio.sleep(1)
                else:
                    logging.error(f"Aysncio Scraping Failed on [{url}] | Error: {e}\n")
                    return {"url": url, "success": False, "content": e}


async def fetch_multiple_urls_async(urls, max_retry=None, max_workers=None):
    logging.debug("Fetching Url Request | Method: Asyncio")

    max_retry = max_retry if max_retry else 4
    max_workers = max_workers if max_workers else 4
    time_out = aiohttp.ClientTimeout(sock_connect=5, sock_read=5)
    semaphore = asyncio.Semaphore(max_workers)

    logging.info(
        f"Max Retries for Scrape: {max_retry}, Max Workers for AsyncioThreads: {max_workers}, Urls: {len(urls)}")
    logging.debug(f"Asyncio Threading Process Started")

    start = time.time()
    async with aiohttp.ClientSession(timeout=time_out) as session:
        async with asyncio.TaskGroup() as tg:
            tasks = [tg.create_task(fetch_url_async(session, url, max_retry, semaphore)) for url in urls]
    re_list = [task.result() for task in tasks]
    finished = round(time.time() - start, 5)
    cpu_time = {"cpu_time_async": finished}

    logging.info(f"Aysncio Threading Process Completed | CPU Time: {finished} Secs")
    re_list.append(cpu_time)

    logging.info(f"Returning Scraped lIst: {len(re_list)}\n")
    return re_list


def fetch_url_threaded(url, max_retry):
    logging.debug(f"Fetching url: {url}")

    for i in range(max_retry):
        try:
            response = requests.get(url, timeout=5)
            if not response.status_code == 200:
                if i < max_retry - 1:
                    time.sleep(1)
                else:
                    logging.error(
                        f"ThreadPool Scraping Failed on [{url}] | Error: Invalid Status Code:{response.status_code}\n")
                    return {"url": url, "success": False, "content": f"Invalid Status Code:{response.status_code}"}
            else:
                if "text" in response.headers.get("Content-Type"):

                    logging.info(f"ThreadPool Scraping Successful on [{url}] | Content-Type: html/text ")
                    return {"url": url,
                            "success": True,
                            "content": response.text,
                            "type": response.headers["Content-Type"]
                            }

                elif "json" in response.headers.get("Content-Type"):

                    logging.info(f"ThreadPool Scraping Successful on [{url}] | Content-Type: Application/Json")
                    return {"url": url,
                            "success": True,
                            "content": response.json(),
                            "type": response.headers["Content-Type"]
                            }
                logging.info(f"Returning Content-type\n")

        except ConnectionError as ce:
            if i < max_retry - 1:
                time.sleep(1)
            else:
                logging.error(f"ThreadPool Scraping Failed on [{url}] | Error: {ce}\n")
                return {"url": url, "success": False, "content": ce}

        except TimeoutError as te:
            if i < max_retry - 1:
                time.sleep(1)
            else:
                logging.error(f"ThreadPool Scraping Failed on [{url}] | Error: {te}\n")
                return {"url": url, "success": False, "content": te}

        except requests.RequestException as rx:
            if i < max_retry - 1:
                time.sleep(1)
            else:
                logging.error(f"ThreadPool Scraping Failed on [{url}] | Error: {rx}\n")
                return {"url": url, "success": False, "content": rx}

        except Exception as e:
            if i < max_retry - 1:
                time.sleep(1)
            else:
                logging.error(f"ThreadPool Scraping Failed on [{url}] | Error: {e}\n")
                return {"url": url, "success": False, "content": e}

def fetch_multiple_threaded(urls, max_retry=None, max_workers=None):
    logging.debug(f"Starting Url Scraping | Method: ThreadPool\n")
    logging.debug("Fetching Url Request | Method: ThreadPool")

    max_workers = max_workers if max_workers else 4
    max_retry = max_retry if max_retry else 4

    logging.info(
        f"Max Retries for Scrape: {max_retry}, Max Workers for ThreadPool Threads: {max_workers}, Urls: {len(urls)}")
    logging.debug(f"ThreadPool Threading Process Started")

    start = time.time()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(fetch_url_threaded, url, max_retry) for url in urls]
        result = [future.result() for future in futures]
    finished = round(time.time() - start, 5)
    cpu_time = {"cpu_time_threaded": finished}

    logging.info(f"ThreadPool Threading Process Completed | CPU Time: {finished} Secs")
    result.append(cpu_time)

    logging.info(f"Returning Scraped lIst: {len(result)}\n")
    return result

def sequential_fetch(urls, max_retry=None):
    logging.debug(f"Starting Url Scraping | Method: Sequential Fetch\n")
    logging.debug("Fetching Url Request | Method: Sequential Fetch")

    max_rty = max_retry if max_retry else 4
    result_list = []

    logging.info(
        f"Max Retries for Scrape: {max_retry}, Urls: {len(urls)}")
    logging.debug(f"Sequential Fetch Threading Process Started")

    start = time.time()
    for url in urls:
        res = fetch_url_threaded(url, max_rty)
        result_list.append(res)
    finished = round(time.time() - start, 5)
    cpu_time = {"seq_time_threaded": finished}

    logging.info(f"Sequential Fetch Threading Process Completed | CPU Time: {finished} Secs")
    result_list.append(cpu_time)

    logging.info(f"Returning Scraped lIst: {len(result_list)}\n")
    return result_list




def clean_words(content):
    logging.debug("Cleaning Words")

    page = BeautifulSoup(content, "html.parser")
    logging.info("Page Parsed with Beautiful Soup 4")

    page_text = page.text.split()
    contraband = """ !.,“”@#$%^&*(){}[];|/\\-_=·+<>:❤'\""""
    contraband_alt = """ !,“”@#$%^&*(){}[];|/\\_=+<>:❤'\"""" #Does not include ['.', '-']
    cleaned_page_stg1 = [word.strip(contraband) for word in page_text ]
    cleaned_page_stg2 = []

    for word in cleaned_page_stg1:
        cleaned_word = "".join(w for w in word if not w in contraband_alt)
        if cleaned_word:                        #for words like (@@@@) or (!!!!)
            if not cleaned_word in [".", "-"]:  #for words like (....) or (----)
                cleaned_page_stg2.append(cleaned_word)

    logging.info("Words in Page cleaned | Returning Content")
    return page, cleaned_page_stg2

def analyze_words(content):
    logging.debug("Analyzing Words in Page")

    _, cleaned_page_word_list = clean_words(content)
    logging.debug("Analyzing cleaned Page")

    cleaned_characters = "".join(word for word in cleaned_page_word_list)
    word_frequency = Counter(cleaned_page_word_list)
    total_count = len(cleaned_page_word_list)
    longest = max(cleaned_page_word_list, key=len)
    longest_word = {longest: len(longest)}

    average_word_length = round(len(cleaned_characters) / len(cleaned_page_word_list), 4)
    most_common_word = {word_frequency.most_common(1)[0][0] : word_frequency.most_common(1)[0][1]}
    character_distribution = Counter(cleaned_characters)

    analyzed_word_dict = {"total_word_count": total_count,
                          "word_list": cleaned_page_word_list,
                          "word_frequency": word_frequency,
                          "character_distributions": character_distribution,
                          "longest_word": longest_word,
                          "avg_word_length": average_word_length,
                          "most_common_word": most_common_word,
                          }

    logging.info("Analyzing Process Completed")
    return analyzed_word_dict

def analyze_html(content):
    logging.debug(f"Analyzing HTML Contents in Page")

    page, cleaned_page_word_list = clean_words(content)
    find_tags = page.find_all(True)
    find_links = page.find_all("a")
    links = set()

    for a in find_links:
        link = a.get("href")
        if link:
            if not link in "/#":
                links.add(link)
    tags = [tag.name for tag in find_tags]
    tags_count = Counter(tags)

    word_frequency = Counter(cleaned_page_word_list)
    html_analyzed = {"all_page_links": links,
                     "html_tags_count": tags_count,
                     "word_frequency_dictionary": word_frequency
                     }

    logging.info("Analyzing HTML Completed")
    return html_analyzed

def process_task(dicts):
    logging.debug(f"Processing Scraped Content-type")

    if "text" in dicts["type"]:
        url = dicts["url"]
        content = dicts["content"]

        logging.info(f"Content from Url: [{url}] is html/text ")
        word_analysis = analyze_words(content)
        html_analysis = analyze_html(content)

        logging.info(f"Scraping Process for [{url}] Completed\n")
        return {"url": url, "words": word_analysis, "html": html_analysis}

    else:
        url = dicts["url"]
        c_type = dicts["type"]

        logging.warning(f"Cannot parse with BeautifulSoup | Content-Type not html/text ")
        return {"url": url, "error": f"Cannot parse with BeautifulSoup | Content-Type: {c_type}"}


def run_async(urls, max_rty=None, max_wrks=None):
    logging.debug(f"Starting Url Scraping | Method: Asyncio\n")

    data = asyncio.run(fetch_multiple_urls_async(urls, max_rty, max_wrks))
    return data

def split_urls(urls):
    logging.debug(f"Splitting urls into parts for different thread methods")

    dividen = len(urls) // 3
    mid_range = len(urls) - dividen
    start_range = mid_range - dividen
    end_range = len(urls)

    url_set1 = set()
    url_set2 = set()
    url_set3 = set()

    for i in range(0, start_range):
        url_set1.add(urls[i])

    for j in range(start_range, mid_range):
        url_set2.add(urls[j])

    for k in range(mid_range, len(urls)):
        url_set3.add(urls[k])

    logging.info("Url Splitting Completed")
    return url_set1, url_set2, url_set3


def process_multiple_cpu_bound(urls, max_rty=None, max_wrks=None, max_wrks_pool=None):
    main_workers = max_wrks_pool if max_wrks_pool else 4

    if not len(urls) % 3 == 0:
        logging.info(
            f"Url list is not divisible by 3 | Current Url List: {len(urls)} | Time comparison might be Inaccurate")
        print(f"For the most Accurate time Comparison with Sequential_task, ThreadPool and Asyncio, "
              f"let the Url List be divisible by 3 | "
              f"Current Url List Length: {len(urls)}")
        print()

    urls_1, urls_2, urls_3 = split_urls(urls)
    logging.info(f"Url splits: first_set={len(urls_1)}, second_set={len(urls_2)}, third_set={len(urls_3)}\n")

    collected_data = []
    collected_time = {}
    collected_errors = []
    pool_results = []

    start = time.time()
    logging.debug(
        f"Starting ProcessPoolExecutor for Threading | Urls: {len(urls)}, Maximum Worker for ProcessPool: {main_workers}")

    with ProcessPoolExecutor(max_workers=main_workers) as proces_exe:
        process_futures_threads = []
        task_1 = proces_exe.submit(run_async, urls_1, max_rty, max_wrks)
        task_2 = proces_exe.submit(fetch_multiple_threaded, urls_2, max_rty, max_wrks)
        task_3 = proces_exe.submit(sequential_fetch, urls_3, max_rty)
        process_futures_threads.append(task_1)
        process_futures_threads.append(task_2)
        process_futures_threads.append(task_3)

        for future in as_completed(process_futures_threads):
            data = future.result()
            last_index = len(data) - 1
            collected_time.update({k: v for k, v in data[last_index].items()})
            for dicts in data:
                if "success" in dicts:
                    if dicts["success"]:
                        collected_data.append(dicts)
                    else:
                        collected_errors.append(dicts)
        finished = round(time.time() - start, 5)

        logging.debug(
            f"ProcessPoolExecutor for Threading Completed | CPU Time: {finished} secs\n")
        start_2 = time.time()

        logging.debug(
            f"Starting ProcessPoolExecutor for Process | Maximum Worker for ProcessPool: {main_workers}")
        process_futures = [proces_exe.submit(process_task, dts) for dts in collected_data]

        for future in as_completed(process_futures):
            res = future.result()
            pool_results.append(res)

    fin = round(time.time() - start_2, 5)
    logging.debug(
        f"ProcessPoolExecutor for Process Completed | CPU Time: {fin} secs\n")

    collected_time.update({"all_cpu_time_process": finished})
    collected_time.update({"cpu_time_process": fin})
    return collected_time, collected_errors, pool_results


if __name__ == "__main__":
    print(f"\nAll Logs are stored in: {main_path}\n")
    url_list = ["https://books.toscrape.com/", "http://quotes.toscrape.com/",
             "https://sandbox.oxylabs.io/", "https://www.scrapethissite.com/pages/simple/",
             "https://www.scrapethissite.com/pages/forms/", "https://www.scrapethissite.com/pages/ajax-javascript/#2013",
             "https://www.scrapethissite.com/pages/frames/", "https://www.scrapethissite.com/pages/advanced/",
             "https://mockaroo.com/", "https://github.com/realpython/fake-jobs",
             "https://nigeria.opendataforafrica.org/", "https://finance.yahoo.com/",
             "https://old.reddit.com/"]

    print(f"{"=" * 20} TESTING {"=" * 20}\n")
    logging.info(f"Starting Script Process\n")
    task_time, errors, results = process_multiple_cpu_bound(url_list)

    logging.info(f"Script Process Completed\n")
    sequential_time = task_time["seq_time_threaded"]
    threadpool_time = task_time["cpu_time_threaded"]
    async_thread_time = task_time["cpu_time_async"]
    processpool_time = task_time["cpu_time_process"]
    processpool_thread_time = task_time["all_cpu_time_process"]

    logging.info("Printing Process Contents")

    logging.info("Printing Process Time")
    print(f"{"=" * 20} TIME COMPARISON {"=" * 20}")
    print(f"Sequential Time: {sequential_time} secs")
    print(f"ThreadPool Time: {threadpool_time} secs")
    print(f"AsyncThread Time: {async_thread_time} secs")
    print(f"ProcessPool Waiting For Threads Time: {processpool_thread_time} secs")
    print(f"ProcessPool on Processes Time: {processpool_time} secs")
    print()

    logging.warning("Checking for Url Errors")
    print(f"{"=" * 20} URL ERRORS {"=" * 20}")
    if not errors:
        print("ALl URLs PARSED SUCCESSFULLY")
        logging.info("No Errors Found")

    else:
        logging.error("Errors Found | Printing")
        for dcts in errors:
            url = dcts["url"]
            error = dcts["content"]
            print(f"Url: {url} | Error: {error}")


        for dcts in results:
            if "error" in dcts:
                url = dcts["url"]
                error = dcts["error"]
                print(f"Url: {url} | Error: {error}")
    print()

    logging.info("Printing Process Results\n")
    print(f"{"=" * 20} RESULTS {"=" * 20}")
    for dcts in results:
        if not "error" in dcts:
            url = dcts["url"]
            words_analyzed = dcts["words"]
            html_analyzed = dcts["html"]
            print(f"For URL: {url}")
            print()
            print(f"WORD INFERENCE:")
            print(f"Total Word Count: {words_analyzed["total_word_count"]}")
            print(f"Word List: {words_analyzed["word_list"]}")
            print(f"Word Frequency: {words_analyzed["word_frequency"]}")
            print(f"Character Distributions: {words_analyzed["character_distributions"]}")
            print(f"Longest Word: {words_analyzed["longest_word"]}")
            print(f"Avg. Word Length: {words_analyzed["avg_word_length"]}")
            print(f"Most Common Word: {words_analyzed["most_common_word"]}")
            print()

            print(f"HTML INFERENCE:")
            print(f"All Page Links: {html_analyzed["all_page_links"]}")
            print(f"HTMl Tags Count: {html_analyzed["html_tags_count"]}")
            print(f"Word Frequency Dictionary: {html_analyzed["word_frequency_dictionary"]}")
            print()


    logging.info("Scrit Ended\n")




"""i did something i wanted to try for a long time, linking processes to threads, that means different processes handles
different threads which handles different task and that made me giggle, i dont know if it makes my script run faster or otherwise
i also had issues with dicts, i used [] instead of simply just using, i didnt know the diff btw .json and .json() but to
be fair, i havent learnt json yet"""