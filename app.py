from flask import Flask, request , render_template, render_template_string
from groq import Groq
from dotenv import load_dotenv
import pandas as pd
import os
import json

#Create Flask App
app = Flask(__name__)

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

#HTML Form
HTML_form= """"
<!DOCTYPE html>
<html>
<head>
    <title>Mrunmayee Naik- Call Transcript Analyzer </title>
</head>
<body style = "font-family : Arial, sans-serif; margin: 40px;">
    <h2>Customer Call Transcript Analyzer </h2>
    <form method ="post" action ="/analyze">
        <textarea name ="transcript" rows="6" cols="70" placeholder="Paste transcript here..."></textarea><br><br>
        <input type="submit" value="Analyze">
    </form> 
</body>
</html>   
"""

#HOMEPAGE Router
@app.route("/",methods=["GET"])
def home():
    return render_template_string(HTML_form)

# ANALYZE Router
@app.route("/analyze", methods=["POST"])
def analyze():
    transcript = request.form.get("transcript")

    if not transcript:
        return jsonify({"error":"No transcript provided"}),400

    #Build Prompt for Groq AI
    messages=[
        {
            "role":"system",
            "content": (
                "You are an assistant that summarizes customer call transcript"
                "Always respond ONLY in valid JSON format like this: "
                '{"summary": "...", "sentiment": "..."} . '
                "Do not add extra text or explanation."
            )
        },
        {
            "role": "user",
            "content": f"Transcript: {transcript}\n\n"
                       "Summarize in 2–3 sentences. "
                       "Extract sentiment (Positive, Neutral, Negative)."
        }
    ]

    #Call Groq AI
    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
    )

    result_text = completion.choices[0].message.content.strip()

    #Parse AI Response JSON
    try:
        result = json.loads(result_text)
    except json.JSONDecodeError:
        # If Groq returns text around JSON, try extracting JSON part
        if "{" in result_text and "}" in result_text:
            possible_json = result_text[result_text.find("{"): result_text.rfind("}")+1]
            try:
                result = json.loads(possible_json)
            except:
                result = {"summary": "Parsing failed", "sentiment": "Unknown"}
        else:
            result = {"summary": "Parsing failed", "sentiment": "Unknown"}

    summary = result.get("summary", "Parsing failed")
    sentiment = result.get("sentiment", "Unknown")
    
    # Saving to CSV
    csv_file = "call_analysis.csv"
    new_row = {"Transcript":transcript, "Summary":summary, "Sentiment":sentiment}

    if os.path.exists(csv_file):
        df = pd.read_csv(csv_file)
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    else:
        df = pd.DataFrame([new_row])
    
    df.to_csv(csv_file,index=False)

    #Return result as JSON
    return render_template(
       "result.html",
        transcript=transcript,
        summary=summary,
        sentiment=sentiment,
    )


#Run Flask App
if __name__ == "__main__":
    app.run(debug=True)





