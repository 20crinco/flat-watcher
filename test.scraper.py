import os
import requests
import json
import smtplib
import ssl
from bs4 import BeautifulSoup

# Pushbullet notification setup
def send_pushbullet_message(message):
    print("Sending Pushbullet notification...")
    token = os.environ.get("PUSHBULLET_TOKEN")
    if not token:
        print("Pushbullet token not set")
        return
    data = {
        "type": "note",
        "title": "New Flat Posted",
        "body": message
    }
    try:
        response = requests.post(
            "https://api.pushbullet.com/v2/pushes",
            json=data,
            headers={"Access-Token": token}
        )
        if response.status_code != 200:
            print(f"Failed to send Pushbullet notification: {response.text}")
        else:
            print("Pushbullet notification sent!")
    except Exception as e:
        print(f"Pushbullet error: {e}")

# Email notification setup
def send_email_notifications(message):
    email_address = os.environ.get("EMAIL_ADDRESS")
    email_password = os.environ.get("EMAIL_PASSWORD")
    email_recipient = os.environ.get("EMAIL_RECIPIENT")

    if not all([email_address, email_password, email_recipient]):
        print("Email environment variables not set")
        return

    subject = "New flat available"
    email_text = f"Subject: {subject}\n\n{message}"

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(email_address, email_password)
            server.sendmail(email_address, email_recipient, email_text)
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

# Scraper URL
URL = "https://domus.ed.ac.uk/properties/?wpp_search%5Bsort_order%5D=ASC&wpp_search%5Bsort_by%5D=price&wpp_search%5Bpagination%5D=on&wpp_search%5Bper_page%5D=10&wpp_search%5Bstrict_search%5D=false&wpp_search%5Bproperty_type%5D=long_term_let"

# Scrape post links
def get_post_links():
    try:
        response = requests.get(URL)
        soup = BeautifulSoup(response.text, 'html.parser')

        listings = soup.find_all('div', class_='property-overview-wrapper')
        print(f"Found {len(listings)} listings on page.")

        posts = []
        for listing in listings:
            link_tag = listing.find('a', class_='property-title-link')
            if link_tag:
                title = link_tag.find('h3').text.strip() if link_tag.find('h3') else 'No Title'
                link = link_tag['href']
                full_link = f"https://domus.ed.ac.uk{link}"
                posts.append(f"{title} - {full_link}")
        return posts
    except Exception as e:
        print(f"Error fetching posts: {e}")
        return []

# Load previous posts
def load_previous_posts():
    try:
        if os.path.exists('data.json'):
            with open('data.json', 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading data.json: {e}")
    return []

# Save current posts
def save_posts(posts):
    try:
        with open('data.json', 'w') as f:
            json.dump(posts, f)
        print(f"Saved {len(posts)} posts to data.json.")
    except Exception as e:
        print(f"Error saving posts: {e}")

# Main runner
def main():
    print("Running scraper...")

    current_posts = get_post_links()
    print(f"Found {len(current_posts)} posts.")

    previous_posts = load_previous_posts()
    new_posts = [post for post in current_posts if post not in previous_posts]

    test_mode = os.environ.get("TEST_MODE", "false").lower() == "true"

    if test_mode:
        print("TEST MODE enabled — sending test messages only.")
        send_pushbullet_message("TEST: This is a test Pushbullet notification from GitHub Actions")
        send_email_notifications("TEST: This is a test email from GitHub Actions")
    elif new_posts:
        print(f"Sending notifications for {len(new_posts)} new posts...")
        for post in new_posts:
            send_pushbullet_message(post)
            send_email_notifications(post)
    else:
        print("No new posts found.")

    save_posts(current_posts)

if __name__ == "__main__":
    main()