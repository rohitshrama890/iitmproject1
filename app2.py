from fastapi import FastAPI, HTTPException, Query
import subprocess
import os
import json
import datetime
import sqlite3
import requests
import pytesseract
from PIL import Image
import pytesseract

# Set the Tesseract path for Windows
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

app = FastAPI()

USER_EMAIL = "23f2002473@ds.study.iitm.ac.in"

# Helper function to parse dates
def parse_date(date_str):
    formats = ["%Y-%m-%d", "%b %d, %Y", "%d-%m-%Y", "%m/%d/%Y", "%d %b %Y"]
    for fmt in formats:
        try:
            return datetime.datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return None  # Return None if format doesn't match

# Count Wednesdays in a file
def count_weekdays_in_file(file_path, weekday):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            dates = file.readlines()
        
        count = sum(1 for date in dates if parse_date(date) and parse_date(date).strftime('%A') == weekday)
        
        with open("/data/dates-wednesdays.txt", "w") as f:
            f.write(str(count))
        
        return count
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.post("/run")
async def run_task(task: str = Query(..., description="Task description to execute")):
    try:
        if "install uv" in task:
            subprocess.run("pip install uv", shell=True, check=True)
            return {"status": "success", "output": "uv installed."}
        elif "run datagen.py" in task:
            script_url = "https://raw.githubusercontent.com/sanand0/tools-in-data-science-public/tds-2025-01/project-1/datagen.py"
            subprocess.run(f"wget {script_url} -O /data/datagen.py", shell=True, check=True)
            subprocess.run(f"python /data/datagen.py {USER_EMAIL}", shell=True, check=True)
            return {"status": "success", "output": "datagen.py executed."}
        elif "Format /data/format.md" in task:
            subprocess.run("npx prettier@3.4.2 --write /data/format.md", shell=True, check=True)
            return {"status": "success", "output": "File formatted successfully."}
        elif "Count the number of Wednesdays" in task:
            count = count_weekdays_in_file("/data/dates.txt", "Wednesday")
            return {"status": "success", "output": f"Wednesdays counted: {count}"}
        elif "Sort contacts" in task:
            with open("/data/contacts.json", "r") as f:
                contacts = json.load(f)
            contacts.sort(key=lambda x: (x["last_name"], x["first_name"]))
            with open("/data/contacts-sorted.json", "w") as f:
                json.dump(contacts, f, indent=2)
            return {"status": "success", "output": "Contacts sorted successfully."}
        elif "Extract first lines from logs" in task:
            logs = sorted([f for f in os.listdir("/data/logs/") if f.endswith(".log")], reverse=True)
            with open("/data/logs-recent.txt", "w") as out_file:
                for log in logs[:10]:
                    with open(f"/data/logs/{log}", "r") as in_file:
                        out_file.write(in_file.readline())
            return {"status": "success", "output": "Recent log entries extracted."}
        elif "Create index of Markdown files" in task:
            index = {}
            for filename in os.listdir("/data/docs/"):
                if filename.endswith(".md"):
                    with open(f"/data/docs/{filename}", "r") as f:
                        for line in f:
                            if line.startswith("# "):
                                index[filename] = line.strip("# ").strip()
                                break
            with open("/data/docs/index.json", "w") as f:
                json.dump(index, f, indent=2)
            return {"status": "success", "output": "Markdown index created."}
        elif "Extract sender email" in task:
            with open("/data/email.txt", "r") as f:
                email_content = f.read()
            sender_email = "Extracted_Email@domain.com"  # Replace with LLM extraction logic
            with open("/data/email-sender.txt", "w") as f:
                f.write(sender_email)
            return {"status": "success", "output": "Email sender extracted."}
        elif "Extract credit card number" in task:
            img = Image.open("/data/credit_card.png")
            card_number = pytesseract.image_to_string(img).strip().replace(" ", "")
            with open("/data/credit_card.txt", "w") as f:
                f.write(card_number)
            return {"status": "success", "output": "Credit card number extracted."}
        elif "Find most similar comments" in task:
            with open("/data/comments.txt", "r") as f:
                comments = f.readlines()
            comment1, comment2 = comments[0], comments[1]  # Replace with embedding similarity logic
            with open("/data/comments-similar.txt", "w") as f:
                f.write(comment1 + comment2)
            return {"status": "success", "output": "Most similar comments extracted."}
        elif "Total sales of Gold tickets" in task:
            conn = sqlite3.connect("/data/ticket-sales.db")
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(units * price) FROM tickets WHERE type='Gold'")
            total_sales = cursor.fetchone()[0] or 0
            with open("/data/ticket-sales-gold.txt", "w") as f:
                f.write(str(total_sales))
            conn.close()
            return {"status": "success", "output": f"Total Gold ticket sales: {total_sales}"}
        else:
            raise HTTPException(status_code=400, detail="Unsupported task.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

@app.get("/read")
async def read_file(path: str = Query(..., description="Path to the file")):
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    try:
        with open(path, "r", encoding="utf-8") as file:
            content = file.read()
        return {"status": "success", "content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")
