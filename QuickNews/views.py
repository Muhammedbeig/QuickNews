from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import ArticleSummary
import nltk
from collections import Counter
from urllib.parse import urlparse
from textblob import TextBlob
from newspaper import Article, ArticleException
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import validators
import requests
import json
import re
import math
import os
import concurrent.futures

# --- Gemini API Key Configuration ---
# IMPORTANT: For the new LLM features to work, you must set the GEMINI_API_KEY 
# in your environment variables where the server is running.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# --- NLTK Data Download ---
# Ensures the necessary sentence tokenizer is available for the fallback summarizer.
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

# --- Main Page View ---
def index(request):
    """Renders the main user interface."""
    return render(request, 'QuickNews/index.html')

# ==============================================================================
# --- NEW ARCHITECTURE HELPER FUNCTIONS ---
# ==============================================================================

def get_website_name(url):
    """Extracts a clean, readable website name from a URL."""
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        # Removes 'www.' from the domain for cleaner display
        return domain[4:] if domain.startswith("www.") else domain
    except:
        return "Unknown Source"

def call_gemini_api(prompt, context=None):
    """
    Handles all calls to the Google Gemini LLM.

    This function is central to the new architecture and operates in two modes:
    1. Direct Query: If only 'prompt' is provided, it asks the LLM a direct question.
    2. Contextual Analysis: If 'prompt' and 'context' are provided, it instructs the
       LLM to answer the user's prompt based *only* on the provided web-scraped text.

    Args:
        prompt (str): The user's original query.
        context (str, optional): The consolidated text scraped from web pages.

    Returns:
        str: The text answer from the LLM, or None if the API call fails.
    """
    if not GEMINI_API_KEY:
        print("CRITICAL: GEMINI_API_KEY environment variable not set. LLM calls are disabled.")
        return None

    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    
    # Dynamically frame the prompt based on whether context is available.
    if context:
        full_prompt = (
            f"Using ONLY the provided text below as context, please provide a clear and comprehensive answer to the following question but don't explicitly say like according to provided text: '{prompt}'\n\n"
            f"---CONTEXT---\n{context}"
        )
    else:
        full_prompt = prompt
    
    payload = {"contents": [{"parts": [{"text": full_prompt}]}]}
    headers = {'Content-Type': 'application/json'}

    try:
        # Increased timeout for potentially larger context payloads from web scraping.
        response = requests.post(api_url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        result = response.json()

        # The API can block a prompt for safety reasons. We handle that gracefully.
        if result.get('promptFeedback', {}).get('blockReason'):
            print(f"Prompt blocked by API. Reason: {result['promptFeedback']['blockReason']}")
            return "My apologies, but I cannot process that request as it violates safety policies."
        
        # Safely access the response text to avoid errors if the structure is unexpected.
        return result['candidates'][0]['content']['parts'][0]['text'].strip()
    except (requests.RequestException, KeyError, IndexError, json.JSONDecodeError) as e:
        print(f"Error during Gemini API call: {e}")
        return None

def _scrape_single_url(url):
    """Helper function to download and parse a single URL. Designed to run in a thread."""
    try:
        # The newspaper library can be slow, so a shorter timeout is better for concurrency.
        article = Article(url, fetch_images=False, request_timeout=10)
        article.download()
        article.parse()
        
        if article.text:
            return f"\n\n--- Content from {url} ---\n" + article.text
    except Exception as e:
        print(f"Skipping URL {url} due to scraping error: {str(e)}")
    return "" # Return empty string on failure to avoid breaking the process

def search_and_scrape_urls(query, num_pages=3):
    """
    Searches DuckDuckGo, then CONCURRENTLY scrapes the full text content from top results.

    This function is used by both the "Search with Globe" feature and the fallback
    mechanism for the standard search.

    Args:
        query (str): The user's search term.
        num_pages (int): The number of top search results to scrape.

    Returns:
        str: A single string containing all the extracted text, or None on failure.
    """
    try:
        search_url = f"https://html.duckduckgo.com/html/?q={query}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        
        search_response = requests.get(search_url, headers=headers, timeout=15)
        search_response.raise_for_status()
        
        soup = BeautifulSoup(search_response.text, 'html.parser')
        links = soup.select('.result__url')
        urls_to_process = [link.get('href') for link in links[:num_pages] if link.get('href') and link.get('href').startswith('http')]

        if not urls_to_process:
            return None

        # OPTIMIZATION: Use a ThreadPoolExecutor to download and parse pages in parallel,
        # which is much faster than doing it sequentially.
        texts = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_pages) as executor:
            # Map the scraping function to the list of URLs
            future_to_url = {executor.submit(_scrape_single_url, url): url for url in urls_to_process}
            for future in concurrent.futures.as_completed(future_to_url):
                result = future.result()
                if result:
                    texts.append(result)
        
        combined_text = "".join(texts)
        return combined_text.strip() if combined_text else None
        
    except requests.RequestException as e:
        print(f"Error during web search phase: {str(e)}")
        return None

# ==============================================================================
# --- CORE VIEW LOGIC ---
# ==============================================================================

@csrf_exempt
def process_article(request):
    """
    Handles the main input bar. It intelligently routes requests based on input type.
    - Path 1: If input is a URL, it processes the article directly.
    - Path 2: If input is a query, it uses the LLM-first with fallback architecture.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    try:
        data = json.loads(request.body)
        input_str = data.get('query', data.get('url', '')).strip()

        if not input_str:
            return JsonResponse({'success': False, 'error': 'Please enter a query or URL.'})

        # --- LOGIC PATH 1: Input is a URL (Original Functionality) ---
        if validators.url(input_str):
            url = input_str
            # Check cache first
            if (cached_article := ArticleSummary.objects.filter(url=url).first()):
                # FIX: Manually create dictionary instead of calling a non-existent .to_dict() method.
                article_data = {
                    'title': cached_article.title,
                    'authors': cached_article.authors,
                    'publish_date': cached_article.publish_date,
                    'summary': cached_article.summary,
                    'top_image': cached_article.top_image,
                    'sentiment': cached_article.sentiment,
                    'url': cached_article.url,
                }
                return JsonResponse({'success': True, 'type': 'article', 'from_cache': True, 'data': article_data})
            
            # Process with newspaper3k if not in cache
            article = Article(url, fetch_images=False)
            article.download()
            article.parse()
            
            if not article.title or not article.text:
                return JsonResponse({'success': False, 'error': 'Could not extract readable content from the URL.'})

            # Run NLP to get the summary
            article.nlp()
            summary = article.summary

            # FIX: Fallback to custom summarizer if newspaper3k fails
            if not summary or len(summary) < 50:
                print("Newspaper3k summary was insufficient. Falling back to custom summarizer.")
                summary = " ".join(summarize(title=article.title, text=article.text, max_sents=7))

            analysis = TextBlob(article.text)
            sentiment = 'Positive 🙂' if analysis.sentiment.polarity > 0.05 else 'Negative ☹️' if analysis.sentiment.polarity < -0.05 else 'Neutral 😐'
            
            db_article = ArticleSummary(
                title=article.title,
                authors=', '.join(article.authors) if article.authors else get_website_name(url),
                publish_date=article.publish_date.strftime('%B %d, %Y') if article.publish_date else "N/A",
                summary=summary,
                top_image=article.top_image,
                sentiment=sentiment,
                url=url
            )
            db_article.save()
            
            # FIX: Manually create dictionary for the new article.
            new_article_data = {
                'title': db_article.title,
                'authors': db_article.authors,
                'publish_date': db_article.publish_date,
                'summary': db_article.summary,
                'top_image': db_article.top_image,
                'sentiment': db_article.sentiment,
                'url': db_article.url,
            }
            return JsonResponse({'success': True, 'type': 'article', 'from_cache': False, 'data': new_article_data})

        # --- LOGIC PATH 2: Input is a Standard Query (LLM-First with Fallback) ---
        else:
            query = input_str
            # Primary Method: Ask the LLM directly for a fast, intelligent answer.
            if (llm_answer := call_gemini_api(prompt=query)):
                return JsonResponse({'success': True, 'type': 'search', 'data': {'answer': llm_answer}})
            
            # Fallback Method: If LLM fails, use the original web scraping and summarization logic.
            print("LLM-first approach failed. Falling back to legacy web search summarization.")
            if (context := search_and_scrape_urls(query, num_pages=3)):
                 # Use the original summarizer on the scraped text
                 if (summary := " ".join(summarize(title=query, text=context, max_sents=7))):
                     return JsonResponse({'success': True, 'type': 'search', 'data': {'answer': summary}})

            return JsonResponse({'success': False, 'error': 'I could not find an answer for your query. Please try rephrasing or using the Globe Search.'})
        
    except Exception as e:
        print(f"CRITICAL ERROR in process_article: {e}")
        return JsonResponse({'success': False, 'error': f'An unexpected server error occurred: {str(e)}'})

@csrf_exempt
def search_with_context(request):
    """
    Handles the "Search with Globe" button. This follows the scrape-first model.
    - Step 1: Performs a DEEPER web search (top 5 pages).
    - Step 2: Consolidates all text into a rich context.
    - Step 3: Asks the LLM to answer the user's query based on that fresh context.
    - Step 4 (NEW): If LLM fails, fall back to local summarizer.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    try:
        data = json.loads(request.body)
        query = data.get('query', '').strip()
        if not query:
            return JsonResponse({'success': False, 'error': 'Search query cannot be empty.'})

        # Step 1 & 2: Deeper Web Search (5 pages) & Consolidate Information
        context_text = search_and_scrape_urls(query, num_pages=5)
        if not context_text:
            return JsonResponse({'success': False, 'error': 'I found search results, but failed to extract readable content from them.'})

        # Step 3: LLM-Powered Analysis using the scraped context
        final_answer = call_gemini_api(prompt=query, context=context_text)
        
        # Step 4: Fallback to local summarization if LLM fails
        if not final_answer:
            print("Globe search LLM call failed. Falling back to local summarization.")
            final_answer = " ".join(summarize(title=query, text=context_text, max_sents=7))
            
            # If both LLM and local summarizer fail, then return an error
            if not final_answer:
                return JsonResponse({'success': False, 'error': 'I gathered fresh information but could not generate a final answer. The AI service may be temporarily unavailable.'})

        return JsonResponse({'success': True, 'type': 'search', 'data': {'answer': final_answer}})

    except Exception as e:
        print(f"CRITICAL ERROR in search_with_context: {e}")
        return JsonResponse({'success': False, 'error': f'An unexpected server error occurred: {str(e)}'})

# ==============================================================================
# --- HISTORY AND ARTICLE MANAGEMENT (UNCHANGED) ---
# ==============================================================================

def get_history(request):
    try:
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        
        today_articles = ArticleSummary.objects.filter(created_at__date=today).order_by('-created_at')
        week_articles = ArticleSummary.objects.filter(created_at__date__lt=today, created_at__date__gte=week_ago).order_by('-created_at')
        older_articles = ArticleSummary.objects.filter(created_at__date__lt=week_ago).order_by('-created_at')
        
        def format_articles(articles, date_format):
            return [{'id': a.id, 'short_title': a.short_title, 'created_at': a.created_at.strftime(date_format)} for a in articles]

        return JsonResponse({'success': True, 'data': {
            'today': format_articles(today_articles, '%H:%M'),
            'week': format_articles(week_articles, '%b %d'),
            'older': format_articles(older_articles, '%b %d, %Y')
        }})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def get_article(request, article_id):
    try:
        article = get_object_or_404(ArticleSummary, id=article_id)
        # FIX: Manually create dictionary here as well.
        article_data = {
            'title': article.title,
            'authors': article.authors,
            'publish_date': article.publish_date,
            'summary': article.summary,
            'top_image': article.top_image,
            'sentiment': article.sentiment,
            'url': article.url,
        }
        return JsonResponse({'success': True, 'data': article_data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@csrf_exempt
def delete_article(request, article_id):
    if request.method == 'DELETE':
        try:
            article = get_object_or_404(ArticleSummary, id=article_id)
            article.delete()
            return JsonResponse({'success': True, 'message': 'Article deleted.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

# ==============================================================================
# --- ORIGINAL TEXT SUMMARIZATION LOGIC (KEPT FOR FALLBACK) ---
# ==============================================================================
stopwords = set(['i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're", "you've", "you'll", "you'd", 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', "she's", 'her', 'hers', 'herself', 'it', "it's", 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', "don't", 'should', "should've", 'now'])
ideal = 20.0

def summarize(title='', text='', max_sents=5):
    if not text or not title or max_sents <= 0: return []
    sentences = split_sentences(text)
    keys = keywords(text)
    titleWords = split_words(title)
    if not sentences or not keys or not titleWords: return []
    ranks = score(sentences, titleWords, keys).most_common(max_sents)
    # The sorted key now correctly uses summary[0] to sort by the (index, sentence) tuple
    return [summary[0][1] for summary in sorted(ranks, key=lambda summary: summary[0])]

def score(sentences, titleWords, keywords):
    senSize = len(sentences)
    ranks = Counter()
    for i, s in enumerate(sentences):
        sentence_words = split_words(s)
        if not sentence_words: continue
        titleFeature = title_score(titleWords, sentence_words)
        sentenceLength = length_score(len(sentence_words))
        sentencePosition = sentence_position(i + 1, senSize)
        sbsFeature = sbs(sentence_words, keywords)
        dbsFeature = dbs(sentence_words, keywords)
        frequency = (sbsFeature + dbsFeature) / 2.0 * 10.0
        totalScore = (titleFeature*1.5 + frequency*2.0 + sentenceLength*1.0 + sentencePosition*1.0)/4.0
        ranks[(i, s)] = totalScore
    return ranks

def sbs(words, keywords):
    score = 0.0
    if not words: return 0
    for word in words:
        if word in keywords: score += keywords[word]
    return (1.0 / math.fabs(len(words)) * score) / 10.0 if words else 0

def dbs(words, keywords):
    if not words: return 0
    summ, first, second = 0, [], []
    for i, word in enumerate(words):
        if word in keywords:
            score = keywords[word]
            if not first: first = [i, score]
            else:
                second = first
                first = [i, score]
                dif = first[0] - second[0]
                summ += (first[1] * second[1]) / (dif ** 2)
    k = len(set(keywords.keys()).intersection(set(words))) + 1
    return (1 / (k * (k + 1.0)) * summ)

def split_words(text):
    try:
        text = re.sub(r'[^\w ]', '', text)
        return [x.strip('.').lower() for x in text.split()]
    except (TypeError, AttributeError):
        return []

def keywords(text):
    text = split_words(text)
    if not text: return {}
    num_words = len(text)
    text = [x for x in text if x not in stopwords]
    freq = Counter(text)
    min_size = min(10, len(freq))
    keywords_sorted = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:min_size]
    keywords_dict = dict(keywords_sorted)
    for k in keywords_dict:
        articleScore = keywords_dict[k] * 1.0 / num_words
        keywords_dict[k] = articleScore * 1.5 + 1
    return keywords_dict

def split_sentences(text):
    try:
        sentences = nltk.sent_tokenize(text)
        return [s.replace('\n', ' ').strip() for s in sentences if len(s) > 15]
    except:
        return []

def length_score(sentence_len):
    return 1 - math.fabs(ideal - sentence_len) / ideal

def title_score(title, sentence):
    title = [x for x in title if x not in stopwords]
    if not title: return 0
    count = sum(1.0 for word in sentence if word not in stopwords and word in title)
    return count / len(title)

def sentence_position(i, size):
    normalized = i * 1.0 / size
    if 0 < normalized <= 0.1: return 0.17
    elif 0.1 < normalized <= 0.2: return 0.23
    elif 0.2 < normalized <= 0.3: return 0.14
    elif 0.3 < normalized <= 0.4: return 0.08
    elif 0.4 < normalized <= 0.5: return 0.05
    elif 0.5 < normalized <= 0.6: return 0.04
    elif 0.6 < normalized <= 0.7: return 0.06
    elif 0.7 < normalized <= 0.8: return 0.04
    elif 0.8 < normalized <= 0.9: return 0.15
    else: return 0
