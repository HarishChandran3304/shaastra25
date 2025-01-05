import requests
from bs4 import BeautifulSoup
from googlesearch import search
import os
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


def generate_esg_queries(input_text):
    """
    Generate ESG-related search queries using OpenAI's GPT model.

    Args:
        input_text (str): Input text describing the business or context.

    Returns:
        list: A list of 5 ESG-focused search queries.
    """
    prompt = f"""
    You are an AI assistant specializing in Environmental, Social, and Governance (ESG) analysis.
    Based on the following text, generate 5 concise search queries to gather relevant ESG information:

    Text: {input_text}

    Each query should focus on extracting ESG data, such as projects, environmental policies, social initiatives, or governance metrics.
    """

    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=150,
            n=1,
            stop=None
        )
        queries = response.choices[0].text.strip().split("\n")
        return [query.strip() for query in queries if query.strip()]
    except Exception as e:
        print(f"Error generating queries: {e}")
        return []


def scrape_website_content(url):
    """
    Scrapes text content from the given URL.

    Args:
        url (str): The URL to scrape.

    Returns:
        str: The scraped text content, or an error message if scraping fails.
    """
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        paragraphs = soup.find_all("p")
        content = "\n".join(p.get_text(strip=True) for p in paragraphs)
        return content
    except Exception as e:
        return f"Failed to scrape {url}: {e}"


def search_and_scrape_esg_data(query, num_results=5):
    """
    Searches for a query online and scrapes text content from the top results.

    Args:
        query (str): The search query.
        num_results (int): Number of search results to scrape.

    Returns:
        dict: A dictionary with URLs as keys and their scraped content as values.
    """
    results = {}
    print(f"Searching for: {query}")
    try:
        for url in search(query, num_results=num_results, lang="en"):
            print(f"Scraping: {url}")
            content = scrape_website_content(url)
            results[url] = content
    except Exception as e:
        print(f"Error during search: {e}")
    return results


def main():
    """
    Main function to perform ESG data scraping.
    """
    # Example input text for ESG analysis
    input_text = input("Enter a description of the business or context for ESG analysis: ")

    # Generate ESG-focused search queries
    queries = generate_esg_queries(input_text)

    if not queries:
        print("Failed to generate queries.")
        return

    all_data = {}

    # Search and scrape data for each query
    for query in queries:
        scraped_data = search_and_scrape_esg_data(query)
        all_data.update(scraped_data)

    # Display the scraped data
    for url, content in all_data.items():
        print(f"\nURL: {url}\nContent:\n{content[:500]}...\n")  # Truncate content for readability


if __name__ == "__main__":
    main()
