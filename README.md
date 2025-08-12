# QuickNews: AI-Powered News Summarizer & Insight Engine

<div align="center">

An intelligent web application that leverages the **Google Gemini API** to instantly summarize news articles, answer complex questions, and deliver insights through a modern, conversational UI.

</div>

---

## 📌 Table of Contents
- [About](#about)
- [Key Features](#key-features)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

---

## 📰 About

In today's fast-paced world, staying informed is essential — but reading lengthy articles can be time-consuming.  
**QuickNews** solves this by providing **concise, AI-generated summaries** from any news article URL.

It’s more than just a summarizer — QuickNews is also an **answer engine**. You can ask any question, and it will:
- Perform a **web search** (if needed)
- Scrape and analyze multiple top sources **concurrently**
- Use the **Google Gemini API** to deliver accurate, context-aware responses

The app combines a **robust Django backend** with a **sleek, responsive JavaScript frontend** for a seamless experience.

---

## ✨ Key Features

- **🤖 Dual-Mode AI Processing**
  - **URL Summarization**: Paste a news link to get a quick, accurate summary, author details, and sentiment analysis.
  - **Intelligent Q&A**: Ask natural-language questions and receive direct, AI-powered answers.

- **🌐 Context-Aware Search**
  - Automatically searches the web and scrapes top results when additional context is needed.

- **⚡ High-Performance Backend**
  - Built with Django and **optimized for concurrency** in web scraping to keep responses fast.

- **💬 Modern Conversational UI**
  - Clean, chat-based interface styled with Tailwind CSS for a smooth, app-like feel.

- **🗂 Persistent Chat History**
  - Save and revisit all summarized articles, grouped by date.

---

## 🛠 Tech Stack

**Backend**
- Django
- Concurrent web scraping

**Frontend**
- Vanilla JavaScript
- Tailwind CSS

**AI / NLP**
- Google Gemini API
- NLTK
- Newspaper3k
- TextBlob
- BeautifulSoup

---

## 🚀 Getting Started

Follow these steps to set up QuickNews locally.

### **Prerequisites**
- Python 3.10+
- API Key from [Google AI Studio](https://aistudio.google.com/)

### **Installation**
1. **Clone the repository**
   ```bash
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
