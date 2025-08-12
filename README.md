QuickNews: AI-Powered News Summarizer & Insight Engine
<div align="center">

An intelligent web application that uses the Google Gemini API to provide instant summaries of news articles, answer complex questions, and deliver insights with a modern, conversational UI.

</div>

<p align="center">
<a href="#about-the-project">About</a> •
<a href="#key-features">Features</a> •
<a href="#built-with">Tech Stack</a> •
<a href="#getting-started">Getting Started</a> •
<a href="#roadmap">Roadmap</a> •
<a href="#contributing">Contributing</a>
</p>

About The Project
In today's fast-paced world, staying informed is crucial, but reading long articles can be time-consuming. QuickNews tackles this problem by acting as an intelligent agent that provides concise, AI-generated summaries from any article URL.

But it doesn't stop there. QuickNews also functions as a powerful answer engine. Ask it any question, and it will use the Google Gemini API and a concurrent web-scraping backend to deliver comprehensive, context-aware answers. Built with a robust Django backend and a sleek, responsive vanilla JavaScript frontend, QuickNews is designed for a seamless and intuitive user experience.

Key Features
🤖 Dual-Mode AI Processing: Intelligently handles two types of input:

URL Summarization: Paste any news article link to get a quick, accurate summary, author details, and sentiment analysis.

Intelligent Q&A: Ask complex questions in natural language to get direct answers powered by the Google Gemini API.

🌐 Context-Aware Search: For questions requiring up-to-date information, the app performs a web search, scrapes the top results concurrently, and feeds the context to the LLM for a rich, informed response.

⚡ High-Performance Backend: Built with Django and optimized with concurrent web scraping to ensure fast, non-blocking responses even when gathering data from multiple sources.

✨ Modern Conversational UI: A clean, chat-based interface built with Tailwind CSS and vanilla JavaScript that provides a fluid, app-like experience.

🗂️ Persistent Chat History: All your summarized articles are saved and grouped by date, allowing you to revisit them anytime.

Built With
This project combines a powerful backend with a modern frontend stack.

Backend

Frontend

AI / NLP











NLTK, Newspaper3k, TextBlob, BeautifulSoup

Getting Started
To get a local copy up and running, follow these simple steps.

Prerequisites
Python 3.10 or higher

An API key from Google AI Studio

Installation
Clone the repository:

git clone https://github.com/Muhammedbeig/QuickNews.git
cd QuickNews

Create and activate a virtual environment:

# For Windows
python -m venv venv
.\venv\Scripts\activate

# For macOS/Linux
python3 -m venv venv
source venv/bin/activate

Install the required packages:

pip install -r requirements.txt

Set up your environment variables:
Create a .env file in the project root and add your Google Gemini API key:

GEMINI_API_KEY="YOUR_API_KEY_HERE"

Run the NLTK downloader:
Open a Python shell (python or python3) and run the following to download the 'punkt' tokenizer:

import nltk
nltk.download('punkt')

Apply database migrations:

python manage.py migrate

Run the development server:

python manage.py runserver

The application will be available at http://127.0.0.1:8000/.

Roadmap
[ ] User authentication and dedicated accounts.

[ ] Ability to customize summary length and style.

[ ] Enhanced data visualizations for search results.

[ ] Support for summarizing PDF documents and other file types.

[ ] Dockerize the application for easy deployment.

See the open issues for a full list of proposed features and known issues.

Contributing
Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are greatly appreciated.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement". Don't forget to give the project a star! Thanks again!

Fork the Project

Create your Feature Branch (git checkout -b feature/AmazingFeature)

Commit your Changes (git commit -m 'Add some AmazingFeature')

Push to the Branch (git push origin feature/AmazingFeature)

Open a Pull Request

License
Distributed under the MIT License. See LICENSE for more information.

Contact
Muhammad Beig - LinkedIn - muhammed.beig@icloud.com

Project Link: https://github.com/Muhammedbeig/QuickNews
