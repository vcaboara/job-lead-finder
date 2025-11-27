import httpx
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse


def find_apply_link(html_content: str, base_url: str):
    """
    Parses HTML to find a likely "Apply" link.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    # Regex to find links with "apply", "submit", etc.
    apply_pattern = re.compile(r"apply|submit", re.IGNORECASE)

    # Find all <a> tags with a href attribute
    links = soup.find_all("a", href=True)

    for link in links:
        # Check link text or attributes for the pattern
        if apply_pattern.search(link.text):
            href = link.get("href")
            # Convert relative URL to absolute
            return urljoin(base_url, href)

    return None


def validate_job_link(url: str, max_depth: int = 2) -> bool:
    """
    Validates a job posting link by trying to find and follow the "Apply" link.

    Args:
        url: The initial URL of the job posting.
        max_depth: How many "Apply" links to follow (default is 2).

    Returns:
        True if the final link is valid (not a 404), False otherwise.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    current_url = url

    try:
        with httpx.Client(follow_redirects=True, headers=headers, timeout=15.0) as client:
            for depth in range(max_depth + 1):
                print(f"Checking URL (depth {depth}): {current_url}")
                response = client.get(current_url)

                # Check for client or server errors on the final check
                if depth == max_depth:
                    response.raise_for_status()
                    print(f"Final URL is valid: {current_url}")
                    return True

                # For intermediate pages, check status and find next link
                response.raise_for_status()

                # If we are not at max depth, find the next link
                next_link = find_apply_link(response.text, str(response.url))

                if not next_link:
                    # If no "apply" link is found, assume the current page is the application page
                    # and consider it valid if it didn't raise an error.
                    print(f"No further 'apply' link found. Assuming {current_url} is valid.")
                    return True

                current_url = next_link

    except httpx.HTTPStatusError as e:
        print(f"HTTP Error validating link {e.request.url}: Status {e.response.status_code}")
        return False
    except httpx.RequestError as e:
        print(f"Request Error validating link {e.request.url}: {e}")
        return False

    return False # Should not be reached if max_depth is handled correctly
