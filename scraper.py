import os
import requests
import json
import smtplib
import ssl
from bs4 import BeautifulSoup

#pushbullet set up
def send_pushbullet_message(message):
    print("Sending Pushbullet notification...")
    token = os.environ.get("PUSHBULLET_TOKEN")
    if not token:
        print("Pushbullet token not set")
        return
    data={
        "type":"note",
        "title":"New Flat Posted",
        "body": message
    }
    response = requests.post(
        "https://api.pushbullet.com/v2/pushes",
        json=data,
        headers={"Access-Token":token}
    )
    if response.status_code != 200:
        print("Failed to send Pushbullet notification")
    else:
        print("Pushbullet notification sent!")

#email notification 
def send_email_notifications(message):
    email_address = os.environ.get ("EMAIL_ADDRESS")
    email_password = os.environ.get ("EMAIL_PASSWORD")
    email_recipient = os.environ.get ("EMAIL_RECIPIENT")

    if not all ([email_address, email_password, email_recipient]):
        print ("Email environment variables not set")
        return
    
    subject = "New flat available"
    email_text = f"Subject: {subject}\n\n{message}"

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(email_address, email_password)
            server.sendmail(email_address, email_recipient, email_text)
        print ("Email sent succesfully!")
    except Exception as e:
        print (f" Failed to send email: {e}")

#the url of the website 
URL = "https://domus.ed.ac.uk/properties/?wpp_search%5Bsort_order%5D=ASC&wpp_search%5Bsort_by%5D=price&wpp_search%5Bpagination%5D=on&wpp_search%5Bper_page%5D=10&wpp_search%5Bstrict_search%5D=false&wpp_search%5Bproperty_type%5D=long_term_let&wpp_search%5Bsuitability%5D=-1&wpp_search%5Bproperty_address%5D=&wpp_search%5Bneighbourhood%5D=-1&wpp_search%5Bbedrooms%5D=-1&wpp_search%5Brental_price%5D%5Bmin%5D=&wpp_search%5Brental_price%5D%5Bmax%5D=&wpp_search%5Bavailability_date%5D%5Bfrom%5D=&wpp_search%5Bavailability_date%5D%5Bto%5D="

def get_post_links():
    response = requests.get(URL)
    soup = BeautifulSoup(response.text, 'html.parser')
    listings = soup.find_all('div', class_="property-overview-wrapper")
    #using title + URL as unique identifier
    posts= []
    for listing in listings:
        title_tag = listing.find('h2', class_='property-title')
        link_tag = title_tag.find('a') if title_tag else None
        if title_tag and link_tag:
            title = link_tag.find('h3').text.strip()
            link = link_tag ['href']
            full_link = f"https://domus.ed.ac.uk{link}"
            posts.append(f"{title} - {full_link}")
    return posts

def load_previous_posts():
    if os.path.exists('data.json'):
        with open('data.json','r') as f:
            return json.load(f)
    return []

def save_posts(posts):
    with open('data.json','w') as f:
        json.dump(posts, f)

def main():
    print("Running scrapper...")  # log start
    current_posts = get_post_links()
    print(f"Found {len(current_posts)} posts.")  # how many posts
    #print the extracted posts
    print("current posts extracted:")
    for post in current_posts:
        print(post)
        
    previous_posts = load_previous_posts()
    new_posts = [post for post in current_posts if post not in previous_posts]

    if new_posts:
        print(f"Sending notifications for {len(new_posts)} new posts...")
        for post in new_posts:
            for i in range(5):
                send_pushbullet_message(post)
                send_email_notifications(post)
    else:
        print("No new posts found.")

    save_posts(current_posts)  # saving posts to ensure data.json is created
    print(f"Saved {len(current_posts)} post(s) to data.json.")

if __name__ == "__main__":
    main()
