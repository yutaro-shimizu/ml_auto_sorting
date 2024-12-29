import asyncio
import json
import os
from collections import defaultdict

import aiohttp
from llama_index.core import Document, SimpleDirectoryReader
from llama_index.core.schema import ImageDocument
from llama_index.core.node_parser import TokenTextSplitter
from termcolor import colored
from dotenv import load_dotenv

load_dotenv()  # Load environment variables

OLLAMA_URL = "http://localhost:11434/api/generate"  # Ollama local REST API endpoint
OLLAMA_MODEL = "llama3"

# Async function to get directory summaries
async def get_dir_summaries(path: str):
    doc_dicts = load_documents(path)
    summaries = await get_summaries(doc_dicts)
    # Convert path to relative path
    for summary in summaries:
        summary["file_path"] = os.path.relpath(summary["file_path"], path)
    return summaries

# Function to load documents from a directory
def load_documents(path: str):
    reader = SimpleDirectoryReader(
        input_dir=path,
        recursive=True,
        required_exts=[".pdf", ".txt", ".png", ".jpg", ".jpeg"],
    )
    splitter = TokenTextSplitter(chunk_size=6144)
    documents = []
    for docs in reader.iter_data():
        if len(docs) > 1:
            for d in docs:
                contents = splitter.split_text("\n".join(d.text))
                text = contents[0] if len(contents) > 0 else ""
                documents.append(Document(text=text, metadata=docs[0].metadata))
        else:
            documents.append(docs[0])
    return documents

def process_metadata(doc_dicts):
    file_seen = set()
    metadata_list = []
    for doc in doc_dicts:
        if doc["file_path"] not in file_seen:
            file_seen.add(doc["file_path"])
            metadata_list.append(doc)
    return metadata_list

def document_to_dict(doc):
    return {
        "text": doc.text,
        "metadata": doc.metadata,
    }

# Async function to summarize a document
async def summarize_document(doc, client):
    PROMPT = """
    You will be provided with the contents of a file along with its metadata. Provide a summary of the contents. The purpose of the summary is to organize files based on their content. To this end provide a concise but informative summary. Make the summary as specific to the file as possible.

    Write your response a JSON object with the following schema:

    ```json
    {
        "file_path": "path to the file including name",
        "summary": "summary of the content"
    }
    """.strip()

    max_retries = 5
    attempt = 0
    while attempt < max_retries:
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": PROMPT},
                    {"role": "user", "content": json.dumps(document_to_dict(doc))},
                ],
                model=OLLAMA_MODEL,
                response_format={"type": "json_object"},
                temperature=0,
            )
            break
        except Exception as e:
            print("Error status {}".format(e.status_code))
            attempt += 1

    summary = json.loads(chat_completion.choices[0].message.content)

    try:
        # Print the filename in green
        print(colored(summary["file_path"], "green"))
        print(summary["summary"])  # Print the summary of the contents
        # Print a separator line with spacing for readability
        print("-" * 80 + "\n")
    except KeyError as e:
        print(e)

    return summary

async def summarize_image_document(doc: ImageDocument, client): 
    PROMPT = """ You will be provided with an image along with its metadata. Provide a summary of the image contents. 
    The purpose of the summary is to organize files based on their content. To this end provide a concise but informative summary. 
    Make the summary as specific to the file as possible.
    Write your response a JSON object with the following schema:

    ```json{
        "file_path": "path to the file including name",
        "summary": "summary of the content"
    }
    """.strip()

    chat_completion = await client.chat(
        messages=[
            {"role": "user", "content": "Summarize the contents of this image."},
        ],
        model="moondream",
    )

    summary = {
        "file_path": doc.image_path,
        "summary": chat_completion["message"]["content"],
    }
    return summary

async def dispatch_summarize_document(doc, client):
    if isinstance(doc, ImageDocument):
        return await summarize_image_document(doc, client)
    elif isinstance(doc, Document):
        print(f"Summarizing document: {doc.metadata['file_path']}")
        return await summarize_document({"content": doc.text, **doc.metadata}, client)
    else:
        raise ValueError("Document type not supported")

async def get_summaries(documents):
    """
    Summarizes a list of documents using the Ollama API.

    Args:
        documents (list): A list of documents to summarize.

    Returns:
        list: A list of summaries for the provided documents.
    """
    async with aiohttp.ClientSession() as session:
        summaries = await asyncio.gather(
            *[dispatch_summarize_document(doc, session) for doc in documents]
        )
    return summaries

def merge_summary_documents(summaries, metadata_list):
    list_summaries = defaultdict(list)

    for item in summaries:
        list_summaries[item["file_path"]].append(item["summary"])

    file_summaries = {
        path: ". ".join(summaries) for path, summaries in list_summaries.items()
    }

    file_list = [
        {"summary": file_summaries[file["file_path"]], **file} for file in metadata_list
    ]

    return file_list