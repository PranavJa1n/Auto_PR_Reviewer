import os
import json
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from google import genai
from google.genai import types
import time

load_dotenv()

app = Flask(__name__)

def generate_review(code_content, max_retries=3, delay=2):
    """Generate AI review for the provided code content with retry logic"""
    
    for attempt in range(max_retries):
        try:
            client = genai.Client(
                api_key=os.getenv("gemini_api"),
            )

            model = "gemini-2.5-pro"
            contents = [
                types.Content(
                    role="user",
                    parts=[
                    types.Part.from_text(text="""You are a senior code reviewer. IMPORTANT: Respond ONLY with valid JSON.

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
"""),
            ],
        ),
        types.Content(
            role="model",
            parts=[
                types.Part.from_text(text="""**Assessing the Request**

Okay, so I now understand the user wants me to be a senior code reviewer, but needs to first provide the code. I am waiting for the code. Once it arrives, I plan to analyze it across multiple categories like performance, security, and readability.


**Planning the Review Process**

I've solidified my plan to perform a code review. The user's prompt outlines my role and the desired output. I'm waiting for the code now. Upon receipt, I'll dive into analysis, categorizing issues by severity and crafting detailed feedback with actionable suggestions. I'll also highlight any positive aspects before compiling the JSON response.


**Revising Response Strategy**

I've carefully re-read the instructions and identified a potential contradiction: the demand for *only* JSON while lacking the required input code. My options are to return empty JSON, violate the JSON-only rule by requesting code, or generate a JSON with an error message. I'm leaning toward the third option – a JSON structure populated with an error status – to satisfy both the format constraint and the need for communication. This seems the most robust approach to address the current situation. I'm now drafting a preliminary JSON structure that reflects this approach.


**Crafting a Response**

I'm now generating a valid JSON response. It will communicate the necessity of the code for the code review. The format will adhere to user instructions, including an error state with an appropriate explanation. My aim is to be both helpful and compliant. I'm focusing on providing the user with an actionable message. The structure includes an error issue, indicating a requirement for code input.


**Addressing the Code Deficiency**

I've crafted a strategy to address the absence of code. My primary objective is to generate the requested JSON response. Given the \"JSON only\" constraint, I've decided to create an error state JSON response. This response acknowledges the missing code, communicates the issue, and provides a clear suggestion to the user. I've designed the JSON structure, which will include an error status, a \"critical\" issue detailing the situation, and guidance for proceeding. I believe this balanced response satisfies both the format requirement and the interactional necessity. The current structure is ready.


**Addressing the Input Deficiency**

I've decided to respond with the error JSON. My current plan is to generate a JSON response indicating the missing code. I will include a detailed explanation and suggestion within the JSON structure. This structured approach directly addresses the user's initial request while acknowledging the necessary input. The finalized JSON structure will contain an \"error\" status, a critical issue specifying the issue, and guidance to the user, balancing compliance and effective interaction. The response is ready to be delivered.


**Preparing the Error Response**

I'm now fully committed to the error JSON approach. It's the most compliant and informative solution. I've finalized the structure, including the error status, a descriptive issue, and a clear suggestion for the user. I'm ready to craft the precise JSON response.


"""),
                types.Part.from_text(text="""```json
{
  \"status\": \"AWAITING_CODE\",
  \"overall_score\": \"0\",
  \"total_issues\": 1,
  \"issues\": [
    {
      \"line_number\": 0,
      \"severity\": \"Info\",
      \"category\": \"Input\",
      \"title\": \"No Code Provided for Review\",
      \"description\": \"You have instructed me to analyze code, but no code was provided in the prompt. Please provide the code you would like me to review.\",
      \"suggestion\": \"Please provide the code snippet in your next message so I can perform the analysis and generate the requested JSON response.\",
      \"code_fix\": \"\"
    }
  ],
  \"positive_points\": []
}```"""),
                    ],
                ),
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=code_content),
                    ],
                ),
            ]
            
            tools = [
                types.Tool(googleSearch=types.GoogleSearch()),
            ]
            
            generate_content_config = types.GenerateContentConfig(
                temperature=0,
                thinking_config=types.ThinkingConfig(
                    thinking_budget=-1,
                ),
                tools=tools,
            )

            # Collect the full response
            response_text = ""
            for chunk in client.models.generate_content_stream(
                model=model,
                contents=contents,
                config=generate_content_config,
            ):
                response_text += chunk.text

            # If we get here, the API call was successful
            app.logger.info(f"API call successful on attempt {attempt + 1}")
            return response_text

        except Exception as e:
            app.logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
            
            if attempt == max_retries - 1:  # Last attempt
                app.logger.error(f"All {max_retries} attempts failed. Last error: {str(e)}")
                return json.dumps({
                    "status": f"Error after {max_retries} attempts: {str(e)}",
                    "overall_score": 0,
                    "total_issues": 0,
                    "issues": [],
                    "positive_points": []
                })
            
            # Wait before retrying (exponential backoff)
            wait_time = delay * (2 ** attempt)
            app.logger.info(f"Waiting {wait_time} seconds before retry...")
            time.sleep(wait_time)
    
    # This should never be reached, but just in case
    return json.dumps({
        "status": "Unexpected error in retry logic",
        "overall_score": 0,
        "total_issues": 0,
        "issues": [],
        "positive_points": []
    })



def extract_json_from_response(response_text):
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
        print(data)
        
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
        raw_response = generate_review(code_content)
        print(raw_response)
        app.logger.info(f"Raw AI response: {raw_response}")
        
        print(raw_response) # checking if ther is a problem in raw_response

        # Extract JSON from response
        review_data = extract_json_from_response(raw_response)
        
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