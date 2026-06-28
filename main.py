from dotenv import load_dotenv
import os
load_dotenv()
print("stormcaller setup is working")
print("Apify token loaded:", bool(os.getenv("APIFY_TOKEN")))
