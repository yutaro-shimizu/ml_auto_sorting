import os
import shutil
import streamlit as st
import pandas as pd

def list_visible_files_recursive(path):
    file_list = []
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if not d.startswith('.')]  # Exclude hidden dirs
        for file in files:
            if not file.startswith('.'):  # Exclude hidden files
                full_path = os.path.join(root, file)
                file_list.append(full_path)
    return file_list

def move_file(src, dst):
    try:
        if not os.path.exists(dst):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.move(src, dst)
            st.success(f"移動しました: {src} -> {dst}")
        else:
            st.warning(f"同名ファイルが既にあります: {dst}")
    except Exception as e:
        st.error(f"ファイルの移動に失敗しました: {e}")

def on_move(src_path, dst_path, new_tree):
    move_file(src_path, dst_path)
    # Update the tree structure in session state
    for item in new_tree:
        if item["src_path"] == src_path:
            item["dst_path"] = dst_path
            break

def on_reset(src_path, original_dst, new_tree):
    current_dst = next((item["dst_path"] for item in new_tree if item["src_path"] == src_path), original_dst)
    move_file(current_dst, src_path)
    # Reset the destination path in new_tree
    for item in new_tree:
        if item["src_path"] == src_path:
            item["dst_path"] = src_path
            break

def create_tree_buttons(new_tree, directory):
    """
    Create buttons in Streamlit for a tree structure based on the given new_tree.
    """
    st.write("移動実行ボタンを押すと、ファイルを移動できます。リセットボタンを押すと、変更を元に戻すことができます。    \n移動実行・リセットボタンを押すと、ローカル環境のディレクトリやファイル配下が変わるので注意して利用してください。")

    for file in new_tree:
        src_path = file["src_path"]
        summary = file["summary"]
        dst_path = os.path.join(directory, file["dst_path"])
        original_dst = file.get("original_dst_path", dst_path)

        # Editable directory path
        text_input_key = f"text_input_{src_path}"
        if src_path not in st.session_state.inputs:
            st.session_state.inputs[src_path] = dst_path

        new_dir_input = st.text_input(
            f"移動先の編集 ({os.path.basename(src_path)}):",
            value=st.session_state.inputs[src_path],
            key=text_input_key
        )

        # Update the destination path in session state
        st.session_state.inputs[src_path] = new_dir_input
        file["dst_path"] = new_dir_input  # Update the new_tree with the new path

        cols = st.columns([5, 3, 1, 1])
        with cols[0]:
            st.write(f"元ディレクトリ: `{src_path}`")
            st.write(f"新ディレクトリ: `{new_dir_input}`")

        with cols[1]:
            st.write(f"*{summary}*")

        with cols[2]:
            if st.button(f"✅ 移動実行", key=f"move_{src_path}"):
                on_move(src_path, new_dir_input, new_tree)

        with cols[3]:
            if st.button(f"🔄 リセット", key=f"reset_{src_path}"):
                on_reset(src_path, original_dst, new_tree)

        # Add spacing between file entries
        st.markdown("---")

def display_error_files(error_files):
    """
    Display files that encountered errors during processing.
    """
    if error_files:
        st.header("エラーが発生したファイル")
        error_data = []
        for file in error_files:
            file_name = file.get("file_name", "不明なファイル")
            file_path = file.get("file_path", "不明なパス")
            error_msg = file.get("summary") if "summary" in file else file.get("error_msg", "エラー内容不明")
            error_data.append({
                "ファイル名": file_name,
                "パス": file_path,
                "エラー内容": error_msg
            })
        
        df_errors = pd.DataFrame(error_data)
        st.table(df_errors)
