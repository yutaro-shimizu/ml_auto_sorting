import json
import requests

def summarize_with_ollama(file_data: dict) -> dict:
    """
    Sends a prompt to Ollama's REST API and returns a concise summary of the file content.
    
    Args:
        file_data (dict): Must contain "text", "file_name", and "file_path".
    
    Returns:
        dict: A dictionary containing the summary and error flag.
    """
    ollama_url = "http://localhost:11434/api/generate"
    text_content = file_data.get("text", "")
    file_name = file_data.get("file_name", "")
    file_path = file_data.get("file_path", "")

    # Truncate text to avoid overly large prompts
    truncated_text = text_content[:5000]

    # Strict prompt to request a single JSON object with only "summary"
    prompt = f"""
You are an AI assistant. You must return strictly valid JSON, no extra formatting or keys.

Constraints:
- summary: A short, human-readable summary of the file (100 words max).

File content:
\"\"\"
{truncated_text}
\"\"\"

Return exactly:
{{
  "summary": "..."
}}
No additional fields or text.
"""

    payload = {
        "model": "llama3.2",  # Adjust if needed
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(ollama_url, json=payload, timeout=60)
        if response.status_code != 200:
            return {"summary": "No summary available.", "file_name": file_name, "file_path": file_path, "error": True}

        # "response" is where Ollama places the model's text output
        data = response.json()
        raw_response = data.get("response", "").strip()

        # Attempt to parse raw_response as JSON
        try:
            parsed_json = json.loads(raw_response)
            parsed_json["file_name"] = file_name
            parsed_json["file_path"] = file_path
            parsed_json["error"] = False
            return parsed_json
        except json.JSONDecodeError:
            return {"summary": "No summary available.", "file_name": file_name, "file_path": file_path, "error": True}

    except requests.exceptions.RequestException:
        return {"summary": "No summary available.", "file_name": file_name, "file_path": file_path, "error": True}

def summarize_image_with_moondream(image_data: dict) -> dict:
    """
    Summarizes the content of an image using the Ollama Moondream API.

    Args:
        image_data (dict): Must contain "image_path" and "file_name".

    Returns:
        dict: A dictionary containing the summary, file details, and error flag.
    """
    api_url = "http://localhost:11434/api/generate"
    image_path = image_data.get("image_path", "")
    file_name = image_data.get("file_name", "")

    try:
        # Prepare the payload for the API
        payload = {
            "model": "moondream",
            "prompt": "Describe the contents of this image and summarize its features.",
            "image": image_path,
            "stream": False
        }

        # Make the API request
        response = requests.post(api_url, json=payload)
        response.raise_for_status()

        # Parse the response
        summary_data = response.json()

        # Return the summary
        return {
            "summary": summary_data.get("response", "No summary returned."),
            "file_path": image_path,
            "file_name": file_name,
            "error": False
        }
    except Exception as e:
        return {
            "summary": f"Error processing image: {e}",
            "file_path": image_path,
            "file_name": file_name,
            "error": True
        }
