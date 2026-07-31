# Readme for GEEKs

> *The design notes, thought process, mistakes, and lessons learned while building this project.*

For Analytics head to `ReadmeNERD.md`.

Simply want to run the script `Readme.md`.



---

# So... What Are You Looking At?

This project started as a assignment.

The task was:

> **Build a comprehensive concurrent processing system using modern Python concurrency.**

I had just finished learning **Threads** and **Processes**, and honestly, it was pretty nice. I was curious to how they really worked the way they do and that mindset eventually became this project.

I settled on building a multi-web scraper because web scraping naturally fits concurrency. Most of the time is spent waiting on network requests, making it a great playground for comparing different execution models.

But just downloading web pages and saving them felt boring.

Once I had the pages, I wanted to do something useful with them.

Instead of stopping at scraping, I decided to analyze the downloaded pages by extracting words, counting frequencies, inspecting HTML tags, collecting links, and generally seeing what interesting information could be pulled from them.

That decision was made to really test the difference between **Threads** and **Processes**.

---

# Why I Built It This Way

This project was also an excuse to try something I had wanted to experiment with for a long time.

I wanted to see what would happen if I combined **processes** with **threads**.

In my implementation, different processes are responsible for different workloads, and inside those workloads different threads handle different tasks.

Did it make the program faster?

Honestly... I don't know.

I just wanted to try it.

And I won't lie, it made me giggle seeing the whole thing working together. which i think justified my reason to do it.

Another goal was to compare Python's concurrency models under the same workload.

Rather than assuming one approach was better, I wanted actual numbers.

So I implemented three different execution strategies:

* Sequential execution
* ThreadPoolExecutor
* Asyncio

Then I measured how long each one took.

Sequential execution became my baseline.

---

# What I Observed

People often say:

> "Asyncio is faster."

And in many situations, that's true.

But after running my own tests, I noticed something interesting.

When working with webpages that frequently fail, return invalid status codes, or require retries, my ThreadPool implementation often performed better than my Asyncio implementation.

Maybe that's because of my implementation.

Maybe it's because of the retry strategy.

Maybe it's something else entirely.

I'm not claiming it's universally true.

I'm simply documenting what I observed while testing this project.


---

# Parsing HTML Was Harder Than I Expected

Cleaning webpage text turned out to be one of the most frustrating parts of the project.

At first it sounded easy, just extract the words.

Then the questions started: Should this count as one word?

```
over-worked
```

What about this?

```
dont.wait
```

Or this?

```
https://www.facebook.com/facebook/
```

I wanted to count **words** not characters so ok.

That meant making assumptions about what a "word" actually is.

I ended up writing a cleaning pipeline that strips punctuation, removes unwanted symbols, and prepares the text before any analysis begins.

It was not perfect, but it taught me that preprocessing data is often harder than analyzing it.

---

# Counter Was a Pleasant Surprise

One of my favorite discoveries during this project was `collections.Counter`.

Before this assignment I knew dictionaries, defaultdict, and namedturple fairly well. 

What I didn't know was that `Counter` is essentially a specialized dictionary designed specifically for counting things.

Once I started using it, a lot of my code became cleaner and much easier to read.

Sometimes Python really is That GUY

---

# Asyncio Lessons

This project taught me much more than just syntax.

One of the biggest lessons was learning how asynchronous context managers stack together.

I ran into several confusing bugs before realizing something important.

When multiple asynchronous context managers are nested, the one responsible for calling coroutines should generally be the deepest context manager in the stack.

In my case that meant carefully arranging things like:

* `aiohttp.ClientSession`
* `asyncio.TaskGroup`

Once I understood that relationship, everything suddenly became much easier to reason about.

---

# TaskGroup vs gather()

Another lesson came from comparing `asyncio.TaskGroup` with `asyncio.gather()`.

From my experience:

* Use **`gather()`** when you want every task to continue running even if one fails.
* Use **`TaskGroup`** when failure should stop the entire operation.

Neither is "better."

They're simply designed for different situations.

Understanding *when* to use each one is more important.

---

# The Bugs That Taught Me the Most

Looking back, some of the biggest lessons came from mistakes.

At one point I completely forgot about dictionary comprehensions.

I even forgot that dictionaries have methods for safely checking and inserting values.

Instead...

I literally started looping through dictionaries just to check whether a key already existed.

Yes.

It was that bad.

Another small lesson was discovering the difference between:

```python
response.json
```

and

```python
response.json()
```

To be fair, I hadn't learned JSON yet, so that confusion made sense in hindsight.

Sometimes not knowing something is exactly what forces you to learn it properly.

---

# What Is This Project Demonstrating?

On the surface, it's a web scraper.

But that's not really what it's about.

It's a practical comparison of Python's concurrency tools.

After building it, these are my personal takeaways.

- If you have lots of I/O-bound tasks with very few expected failures, Asyncio is an excellent choice.


- If your workload is likely to encounter many errors and you want complete control over how work is distributed, I still enjoy working with threads.

  In fact, my favorite approach isn't `ThreadPoolExecutor`.

  It's building my own worker threads with queues, producers, and consumers. It requires more code, but I enjoy the control it provides.


- As for CPU-intensive work, Processes still win.

---

# What I Would Change or Add Later On

There are plenty of things I'd like to improve.

Some ideas include:

* Saving downloaded pages to disk.
* Building a command-line interface.
* Exporting analysis results.
* Supporting additional output formats.
* Improving the text-cleaning pipeline.
* Adding more configurable analysis modules.

But for now...

Assignments keep coming, and it's time to move on to the next challenge.


---

# Final Thoughts

This Project taught me far more than I expected.

I learned about asynchronous programming, multithreading, multiprocessing, requests, retries, HTML (yes the language), HTML parsing, text preprocessing, structured concurrency, and probably most importantly...

I learned that the best way to understand a concept is to build something with it.

Thanks for reading.

If you're interested in the technical implementation and internal architecture, head over to **ReadmeNERD.md**.

If you simply want to run the script yourself, check out **ReadmeUSER.md**.

Until the next project...
