import json
import requests
import streamlit as st

def generate_tree_structure(summaries, api_url="http://localhost:11434/api/generate"):
    """
    Generates a tree structure based on file summaries, names, and paths using Ollama's API.
    
    Args:
        summaries (list): A list of dictionaries containing summaries, file names, and file paths.
    
    Returns:
        dict: A JSON response containing the proposed tree structure with new file paths.
    """
    # Construct the prompt
    summaries_text = "\n".join([f"File: {s['file_name']}\nSummary: {s['summary']}" for s in summaries])

    prompt = f"""
    You must return strictly valid JSON, no extra formatting or keys.

    You will be provided with list of source files and a summary of their contents. For each file, propose a new path and filename, using a directory structure that optimally organizes the files.
    Follow good naming conventions. Here are a few guidelines:
    - Think about your files: What related files are you working with?
    - Identify metadata (for example, date, sample, experiment): What information is needed to easily locate a specific file?
    - Do not create multiple subdirectories for a single file, unless it is necessary.
    - Abbreviate or encode metadata.
    - Think about how you will search for your files: What comes first?

    - The file name needs to be descriptive and concise.
    - Format file names: Avoid spaces, capital letters or special characters in your file names. Strictly use only lowercase and underscores instead.

    If the file is already named well or matches a known convention, set the destination path to the same as the source path.
    The destination path should be placed under the current directory. Always return the full path.

    Summaries:
    \"\"\"
    {summaries}
    \"\"\"
    
    Your response must ONLY be a JSON object with the following schema:
    {{
            {{
                "src_path": "original file path",
                "summary": "original summary of the file content",
                "dst_path": "new full file path"
            }}
        ]
    }}

    Do not include any additional text or formatting."""

    payload = {
        "model": "llama3",
        "prompt": prompt.strip(),
        "stream": False
    }

    try:
        response = requests.post(api_url, json=payload)
        response.raise_for_status()

        data = response.json()
        tree_response = data.get("response", "").strip()
        return json.loads(tree_response)
    except requests.exceptions.RequestException as e:
        st.error(f"Error generating tree structure: {e}")
        return []
    except json.JSONDecodeError:
        st.error("Failed to decode the tree structure JSON.")
        return []
