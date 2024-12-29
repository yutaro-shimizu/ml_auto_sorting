import os
import asyncio
import json
import pathlib
from pathlib import Path
from asciitree import LeftAligned
from asciitree.drawing import BoxStyle, BOX_LIGHT
import streamlit as st
from dotenv import load_dotenv

# Import custom functions
from src.loader import get_dir_summaries
from src.tree_generator import create_file_tree

# Load environment variables
load_dotenv()

# Initialize the Streamlit app
st.set_page_config(page_title="Directory Summarizer", layout="wide")
st.title("Directory Summarizer and Tree Viewer")

# Input: Source and Destination paths
src_path = st.text_input("Source Path", help="Enter the path of the source directory")
dst_path = st.text_input(
    "Destination Path", help="Enter the path where the directory tree will be created"
)

# Confirmation checkbox
auto_yes = st.checkbox("Automatically confirm directory structure creation")

# Process the directory when "Generate" is clicked
if st.button("Generate Directory Structure"):
    if not src_path or not dst_path:
        st.error("Both source and destination paths are required!")
    else:
        try:
            # Run the asynchronous function to get directory summaries
            summaries = asyncio.run(get_dir_summaries(src_path))
            
            # Create file tree
            files = create_file_tree(summaries)

            BASE_DIR = pathlib.Path(dst_path)
            BASE_DIR.mkdir(exist_ok=True)

            # Recursively create dictionary from file paths
            tree = {}
            for file in files:
                parts = Path(file["dst_path"]).parts
                current = tree
                for part in parts:
                    current = current.setdefault(part, {})
            tree = {dst_path: tree}

            # Render the directory tree as ASCII art
            tr = LeftAligned(draw=BoxStyle(gfx=BOX_LIGHT, horiz_len=1))
            st.text("Generated Directory Tree:")
            st.code(tr(tree), language="text")

            # Confirm action
            if auto_yes or st.button("Confirm and Proceed"):
                for file in files:
                    file["dst_path"] = os.path.join(src_path, file["dst_path"])
                    file["summary"] = summaries[files.index(file)]["summary"]
                    file["path"] = pathlib.Path(file["dst_path"])
                    (BASE_DIR / file["path"]).parent.mkdir(parents=True, exist_ok=True)
                    with open(BASE_DIR / file["path"], "w") as f:
                        f.write("")

                st.success("Directory structure created successfully!")
            else:
                st.warning("Operation cancelled.")
        except Exception as e:
            st.error(f"An error occurred: {e}")

# Footer
st.markdown(
    """
    **Instructions:**
    1. Provide a source directory path to analyze.
    2. Provide a destination directory path where the directory tree will be created.
    3. Click "Generate Directory Structure" to preview the directory tree.
    4. Confirm to create the directory structure at the destination.
    """
)