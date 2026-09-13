import os
import zipfile

def create_zip():
    zip_filename = "code.zip"
    
    # Exclude these directories completely
    exclude_dirs = {".cache", ".git", "INFO", "dataset", "__pycache__"}
    
    # Exclude these exact filenames or prefixes
    exclude_files = {".env", "output.csv", "log.txt"}
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk("."):
            # Modify dirs in-place to skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith(".venv") and not d.startswith("venv")]
            
            for file in files:
                if file in exclude_files:
                    continue
                if file.startswith("scratch_"):
                    continue
                if file.endswith(".zip"):
                    continue
                if file == ".gitignore":
                    # include .gitignore? Yes, it's fine, or we can skip it. Let's skip it to be clean.
                    continue
                    
                # The path to add
                file_path = os.path.join(root, file)
                # The archive name (relative to root)
                arcname = os.path.relpath(file_path, ".")
                
                # Only include things we want: code/, evaluation/, tests/, README.md
                if arcname.startswith("code") or arcname.startswith("evaluation") or arcname.startswith("tests") or arcname == "README.md":
                    zf.write(file_path, arcname)

if __name__ == "__main__":
    create_zip()
    
    # Read-only audit
    print(f"--- ZIP AUDIT ---")
    size = os.path.getsize("code.zip")
    print(f"Size: {size} bytes")
    
    with zipfile.ZipFile("code.zip", 'r') as zf:
        file_list = zf.namelist()
        print("Files:")
        for f in sorted(file_list):
            print(f"  {f}")
