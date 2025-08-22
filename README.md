# AI Code Review Bot Documentation

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Architecture](#architecture)
4. [Quick Start (Recommended)](#quick-start-recommended)
5. [Self-Hosting Setup (Advanced)](#self-hosting-setup-advanced)
6. [Configuration](#configuration)
7. [Usage](#usage)
8. [API Reference](#api-reference)
9. [Troubleshooting](#troubleshooting)

## Overview

The AI Code Review Bot is an automated code analysis tool that integrates with GitHub Actions to provide intelligent code reviews for pull requests. It leverages advanced AI models to analyze code for bugs, security vulnerabilities, performance issues, and code quality improvements.

### Key Benefits

- **Automated Reviews**: Instantly review code changes without manual intervention
- **Consistent Quality**: Apply consistent coding standards across your team
- **Early Bug Detection**: Catch issues before they reach production
- **Security Scanning**: Identify potential security vulnerabilities
- **Performance Optimization**: Detect performance bottlenecks and suggest improvements

## Features

### ✨ Core Features

- **AI-Powered Analysis**: Uses advanced LLM models for intelligent code review
- **GitHub Integration**: Seamless integration with GitHub Actions workflow
- **Multi-Language Support**: Supports 20+ programming languages
- **Security Scanning**: Identifies XSS, SQL injection, and other vulnerabilities
- **Performance Analysis**: Detects memory leaks and inefficient algorithms
- **Detailed Reports**: Line-specific feedback with severity levels
- **Positive Recognition**: Highlights well-written code sections

### 🔍 Analysis Categories

- **Bugs & Logic Errors**
- **Security Vulnerabilities**
- **Performance Issues**
- **Code Style & Best Practices**
- **Maintainability Concerns**
- **Documentation Issues**

## Architecture

``` bash
[GitHub PR] → [GitHub Actions] → [AI Review Bot API] → [Perplexity AI] → [Review Comments]
```

## Quick Start (Recommended)

**⭐ This is the easiest and recommended way to get started!**

Simply use our hosted API endpoint without any setup or maintenance. Just add the GitHub Action to your repository and you're ready to go.

### Step 1: Create GitHub Action Workflow

Create `.github/workflows/code-review.yaml` in your repository:

```yaml
name: AI Code Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: write
  issues: write

jobs:
  ai-review:
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Fetch base branch
        run: git fetch origin ${{ github.event.pull_request.base.ref }}

      - name: Find changed source files
        id: changed-files
        run: |
          FILES=$(git diff --name-only origin/${{ github.event.pull_request.base.ref }} ${{ github.sha }} | grep -E '\.(ex|groovy|bf|clj|py|js|ts|java|cpp|c|cs|sql|r|bash|go|rs|php|rb|swift|pl|vb|dart|scala|bhai)$' || true)
          FILES_JSON=$(echo "$FILES" | jq -R -s -c 'split("\n") | map(select(length > 0))')
          echo "files=$FILES_JSON" >> $GITHUB_OUTPUT

      - name: Review changed files with AI
        if: ${{ steps.changed-files.outputs.files != '[]' }}
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          set -e
          for file in $(echo '${{ steps.changed-files.outputs.files }}' | jq -r '.[]'); do
            CODE_CONTENT=$(jq -Rs . < "$file")
            PR_NUMBER="${{ github.event.pull_request.number }}"

            RESPONSE=$(curl -s -X POST https://auto-pr-reviewer.onrender.com/review \
              -H "Content-Type: application/json" \
              -d "{\"code\": $CODE_CONTENT, \"file_path\": \"$file\", \"pr_number\": \"$PR_NUMBER\"}")

            if ! echo "$RESPONSE" | jq empty >/dev/null 2>&1; then
              continue
            fi

            OVERALL_SCORE=$(echo "$RESPONSE" | jq -r '.overall_score // "N/A"')
            STATUS=$(echo "$RESPONSE" | jq -r '.status // "N/A"')
            TOTAL_ISSUES=$(echo "$RESPONSE" | jq -r '.total_issues // "0"')
            ISSUES_BLOCK=$(echo "$RESPONSE" | jq '.issues // []')
            POSITIVE_POINTS_BLOCK=$(echo "$RESPONSE" | jq '.positive_points // []')

            REVIEW_COMMENT="**File:** $file"$'\n'
            REVIEW_COMMENT+="Overall Score : $OVERALL_SCORE"$'\n'
            REVIEW_COMMENT+="Status : $STATUS"$'\n'
            REVIEW_COMMENT+="Total issues : $TOTAL_ISSUES"$'\n'
            REVIEW_COMMENT+="Issues :"$'\n'
            REVIEW_COMMENT+="$ISSUES_BLOCK"$'\n'
            REVIEW_COMMENT+="Positive points :"$'\n'
            REVIEW_COMMENT+="$POSITIVE_POINTS_BLOCK"

            curl -s -X POST \
              -H "Authorization: token $GITHUB_TOKEN" \
              -H "Content-Type: application/json" \
              "https://api.github.com/repos/${{ github.repository }}/issues/$PR_NUMBER/comments" \
              -d "{\"body\": $(echo "$REVIEW_COMMENT" | jq -Rs .)}" \
              >/dev/null 2>&1 || true
          done
```

### Step 2: Commit and Test

1. Commit the workflow file to your repository
2. Create a pull request with some code changes
3. Watch the AI review bot automatically analyze your code!

### Benefits of Using the Hosted Endpoint

✅ **No setup required** - Just add the workflow and go  
✅ **No maintenance** - We handle server updates and scaling
✅ **Latest AI models** - Access to the most recent AI capabilities  
✅ **Free to use** - No hosting costs for you  

---

## Self-Hosting Setup (Advanced)

If you prefer to host your own instance of the AI Code Review Bot, follow these steps:

## Prerequisites

### GitHub Repository Requirements

- GitHub repository with admin access
- Ability to create GitHub Actions workflows
- Pull request workflow enabled

### Backend Requirements

- Python 3.8+
- Flask web framework
- Perplexity AI API access

### Required Dependencies

```bash
flask
python-dotenv
openai
```

## Installation & Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/PranavJa1n/Auto_PR_Reviewer
```

### Step 2: Backend Setup

#### Install Dependencies

```bash
pip install -r requirements.txt --ignore-installed
```

Create a `.env` file in your project root:

```env
perplexity_api=your_perplexity_api_key_here
```

#### Get Perplexity API Key

1. Visit [Perplexity AI](https://www.perplexity.ai)
2. Sign up for an account
3. Navigate to API settings
4. Generate a new API key
5. Copy the key to your `.env` file

### Step 3: Deploy Backend

#### Option A: AWS EC2 Deployment

1. **Launch EC2 Instance**

   ```bash
   # Choose Amazon Linux 2 or Ubuntu 20.04 LTS
   # Instance type: t2.micro (free tier) or t3.small for production
   # Configure security group to allow HTTP (80) and HTTPS (443)
   ```

2. **Connect and Setup Server**

   ```bash
   # Connect via SSH
   ssh -i your-key.pem ec2-user@your-ec2-public-ip
   # Install Python, pip and git
   sudo yum install python3 python3-pip git -y  # Amazon Linux
   # OR
   sudo apt install python3 python3-pip git -y  # Ubuntu
   ```

3. **Deploy Application**

   ```bash
   # Clone your repository
   git clone https://github.com/PranavJa1n/Auto_PR_Reviewer
   
   # Install dependencies
   pip3 install -r requirements.txt
   
   # Create environment file
   echo "perplexity_api=<your_api_key_here>" > .env
   
   # Run application with Gunicorn for production
   pip3 install gunicorn
   gunicorn --bind 0.0.0.0:8080 app:app
   ```

#### Option B: Render Deployment

1. **Create Account**
   - Sign up at [Render](https://render.com)
   - Connect your GitHub account

2. **Deploy Web Service**
   - Click "New" → "Web Service"
   - Connect your repository
   - Configure settings:
     - **Name**: `ai-code-review-bot`
     - **Environment**: `Python 3`
     - **Build Command**: `pip install -r requirements.txt --ignore-installed`
     - **Start Command**: `gunicorn --bind 0.0.0.0:8080 app:app`

3. **Set Environment Variables**
   - Add `perplexity_api` with your API key
   - Get your service URL: `https://your-app-name.onrender.com`

#### Option C: Local Development

```bash
echo "perplexity_api=<your_api_key_here>" > .env
python app.py
# Server runs on http://127.0.0.1:8080
```

### Step 4: GitHub Action Setup

Create `.github/workflows/code-review.yaml` in your repository:

```yaml
name: AI Code Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: write
  issues: write

jobs:
  ai-review:
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Fetch base branch
        run: git fetch origin ${{ github.event.pull_request.base.ref }}

      - name: Find changed source files
        id: changed-files
        run: |
          FILES=$(git diff --name-only origin/${{ github.event.pull_request.base.ref }} ${{ github.sha }} | grep -E '\.(ex|groovy|bf|clj|py|js|ts|java|cpp|c|cs|sql|r|bash|go|rs|php|rb|swift|pl|vb|dart|scala|bhai)$' || true)
          FILES_JSON=$(echo "$FILES" | jq -R -s -c 'split("\n") | map(select(length > 0))')
          echo "files=$FILES_JSON" >> $GITHUB_OUTPUT

      - name: Review changed files with AI
        if: ${{ steps.changed-files.outputs.files != '[]' }}
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          set -e
          for file in $(echo '${{ steps.changed-files.outputs.files }}' | jq -r '.[]'); do
            CODE_CONTENT=$(jq -Rs . < "$file")
            PR_NUMBER="${{ github.event.pull_request.number }}"

            RESPONSE=$(curl -s -X POST YOUR_API_ENDPOINT_HERE \
              -H "Content-Type: application/json" \
              -d "{\"code\": $CODE_CONTENT, \"file_path\": \"$file\", \"pr_number\": \"$PR_NUMBER\"}")

            if ! echo "$RESPONSE" | jq empty >/dev/null 2>&1; then
              continue
            fi

            OVERALL_SCORE=$(echo "$RESPONSE" | jq -r '.overall_score // "N/A"')
            STATUS=$(echo "$RESPONSE" | jq -r '.status // "N/A"')
            TOTAL_ISSUES=$(echo "$RESPONSE" | jq -r '.total_issues // "0"')
            ISSUES_BLOCK=$(echo "$RESPONSE" | jq '.issues // []')
            POSITIVE_POINTS_BLOCK=$(echo "$RESPONSE" | jq '.positive_points // []')

            REVIEW_COMMENT="**File:** $file"$'\n'
            REVIEW_COMMENT+="Overall Score : $OVERALL_SCORE"$'\n'
            REVIEW_COMMENT+="Status : $STATUS"$'\n'
            REVIEW_COMMENT+="Total issues : $TOTAL_ISSUES"$'\n'
            REVIEW_COMMENT+="Issues :"$'\n'
            REVIEW_COMMENT+="$ISSUES_BLOCK"$'\n'
            REVIEW_COMMENT+="Positive points :"$'\n'
            REVIEW_COMMENT+="$POSITIVE_POINTS_BLOCK"

            curl -s -X POST \
              -H "Authorization: token $GITHUB_TOKEN" \
              -H "Content-Type: application/json" \
              "https://api.github.com/repos/${{ github.repository }}/issues/$PR_NUMBER/comments" \
              -d "{\"body\": $(echo "$REVIEW_COMMENT" | jq -Rs .)}" \
              >/dev/null 2>&1 || true
          done
```

**Important**: Replace `YOUR_API_ENDPOINT_HERE` with your actual backend URL or you can use.

## Configuration

### Trigger Events

The workflow triggers on:

- `opened`: New pull requests
- `synchronize`: New commits to existing PRs
- `reopened`: Reopened pull requests

#### File Filtering

The bot analyzes files with these extensions:

- Python: `.py`
- JavaScript: `.js`
- TypeScript: `.ts`
- C++: `.cpp`
- C: `.c`
- C#: `.cs`
- SQL: `.sql`
- R: `.r`
- Bash: `.bash`
- Go: `.go`
- Rust: `.rs`
- PHP: `.php`
- Ruby: `.rb`
- Swift: `.swift`
- Perl: `.pl`
- Visual Basic: `.vb`
- Dart: `.dart`
- Scala: `.scala`
- Bhai: `.bhai`
- Elixir: `.ex`
- Groovy: `.groovy`
- Brainf*ck: `.bf`
- Clojure: `.clj`
- Java: `.java`

#### Custom File Filters

Modify the regex pattern in the workflow to include/exclude file types:

```bash
grep -E '\.(py|js|ts|cpp|c)$'  # Only Python, JS, TS, C and C++
```

#### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `perplexity_api` | Perplexity AI API key | Yes |

#### Flask Configuration

```python
# app.py configurations
app.config['DEBUG'] = False  # Set to True for development
app.config['HOST'] = '0.0.0.0'
app.config['PORT'] = 8080
```

## Usage

The bot automatically reviews code when:

1. A new pull request is opened
2. Commits are pushed to an existing PR
3. A closed PR is reopened

### Overall Score

- **Scale**: 0-10 (10 being the best)
- **Factors**: Code quality, security, performance, maintainability

#### Issue Severity Levels

- 🔴 **Critical**: Security vulnerabilities, major bugs
- 🟠 **High**: Performance issues, logic errors
- 🟡 **Medium**: Code style, minor improvements
- 🟢 **Low**: Suggestions, optimizations

#### Sample Review Output

## API Reference

### POST /review

Reviews the provided code and returns analysis results.

#### Request Body

```json
{
  "code": "string",           // The code content to review
  "file_path": "string",      // Path to the file being reviewed
  "pr_number": "string"       // Pull request number
}
```

#### Response

```json
{
  "status": "string",         // Review status message
  "overall_score": 0,         // Score from 0-10
  "total_issues": 0,          // Total number of issues found
  "issues": [                 // Array of identified issues
    {
      "line_number": 0,       // Line number of the issue
      "severity": "string",   // critical/high/medium/low
      "category": "string",   // Issue category
      "title": "string",      // Brief issue title
      "description": "string", // Detailed description
      "suggestion": "string", // How to fix the issue
      "code_fix": "string"    // Example code fix
    }
  ],
  "positive_points": [        // Array of positive aspects
    "string"                  // Positive feedback
  ]
}
```

#### HTTP Status Codes

- `200`: Success
- `400`: Bad request (missing code or invalid JSON)
- `500`: Internal server error
- `401`: Unauthorized error (missing or invalid api key)

### GET /

Returns the main HTML interface for the code review bot.

## Troubleshooting

### 1. GitHub Action Not Triggering

**Problem**: Workflow doesn't run on PR creation

**Solutions**:

- Verify workflow file is in `.github/workflows/`
- Check file permissions and syntax
- Ensure repository has Actions enabled

#### 2. API Connection Errors

**Problem**: `curl: (7) Failed to connect to API`

**Solutions**:

```bash
# Check if your API endpoint is accessible
curl -I https://your-api-endpoint.com/review

# Verify environment variables
echo $API_ENDPOINT

# Test local connection
curl -X POST http://localhost:8080/review \
  -H "Content-Type: application/json" \
  -d '{"code": "print(\"hello\")", "file_path": "test.py", "pr_number": 1}'
```

#### 3. Perplexity API Key Issues

**Problem**: Authentication errors

**Solutions**:

- Verify API key is correct and active
- Check account usage limits
- Ensure environment variable is set correctly

#### 4. No Files Detected for Review

**Problem**: Workflow runs but finds no files

**Solutions**:

```bash
# Check file extensions in grep pattern
grep -E '\.(py|js|ts|java|cpp|c|cs|sql|r|bash|go|rs|php|rb|swift|pl|vb|dart|scala|bhai)$'

# Add your language extension if missing
# Verify files are actually changed in PR
```

#### 5. JSON Parse Errors

**Problem**: `Invalid JSON from API`

**Solutions**:

- Check API response format
- Verify AI model is returning valid JSON
- Implement JSON validation in backend

---
