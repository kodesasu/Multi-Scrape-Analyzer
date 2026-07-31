# Web Scraping & HTML Analysis Tool

For Analytics head to `ReadmeNERD.md`.

For Programming Logic and Reasoning open `ReadmeGEEK.md`.


# 
A Python Script that scrapes one or more websites and automatically analyzes their textual and HTML contents.

The program can:

- 🌐 Download multiple web pages
- 📊 Analyze word statistics
- 🔗 Extract hyperlinks
- 🏷 Count HTML tags
- 📈 Compare scraping performance
- 📝 Generate execution logs

---

# Features

- Multiple website scraping
- Automatic retry on failed requests
- Word frequency analysis
- Character frequency analysis
- HTML tag counting
- Hyperlink extraction
- Performance comparison
- Automatic logging
- Error reporting

---

# Requirements

Python 3.11 or later

Required packages:

```bash
pip install aiohttp requests beautifulsoup4
```

---

# Installation

Clone the repository.

```bash
git clone hhttps://github.com/kodesasu/office-politics-oop.git
```

Move into the project folder.

```bash
cd repository
```

Install the required packages.

```bash
pip install -r requirements.txt
```

---

# Quick Start

Open the script and locate the `url_list`.

```python
url_list = [
    "https://example.com",
    "https://python.org",
    "https://github.com"
]
```

Replace these URLs with the websites you want to analyze.

Run the script.

```bash
python main.py
```

---

# What Happens When You Run It?

The application will automatically:

1. Download every website.
2. Retry failed requests.
3. Analyze webpage text.
4. Analyze HTML structure.
5. Measure execution time.
6. Display the results.
7. Save logs to a log file.

No additional configuration is required.

---

# Understanding the Output

The application prints four sections.

## 1. Time Comparison

Shows how long each scraping method took.

Example:

```text
Sequential Time: 4.31 secs

ThreadPool Time: 1.54 secs

Async Time: 1.17 secs

Process Time: 0.82 secs
```

---

## 2. URL Errors

Displays websites that could not be downloaded.

Example:

```text
URL:
https://example.com

Error:
Connection timed out
```

If no errors occur, you'll see:

```text
ALL URLs PARSED SUCCESSFULLY
```

---

## 3. Word Analysis

For every webpage the application displays:

- Total words
- Word frequency
- Character frequency
- Longest word
- Average word length
- Most common word

Example:

```text
Total Word Count:
1573

Most Common Word:
python

Average Word Length:
5.82
```

---

## 4. HTML Analysis

Displays structural information about the webpage.

Including:

- All discovered hyperlinks
- HTML tag counts
- Word frequency dictionary

---

# Log Files

Every execution automatically creates a log file.

```
LOG/
    main.log
```

The log records:

- Successful requests
- Failed requests
- Retry attempts
- Performance timings
- Errors

Older logs are automatically archived when the log file reaches its size limit.

---

# Customizing the Scraper

You can change the number of retry attempts.

```python
process_multiple_cpu_bound(
    url_list,
    max_rty=5
)
```

You can also adjust the worker count.

```python
process_multiple_cpu_bound(
    url_list,
    max_wrks=8,
    max_wrks_pool=4
)
```

Increasing these values may improve performance depending on your hardware and internet connection.

---

# Troubleshooting

### Import Errors

Install the required packages.

```bash
pip install -r requirements.txt
```

---

### Permission Error

Ensure Python has permission to create the `LOG` directory.

---

### Websites Not Responding

Some websites block automated requests.

Try another website or reduce the request frequency.

---

### Slow Performance

Performance depends on:

- Internet speed
- Website response time
- CPU performance
- Number of URLs

---

# Just Incase Questions

### Does this modify websites?

No.

The script only downloads publicly available webpage data.

---

### Can it scrape multiple websites?

Yes.

Just add more URLs to the `url_list`.

---

### Does it support JSON APIs?

It can download JSON responses, but HTML analysis is only performed on HTML/text content.

---

### Where are logs stored?

Inside the automatically created `LOG` folder.

---

# License

See the project's LICENSE file for licensing information.