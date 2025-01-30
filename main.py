import os
import json
import streamlit as st
from modules.file_readers import (
    read_pdf, read_doc, read_py, read_txt, read_pptx, 
    read_excel, read_csv, read_kml, read_image
)
from modules.summarization import (
    summarize_with_ollama, summarize_image_with_moondream
)
from modules.tree_structure import generate_tree_structure
from modules.utils import (
    list_visible_files_recursive, create_tree_buttons, display_error_files
)

# Set the page layout to wide
st.set_page_config(page_title="LLMを使った自動ファイル仕訳機能", layout="wide")

# Title for the Streamlit app
st.title("LLMを使った自動ファイル仕訳機能")

# Input for the directory path
st.text("現時点では、txt、PDF、Word、PowerPoint、Excel、JPG/PNGファイルに対応しています。")
st.text("仕訳したいディレクトリを入力して下さい：")

# Create a container for the directory input and the button
col1, col2 = st.columns([7, 1])  # Adjust the ratio as needed

with col1:
    # Input for directory path
    directory = st.text_input("user_dir_input", label_visibility="collapsed")

with col2:
    # Add the "仕訳開始" button next to the directory input
    start_button = st.button("仕訳開始")

# Initialize session state variables
if 'summaries' not in st.session_state:
    st.session_state.summaries = []
if 'new_tree' not in st.session_state:
    st.session_state.new_tree = []
if 'inputs' not in st.session_state:
    st.session_state.inputs = {}
if 'error_files' not in st.session_state:
    st.session_state.error_files = []
if 'last_directory' not in st.session_state:
    st.session_state.last_directory = ""

# Main logic
if directory:
    # Check if the directory has changed since the last run
    if directory != st.session_state.last_directory:
        # If directory has changed, reset the session state
        st.session_state.summaries = []
        st.session_state.new_tree = []
        st.session_state.error_files = []
        st.session_state.inputs = {}
        st.session_state.last_directory = directory

    if start_button:
        if os.path.isdir(directory):
            # Clear previous summaries and errors if reprocessing
            st.session_state.summaries = []
            st.session_state.new_tree = []
            st.session_state.error_files = []

            visible_files = list_visible_files_recursive(directory)

            st.write(f"{len(visible_files)}ファイルを読み込み中...")

            if visible_files:
                progress_bar = st.progress(0)
                total_files = len(visible_files)

                summaries = []
                for idx, file_path in enumerate(visible_files):
                    progress_percentage = int((idx + 1) / total_files * 100)
                    progress_bar.progress(progress_percentage)

                    if file_path.lower().endswith(('.jpg', '.jpeg', '.png')):
                        image_data = read_image(file_path)
                        if image_data.get("error"):
                            st.session_state.error_files.append({
                                "file_name": image_data.get("file_name"),
                                "file_path": image_data.get("image_path"),
                                "summary": image_data.get("error_msg", "画像の読み込みエラー"),
                                "error": True
                            })
                            continue
                        summary = summarize_image_with_moondream(image_data)
                        if summary.get("error"):
                            st.session_state.error_files.append(summary)
                        else:
                            summaries.append(summary)
                        continue
                    elif file_path.endswith('.pdf'):
                        file_content = read_pdf(file_path)
                    elif file_path.endswith(('.docx', '.doc')):
                        file_content = read_doc(file_path)
                    elif file_path.endswith('.py'):
                        file_content = read_py(file_path)
                    elif file_path.endswith('.txt'):
                        file_content = read_txt(file_path)
                    elif file_path.endswith('.pptx'):
                        file_content = read_pptx(file_path)
                    elif file_path.endswith('.xlsx'):
                        file_content = read_excel(file_path)
                    elif file_path.endswith('.csv'):
                        file_content = read_csv(file_path)
                    elif file_path.endswith('.kml'):
                        file_content = read_kml(file_path)
                    else:
                        continue  # Unsupported file type

                    if file_content.get("error"):
                        st.session_state.error_files.append(file_content)
                        continue

                    summary = summarize_with_ollama(file_content)
                    if summary.get("error"):
                        st.session_state.error_files.append(summary)
                    else:
                        summaries.append(summary)

                st.session_state.summaries = summaries
                progress_bar.progress(100)
                st.write("仕訳先作成中。数分間かかります。")

                if summaries:
                    new_tree_response = generate_tree_structure(summaries)
                    st.session_state.new_tree = new_tree_response
                else:
                    st.write("エラーのため、仕訳先を作成できませんでした。")
            else:
                st.write("入力したディレクトリ先にファイルがありません。")
        else:
            st.error("有効なディレクトリを入力して下さい。")

    # Display the tree buttons and error files only if processing has been done
    if st.session_state.new_tree:
        create_tree_buttons(st.session_state.new_tree, directory)

    if st.session_state.error_files:
        display_error_files(st.session_state.error_files)
