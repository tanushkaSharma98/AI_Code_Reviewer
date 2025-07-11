import os
import zipfile
from git import Repo

def save_uploaded_file(file, dest_dir):
    os.makedirs(dest_dir, exist_ok=True)
    file_path = os.path.join(dest_dir, file.filename)
    file.save(file_path)
    return file_path

def clone_github_repo(repo_url, dest_dir):
    os.makedirs(dest_dir, exist_ok=True)
    Repo.clone_from(repo_url, dest_dir)

def extract_zip(zip_path, extract_to):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

def create_session_zip(session_dir, zip_path=None):
    if zip_path is None:
        zip_path = os.path.join(session_dir, 'session_package.zip')
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add all files except the ZIP itself
        for root, _, files in os.walk(session_dir):
            for file in files:
                if file.endswith('.zip'):
                    continue
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, session_dir)
                zipf.write(abs_path, rel_path)
    return zip_path 