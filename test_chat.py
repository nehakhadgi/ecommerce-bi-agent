import os
from dotenv import load_dotenv
from google import genai

# Load your API key from the .env file
load_dotenv()

# Create a Gemini client
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# Send a business question to Gemini
response = client.models.generate_content(
    model="gemini-3.6-flash",
       contents="What were the top selling products in my store last quarter?"
)

# Print the response
print(response.text)