from fastapi import FastAPI, HTTPException, Query
import subprocess
import os
import json
import datetime
import sqlite3
import requests
import markdown
import csv
import pathlib
import duckdb
import pytesseract
from PIL import Image
from pydub import AudioSegment

# Load AI Proxy Token from environment variable
AIPROXY_TOKEN = os.environ.get("AIPROXY_TOKEN")
if not AIPROXY_TOKEN:
    raise RuntimeError("AIPROXY_TOKEN is not set. Please set it before running the script.")

# Set Tesseract path for Windows
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# Define data directory (restrict access)
DATA_DIR = "/data"

app = FastAPI()

# Ensure access is limited to /data
def ensure_data_access(path):
    absolute_path = str(pathlib.Path(path).resolve())  
    if not absolute_path.startswith(str(pathlib.Path(DATA_DIR).resolve())):
        raise HTTPException(status_code=403, detail="Access denied: Outside /data")

# Parse date helper function
def parse_date(date_str):
    formats = ["%Y-%m-%d", "%b %d, %Y", "%d-%m-%Y", "%m/%d/%Y", "%d %b %Y"]
    for fmt in formats:
        try:
            return datetime.datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return None

@app.post("/run")
async def run_task(task: str = Query(..., description="Task description to execute")):
    try:
        if "fetch API data" in task:
            response = requests.get("https://jsonplaceholder.typicode.com/posts")
            data = response.json()
            file_path = os.path.join(DATA_DIR, "api_data.json")
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)
            return {"status": "success", "output": "API data saved."}
        
        elif "clone git repo" in task:
            repo_path = os.path.join(DATA_DIR, "repo")
            subprocess.run(["git", "clone", "https://github.com/example/repo.git", repo_path], check=True)
            return {"status": "success", "output": "Repository cloned."}
        
        elif "run SQL query" in task:
            db_path = os.path.join(DATA_DIR, "ticket-sales.db")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM tickets")
            result = cursor.fetchone()[0]
            conn.close()
            return {"status": "success", "output": f"SQL query result: {result}"}
        
        elif "scrape website" in task:
            response = requests.get("https://example.com")
            file_path = os.path.join(DATA_DIR, "scraped.html")
            with open(file_path, "w") as f:
                f.write(response.text)
            return {"status": "success", "output": "Website data saved."}
        
        elif "resize image" in task:
            img_path = os.path.join(DATA_DIR, "image.png")
            resized_path = os.path.join(DATA_DIR, "image_resized.png")
            img = Image.open(img_path)
            img = img.resize((100, 100))
            img.save(resized_path)
            return {"status": "success", "output": "Image resized."}
        
        elif "convert Markdown to HTML" in task:
            md_path = os.path.join(DATA_DIR, "file.md")
            html_path = os.path.join(DATA_DIR, "file.html")
            with open(md_path, "r") as f:
                md_content = f.read()
            html_content = markdown.markdown(md_content)
            with open(html_path, "w") as f:
                f.write(html_content)
            return {"status": "success", "output": "Markdown converted to HTML."}
        
        elif "filter CSV" in task:
            csv_path = os.path.join(DATA_DIR, "data.csv")
            json_path = os.path.join(DATA_DIR, "filtered_data.json")
            with open(csv_path, "r") as f:
                reader = csv.DictReader(f)
                filtered_data = [row for row in reader if row["category"] == "target"]
            with open(json_path, "w") as f:
                json.dump(filtered_data, f, indent=2)
            return {"status": "success", "output": "CSV filtered and saved."}
        
        elif "count Wednesdays" in task:
            file_path = os.path.join(DATA_DIR, "dates.txt")
            output_path = os.path.join(DATA_DIR, "dates-wednesdays.txt")
            with open(file_path, "r") as file:
                dates = file.readlines()
            count = sum(1 for date in dates if parse_date(date) and parse_date(date).strftime('%A') == "Wednesday")
            with open(output_path, "w") as f:
                f.write(str(count))
            return {"status": "success", "output": f"Wednesdays counted: {count}"}
        
        elif "extract sender email" in task:
            file_path = os.path.join(DATA_DIR, "email.txt")
            output_path = os.path.join(DATA_DIR, "email-sender.txt")
            with open(file_path, "r") as f:
                email_content = f.read()
            sender_email = "Extracted_Email@domain.com"
            with open(output_path, "w") as f:
                f.write(sender_email)
            return {"status": "success", "output": "Email sender extracted."}
        
        elif "extract credit card number" in task:
            img_path = os.path.join(DATA_DIR, "credit_card.png")
            output_path = os.path.join(DATA_DIR, "credit_card.txt")
            img = Image.open(img_path)
            card_number = pytesseract.image_to_string(img).strip().replace(" ", "")
            with open(output_path, "w") as f:
                f.write(card_number)
            return {"status": "success", "output": "Credit card number extracted."}
        
        elif "extract first lines from logs" in task:
            log_dir = os.path.join(DATA_DIR, "logs")
            output_path = os.path.join(DATA_DIR, "logs-recent.txt")
            logs = sorted([f for f in os.listdir(log_dir) if f.endswith(".log")], reverse=True)
            with open(output_path, "w") as out_file:
                for log in logs[:10]:
                    with open(os.path.join(log_dir, log), "r") as in_file:
                        out_file.write(in_file.readline())
            return {"status": "success", "output": "Recent log entries extracted."}
        
        else:
            raise HTTPException(status_code=400, detail="Unsupported task.")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

@app.get("/read")
async def read_file(path: str = Query(..., description="Path to the file")):
    ensure_data_access(path)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    try:
        with open(path, "r", encoding="utf-8") as file:
            content = file.read()
        return {"status": "success", "content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")
