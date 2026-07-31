# 🧠 Readme for NERDs.md
> Internal Technical Documentation,  Analytics Baby!

For Programming Logic and Reasoning open `ReadmeGEEK.md`.

Simply want to run the script `Readme.md`.

---

# Table of Contents

- Project Overview
- Project DNA
- Repository Statistics
- External Dependencies
- Global Objects
- High-Level Architecture
- Execution Pipeline
- Architectural Characteristics
- Functions Reference 
- Analysis & Processing Layer
- Utility Functions
- Concurrency Architecture
- Master Function
- Logging System
- Error Handling
- Performance Measurements 
- Complexity Overview
- Known Limitations 
- Appendix
- Conclusion

---

# Project Overview

This Script is a hybrid web scraping and content analysis engine designed to compare multiple approaches to concurrent execution in Python while simultaneously extracting useful information from web pages.

The Script separates its workload into two independent phases:

1. **I/O Bound Operations**
   - Downloading web pages
   - Managing retries
   - Handling HTTP failures
   - Concurrent network requests


2. **CPU Bound Operations**
   - Parsing HTML
   - Cleaning extracted text
   - Word frequency analysis
   - Character distribution analysis
   - HTML tag analysis

The project intentionally demonstrates the interaction between three different concurrency models:

- Asyncio
- ThreadPoolExecutor
- ProcessPoolExecutor

As they cooperate within a single execution pipeline.

---

# Project DNA

| Category | Value |
|-----------|-------|
| Language | Python 3 |
| Programming Style | Functional |
| Architecture | Multi-stage Pipeline |
| Primary Domain | Web Scraping |
| Secondary Domain | HTML Analysis |
| Execution Model | Hybrid Concurrent |
| I/O Strategy | Asyncio + Threads |
| CPU Strategy | Multiprocessing |
| Logging | Rotating File Logger |
| HTML Parser | BeautifulSoup4 |
| Word Analysis | collections.Counter |
| Output Format | Nested Dictionaries |

---

# Repository Statistics

> Statistics generated from the current source file.

| Metric | Value |
|---------|-------|
| Source Files | 1 |
| Functions | 12 |
| Async Functions | 2 |
| Classes | 0 |
| Thread Pools | 1 |
| Process Pools | 1 |
| Async Task Groups | 1 |
| Semaphores | 1 |
| HTML Parser | BeautifulSoup |
| Logging System | RotatingFileHandler |
| HTTP Clients | aiohttp + requests |

---

# External Dependencies

## Standard Library

| Module | Purpose |
|---------|----------|
| asyncio | Asynchronous execution framework |
| logging | Runtime logging |
| time | Performance benchmarking |
| pathlib | Cross-platform filesystem handling |
| concurrent.futures | ThreadPool and ProcessPool execution |
| collections.Counter | Frequency analysis |

---

## Third Party Libraries

| Library | Purpose |
|----------|----------|
| aiohttp | Asynchronous HTTP requests |
| requests | Synchronous HTTP requests |
| BeautifulSoup4 | HTML parsing and extraction |

---

# Global Objects

## LOG Directory

Creates a dedicated directory for runtime log files.


---

## Rotating File Handler

Logging is configured using a RotatingFileHandler.

Configuration:

| Property | Value |
|----------|------|
| Maximum Log Size | 5 MB |
| Backup Files | 3 |
| Encoding | UTF-8 |

---

# High-Level Architecture

The project is composed of four major subsystems.

```
                URL List
                   │
                   ▼
        process_multiple_cpu_bound()
                   │
         ┌─────────┴──────────┐
         │                    │
         ▼                    ▼
   URL Partitioning     ProcessPoolExecutor
                              │
       ┌───────────────┬──────────────┐
       ▼               ▼              ▼
 Asyncio Pool    ThreadPool Pool   Sequential
       │               │              │
       └───────────────┴──────────────┘
                     │
             Scraped Responses
                     │
             process_task()
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
 analyze_words()          analyze_html()
         │                       │
         └───────────┬───────────┘
                     ▼
             Structured Results
```

---


# Execution Pipeline

The execution flow can be summarized as follows.

```
User

↓

Input URL List

↓

Split URLs into Three Equal Groups

↓

Asyncio Scraper
ThreadPool Scraper
Sequential Scraper

↓

Collect Successful Responses

↓

Discard Failed Responses

↓

ProcessPoolExecutor

↓

HTML Parsing

↓

Word Analysis

↓

HTML Analysis

↓

Aggregate Results

↓

Performance Metrics

↓

Return Final Output
```

---

# Architectural Characteristics

## Strengths

✔ Separation of I/O-bound and CPU-bound workloads

✔ Modular functional design

✔ Retry support

✔ Logging throughout execution

✔ Independent analysis modules

✔ Structured dictionary outputs

✔ Parallel execution

✔ Graceful failure handling

---

## Potential Bottlenecks

- Duplicate HTML parsing in multiple analysis stages.
- Sequential execution included primarily for benchmarking.
- Frequent dictionary creation may increase memory allocation for very large workloads.
- HTML content is parsed multiple times before all analyses complete.

# Function Reference

This section documents every function in the project, describing its responsibility, relationships with other functions, inputs, outputs, and role within the execution pipeline.

---

# fetch_url_async()

**Location**: Async Scraping Module

**Function Type**: Asynchronous Worker (coroutine)

**Purpose**: Downloads a single URL asynchronously using an `aiohttp.ClientSession`.

Concurrency is controlled through an `asyncio.Semaphore`, ensuring that the number of simultaneous requests never exceeds the configured worker limit.

The function also implements automatic retry logic and standardized error reporting.

---

## Parameters

| Name | Type | Description |
|------|------|-------------|
| session | aiohttp.ClientSession | Shared HTTP session |
| url | str | Target URL |
| max_retry | int | Maximum retry attempts |
| semaphore | asyncio.Semaphore | Limits concurrent requests |

---

## Returns

Success

```python
{
    "url": str,
    "success": True,
    "content": str | dict,
    "type": str
}
```

Failure

```python
{
    "url": str,
    "success": False,
    "content": Exception | str
}
```

---

## Called By

- fetch_multiple_urls_async()

---

## Calls

- session.get()
- asyncio.sleep()

---

## Handles

- HTML pages
- JSON responses
- Invalid status codes
- Network failures
- Timeout failures
- Unexpected exceptions

---

## Internal Workflow

```
Acquire Semaphore

↓

Send Request

↓

Status == 200 ?

├── No
│      Retry
│
└── Yes
       │
       ▼
Check Content-Type

├── HTML
│      Return Text
│
└── JSON
       Return JSON
```

---

## Notes

This function never raises an exception to the caller.

All failures are converted into standardized dictionaries.

---

# fetch_multiple_urls_async()

**Function Type**: Async Coordinator (The Mother Brain)

**Purpose**: Creates a shared `aiohttp.ClientSession`, starts all asynchronous download tasks, waits for their completion, and records total execution time.

This function acts as the controller for every asynchronous network request.

---

## Parameters

| Name | Type |
|------|------|
| urls | list[str] |
| max_retry | int |
| max_workers | int |

---

## Returns

List containing

- Individual scrape dictionaries
- CPU timing dictionary

---

## Called By

- run_async()

---

## Calls

- fetch_url_async()

---

## Internal Workflow

```
Create Session

↓

Create Semaphore

↓

Create TaskGroup

↓

Launch fetch_url_async()

↓

Wait for Completion

↓

Collect Results

↓

Append CPU Time

↓

Return
```

---

## Notes

Uses Python's `asyncio.TaskGroup`, providing structured concurrency.

---

# fetch_url_threaded()

**Function Type**: Thread Worker

**Purpose**: Downloads a single URL using the synchronous Requests library.

Unlike the asynchronous version, this function blocks until the request completes, making it suitable for execution inside a `ThreadPoolExecutor`.

---

## Parameters

| Name | Type |
|------|------|
| url | str |
| max_retry | int |

---

## Returns

Same dictionary format as `fetch_url_async()`.

---

## Called By

- fetch_multiple_threaded()
- sequential_fetch()

---

## Calls

- requests.get()

---

## Handles

- ConnectionError
- TimeoutError
- RequestException
- Generic Exception

---

## Notes

Shares nearly identical retry logic with the asynchronous implementation to keep output formats consistent.

---

# fetch_multiple_threaded()

**Function Type**: ThreadPool Controller

**Purpose**: Creates a `ThreadPoolExecutor`, submits one scraping task per URL, waits for every thread to complete, and records execution time.

---

## Parameters

| Name | Type |
|------|------|
| urls | list[str] |
| max_retry | int |
| max_workers | int |

---

## Returns

List containing

- Scrape results
- CPU timing dictionary

---

## Called By

- process_multiple_cpu_bound()

---

## Calls

- fetch_url_threaded()

---

## Workflow

```
Create ThreadPool

↓

Submit Tasks

↓

Wait

↓

Collect Results

↓

Append Timing

↓

Return
```

---

# sequential_fetch()

**Function Type**: Sequential Baseline

**Purpose**: Processes every URL one after another without any concurrency.

This function serves as the performance baseline used to compare ThreadPool and Asyncio execution.

---

## Parameters

| Name | Type |
|------|------|
| urls | list[str] |
| max_retry | int |

---

## Called By

- process_multiple_cpu_bound()

---

## Calls

- fetch_url_threaded()

---

## Notes

No concurrency is used.

Execution order is strictly linear.

This function exists primarily for benchmarking.

---

# Analysis & Processing Layer

This Functions are responsible for transforming raw HTML into structured information.

The project separates data acquisition from data analysis, allowing network operations and CPU-intensive work to remain independent.

This improves modularity while making future extensions significantly easier.

---

# clean_words()

**Function Type**: Data Normalization

**Purpose**: Parses raw HTML into plain text and removes unwanted punctuation and symbols before any statistical analysis is performed.

Every analysis function in the project depends on this function, making it the primary preprocessing stage.

---

## Parameters

| Name | Type | Description |
|------|------|-------------|
| content | str | Raw HTML document |

---

## Returns

Tuple

```python
(
    BeautifulSoup,
    list[str]
)
```

The tuple contains

- Parsed BeautifulSoup document
- Cleaned list of words

---

## Called By

- analyze_words()
- analyze_html()

---

## Calls

- BeautifulSoup()
- page.text.split()

---

## Internal Workflow

```
Receive HTML

↓

Parse HTML

↓

Extract Visible Text

↓

Split Into Words

↓

Stage 1 Cleaning
(strip punctuation)

↓

Stage 2 Cleaning
(remove remaining symbols)

↓

Remove Empty Tokens

↓

Return
```

---

## Cleaning Strategy

The cleaning process occurs in two independent stages.

### Stage 1

Uses `str.strip()` to remove punctuation surrounding words.

Example

```
"hello!"
↓

hello
```

---

### Stage 2

Iterates through every remaining character and removes internal unwanted symbols.

Example

```
Py@th#on

↓

Python
```

---

## Notes

This function intentionally separates parsing from statistical analysis.

Keeping cleaning isolated makes every analysis function deterministic and reusable.

---

# analyze_words()

**Function Type**: Statistical Analyzer

**Purpose**: Produces lexical statistics describing the textual contents of a webpage.

This function performs word-level analysis rather than HTML analysis.

---

## Parameters

| Name | Type |
|------|------|
| content | str |

---

## Returns

Dictionary

Containing

- Total word count
- Word list
- Word frequency
- Character distribution
- Longest word
- Average word length
- Most common word

---

## Called By

- process_task()

---

## Calls

- clean_words()
- Counter()

---

## Internal Workflow

```
Receive HTML

↓

Clean Words

↓

Count Words

↓

Count Characters

↓

Determine Longest Word

↓

Calculate Average Length

↓

Determine Most Common Word

↓

Return Dictionary
```

---

## Generated Statistics

| Statistic | Description |
|-----------|-------------|
| total_word_count | Number of cleaned words |
| word_frequency | Occurrences of every word |
| character_distribution | Frequency of every character |
| longest_word | Longest detected word |
| avg_word_length | Mean word size |
| most_common_word | Highest frequency word |

---

## Notes

The function never modifies HTML.

It operates solely on cleaned text produced by `clean_words()`.

---

# analyze_html()

**Function Type**: Structural Analyzer

**Purpose**: Extracts structural information from an HTML document.

The function studies the page itself rather than its textual contents.

---

## Parameters

| Name | Type |
|------|------|
| content | str |

---

## Returns

Dictionary

Containing

- All discovered hyperlinks
- HTML tag frequencies
- Word frequency dictionary

---

## Called By

- process_task()

---

## Calls

- clean_words()
- BeautifulSoup.find_all()

---

## Internal Workflow

```
Receive HTML

↓

Clean Words

↓

Locate Every HTML Tag

↓

Locate Every Anchor

↓

Extract href

↓

Remove Invalid Links

↓

Count Tags

↓

Return Dictionary
```

---

## Generated Statistics

| Statistic | Description |
|-----------|-------------|
| all_page_links | Unique hyperlinks |
| html_tags_count | Count of every HTML element |
| word_frequency_dictionary | Word frequency |

---

## Notes

Hyperlinks are stored inside a set, automatically removing duplicate URLs.

---

# process_task()

**Function Type**: Analysis Coordinator

---

## Purpose

Acts as the bridge between scraping and analysis.

It receives downloaded content and determines whether the response can be processed.

Only HTML/text responses continue through the analysis pipeline.

---

## Parameters

| Name | Type |
|------|------|
| dicts | dict |

---

## Returns

Successful Analysis

```python
{
    "url": ...,
    "words": ...,
    "html": ...
}
```

Failure

```python
{
    "url": ...,
    "error": ...
}
```

---

## Called By

- ProcessPoolExecutor

---

## Calls

- analyze_words()
- analyze_html()

---

## Internal Workflow

```
Receive Response

↓

Check Content Type

↓

HTML ?

├── No
│      Return Error
│
└── Yes
       │
       ▼
Analyze Words

↓

Analyze HTML

↓

Merge Results

↓

Return
```

---

## Decision Logic

| Content-Type | Action |
|--------------|--------|
| text/html | Analyze |
| text/plain | Analyze |
| application/json | Reject |
| Other | Reject |

---

## Notes

This function serves as the project's decision gate.

Every downloaded response must pass through this function before entering the analysis stage.

---

# Utility Functions

Although small, the following functions perform critical orchestration tasks.

---

# run_async()

## Purpose

Provides a synchronous wrapper around the asynchronous scraping engine using `asyncio.run()`.

This allows asynchronous code to execute inside a `ProcessPoolExecutor`.

---

## Called By

- process_multiple_cpu_bound()

---

# split_urls()

## Purpose

Divides the incoming URL collection into three approximately equal partitions.

Each partition is assigned to a different execution strategy.

---

## Returns

```
(
    url_set1,
    url_set2,
    url_set3
)
```

---

## Notes

This function is responsible for workload distribution across the project's concurrency models.

---

# Layer Relationships

```
process_task()

├── analyze_words()
│      │
│      └── clean_words()
│
└── analyze_html()
       │
       └── clean_words()
```

Notice that both analysis functions depend on the same preprocessing function.

This demonstrates one of the project's central design decisions:

> **Normalize once, analyze many times.**

Although the current implementation calls `clean_words()` twice, the architecture itself is designed around a shared preprocessing stage. A future optimization could cache or reuse the cleaned output to avoid duplicate work.

# Concurrency Architecture

The project's concurrency model is intentionally divided into two independent execution phases.

---

## Stage 1: URL Acquisition

Responsible for retrieving webpage contents.

Execution methods:

- Asyncio
- ThreadPoolExecutor
- Sequential Fetch

These three methods execute independently and are later compared using execution time.

```
                URL List
                    │
                    ▼
             split_urls()
                    │
      ┌─────────────┼─────────────┐
      ▼             ▼             ▼
  Asyncio      ThreadPool     Sequential
      │             │             │
      └─────────────┼─────────────┘
                    ▼
          Scraped Response Objects
```

---

## Stage 2 — Content Processing

After successful downloads are collected, every valid response is submitted to a `ProcessPoolExecutor`.

Unlike the previous stage, this phase performs computational work rather than waiting for network activity.

```
Successful Responses

        │

        ▼

ProcessPoolExecutor

        │

        ▼

process_task()

        │

        ▼

Word Analysis
HTML Analysis

        │

        ▼

Structured Results
```

---

## Hybrid Execution Model

| Workload | Executor |
|----------|----------|
| Network Requests | Asyncio |
| Blocking Requests | ThreadPoolExecutor |
| Performance Baseline | Sequential |
| HTML Analysis | ProcessPoolExecutor |

---

# Master Function (ALL FATHER)

## process_multiple_cpu_bound()

---

### Function Type

Primary Controller

---

### Purpose

Coordinates every major component within the project.

This function is responsible for:

- Dividing workloads
- Scheduling scraping methods
- Collecting successful responses
- Recording timing statistics
- Starting CPU analysis
- Returning the final processed output

Every execution path eventually passes through this function.

---

## Parameters

| Name | Type | Description |
|------|------|-------------|
| urls | list[str] | URLs to process |
| max_rty | int | Maximum retries |
| max_wrks | int | Maximum worker threads |
| max_wrks_pool | int | Maximum worker processes |

---

## Returns

Tuple

```python
(
    collected_time,
    collected_errors,
    processed_results
)
```

---

## Calls

- split_urls()
- run_async()
- fetch_multiple_threaded()
- sequential_fetch()
- process_task()

---

## Internal Workflow

```
Receive URLs

↓

Split URLs

↓

Start ProcessPool

↓

Launch

Asyncio
ThreadPool
Sequential

↓

Collect Results

↓

Separate

Successes
Errors

↓

ProcessPool

↓

process_task()

↓

Merge Results

↓

Return
```

---

## Output Objects

### Timing Dictionary

Contains execution times for every concurrency strategy.

Example

```python
{
    "cpu_time_async": ...,
    "cpu_time_threaded": ...,
    "seq_time_threaded": ...,
    "cpu_time_process": ...,
    "all_cpu_time_process": ...
}
```

---

### Error Collection

Contains every failed request.

```python
[
    {
        "url": "...",
        "success": False,
        "content": Exception
    }
]
```

---

### Processed Results

Contains analyzed webpage data.

```python
[
    {
        "url": "...",
        "words": {...},
        "html": {...}
    }
]
```

---

# Logging System

The project implements centralized logging using Python's logging module.

Every subsystem writes to the same rotating log file.

---

## Log Levels

| Level | Usage |
|--------|-------|
| DEBUG | Execution tracing |
| INFO | Successful operations |
| WARNING | Recoverable problems |
| ERROR | Failures |

---

## Logged Events

Examples include:

- URL requests
- Retry attempts
- HTML parsing
- Analysis completion
- Thread creation
- Process completion
- CPU timings
- Errors

---

# Error Handling

The scraper follows a defensive error-handling strategy.

Instead of allowing exceptions to terminate execution, every error is converted into a standardized response dictionary.

This allows processing of remaining URLs even when individual requests fail.

---

## Async Exceptions

- ClientConnectorError
- ClientHttpProxyError
- ServerDisconnectedError
- ClientPayloadError
- TimeoutError
- Generic Exception

---

## Thread Exceptions

- ConnectionError
- TimeoutError
- RequestException
- Generic Exception

---

# Performance Measurements

The project measures execution time for each concurrency strategy independently.

Recorded metrics include:

| Metric | Description |
|---------|-------------|
| cpu_time_async | Asyncio execution time |
| cpu_time_threaded | ThreadPool execution time |
| seq_time_threaded | Sequential execution time |
| cpu_time_process | HTML analysis time |
| all_cpu_time_process | Overall ProcessPool duration |

---

# Data Flow Summary

```
Input URLs

↓

Partition

↓

Scrape

↓

Collect Responses

↓

Filter Errors

↓

Analyze HTML

↓

Analyze Words

↓

Generate Statistics

↓

Return Results
```

---

# Complexity Overview

The following estimates describe the dominant time complexity of the primary components.

| Component | Complexity |
|-----------|------------|
| URL Splitting | O(n) |
| Sequential Fetch | O(n) |
| ThreadPool Submission | O(n) |
| Async Task Creation | O(n) |
| Word Cleaning | O(w) |
| Word Frequency | O(w) |
| Character Counting | O(c) |
| HTML Tag Counting | O(t) |

Where:

- **n** = Number of URLs
- **w** = Number of words
- **c** = Number of characters
- **t** = Number of HTML tags

Actual runtime depends primarily on network latency rather than algorithmic complexity during the scraping stage.

---

# Known Limitations

Current implementation limitations include:

- HTML content is parsed more than once during analysis.
- `clean_words()` is called independently by multiple analysis functions.
- URL partitions may become uneven when the input size is not divisible by three.
- ThreadPool and Asyncio process identical workloads independently for benchmarking rather than cooperative execution.

These limitations do not affect correctness but may influence performance for very large datasets.

---

# Appendix

## Function Dependency Graph

```
process_multiple_cpu_bound()

├── split_urls()

├── run_async()
│      │
│      └── fetch_multiple_urls_async()
│              │
│              └── fetch_url_async()
│
├── fetch_multiple_threaded()
│      │
│      └── fetch_url_threaded()
│
├── sequential_fetch()
│      │
│      └── fetch_url_threaded()
│
└── process_task()
       ├── analyze_words()
       │      └── clean_words()
       │
       └── analyze_html()
              └── clean_words()
```

---

# Conclusion

This project demonstrates a hybrid concurrent architecture by combining asynchronous I/O, multithreading, multiprocessing, and structured HTML analysis within a single processing pipeline.

Although originally developed as a comparative experiment between concurrency models, the resulting architecture naturally separates data acquisition, preprocessing, analysis, and result aggregation into distinct functional layers.

The implementation serves both as a practical web scraping utility and as a study of Python's concurrency mechanisms, highlighting how different execution models can coexist within a unified workflow.