import json
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"  # Ollama local REST API endpoint
OLLAMA_MODEL = "llama3"

FILE_PROMPT = """
You will be provided with list of source files and a summary of their contents. For each file, propose a new path and filename, using a directory structure that optimally organizes the files using known conventions and best practices.
Follow good naming conventions. Here are a few guidelines
- Think about your files : What related files are you working with?
- Identify metadata (for example, date, sample, experiment) : What information is needed to easily locate a specific file?
- Abbreviate or encode metadata
- Use versioning : Are you maintaining different versions of the same file?
- Think about how you will search for your files : What comes first?
- Deliberately separate metadata elements : Avoid spaces or special characters in your file names
If the file is already named well or matches a known convention, set the destination path to the same as the source path.

Your response must be a JSON object with the following schema:
```json
{
    "files": [
        {
            "src_path": "original file path",
            "dst_path": "new file path under proposed directory structure with proposed file name"
        }
    ]
}
```
""".strip()


def create_file_tree(summaries: list, session):
    """
    Creates a file tree using the Ollama API to suggest optimized file organization.
    Args:
        summaries (list): A list of dictionaries containing file summaries.

    Returns:
        list: A list of dictionaries with original and proposed file paths.
"""
    try:
        payload = {
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": FILE_PROMPT},
                {"role": "user", "content": json.dumps(summaries)},
            ],
            "temperature": 0,
        }

        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()  # Raise an exception for HTTP errors

        result = response.json()
        if "files" in result:
            return result["files"]
        else:
            raise ValueError("Invalid response format: 'files' key not found.")
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with Ollama API: {e}")
        return []
    except ValueError as e:
        print(f"Error processing response: {e}")
        return []