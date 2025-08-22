import os
import json
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from openai import OpenAI
load_dotenv()

app = Flask(__name__)
def generate_review(code_content):
    client = OpenAI(api_key=os.getenv("perplexity_api"), base_url="https://api.perplexity.ai")
    response = client.chat.completions.create(
        model="sonar-pro",
        temperature=0.1,
        messages=[
            {
                "role" : "user",
                "content" : """You are a senior code reviewer. IMPORTANT: Respond ONLY with valid JSON.

Analyze this code and respond with this EXACT JSON structure:
{
    status: ,
    overall_score: 0,
    total_issues: 0,
    issues: [
        {
            line_number: 0,
            severity: ,
            category: ,
            title: ,
            description: ,
            suggestion: ,
            code_fix: 
        }
    ],
    positive_points: [
    ]
}

Remember to give a score out of 10 not 100
"""
            },
            {
                "role":"assistant",
                "content" : """
{
  "status": "error",
  "overall_score": 0,
  "total_issues": 1,
  "issues": [
    {
      "line_number": 0,
      "severity": "critical",
      "category": "missing_code",
      "title": "No code provided for review",
      "description": "You did not submit any code to review. Please provide the source code you would like analyzed.",
      "suggestion": "Paste your code snippet or program so that a comprehensive review can be performed.",
      "code_fix": null
    }
  ],
  "positive_points": [
  
  ]
}"""
            },
            {
                "role" : "user",
                "content" : code_content
            }
        ],
        max_tokens= 4000
    )
    return response.choices[0].message.content


def extract_json_from_response(response_text, data):
    """Extract JSON from the response text, handling markdown code blocks"""
    try:
        # Try to parse as direct JSON first
        return json.loads(response_text)
    except json.JSONDecodeError:
        # Look for JSON in markdown code blocks
        import re
        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Look for JSON without markdown
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        # If all fails, return error response
        return {
            "data":data,
            "status": "Failed to parse AI response as JSON",
            "overall_score": 0,
            "total_issues": 0,
            "issues": [],
            "positive_points": []
        }

@app.route('/review', methods=['POST'])
def review_code():
    """Main endpoint for code review"""
    try:
        data = request.get_json()
        print(data,"\n------------------------------------------")
        
        if not data:
            return jsonify({
                "status": "No JSON data provided"
            }), 400

        code_content = data.get('code', '')
        file_path = data.get('file_path', 'unknown')
        pr_number = data.get('pr_number', 'unknown')

        if not code_content:
            return jsonify({
                "status": "No code content provided",
                "overall_score": 0,
                "total_issues": 0,
                "issues": [],
                "positive_points": []
            }), 400

        app.logger.info(f"Reviewing file: {file_path} for PR: {pr_number}")

        # Generate review using AI
        raw_response = generate_review(f"File Path : {file_path}\nCode:\n{code_content}")
        # print(code_content)
        app.logger.info(f"Raw AI response: {raw_response}")
        
        print(f"{raw_response}\n\n{type(raw_response)}") # checking if ther is a problem in raw_response

        # Extract JSON from response
        review_data = extract_json_from_response(raw_response, data)
        
        # Ensure all required fields exist
        review_data.setdefault('status', 'Review completed')
        review_data.setdefault('overall_score', 0)
        review_data.setdefault('total_issues', 0)
        review_data.setdefault('issues', [])
        review_data.setdefault('positive_points', [])

        return jsonify(review_data)

    except Exception as e:
        app.logger.error(f"Error in review endpoint: {str(e)}")
        return jsonify({
            "status": f"Internal server error: {str(e)}",
            "overall_score": 0,
            "total_issues": 0,
            "issues": [],
            "positive_points": []
        }), 500

@app.route('/', methods=['GET'])
def home():
    """Home endpoint"""
    return render_template("index.html")


if __name__ == "__main__":
    if not os.getenv("gemini_api"):
        print("Warning: gemini_api environment variable not found")
    
    app.run(host='0.0.0.0', port=8080)