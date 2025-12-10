import os

# --- НАСТРОЙКИ ---
MAX_SIZE_BYTES = 500 * 1024  # 500 Кб (с запасом, чтобы влезло)
IGNORE_DIRS = {
    '.git', '__pycache__', 'node_modules', 'venv', 'env', 
    '.idea', '.vscode', 'build', 'dist', 'migrations', 'media', 'static_root'
}
IGNORE_FILES = {
    'package-lock.json', 'yarn.lock', 'packer_split.py', 
    '.DS_Store', 'db.sqlite3'
}
ALLOWED_EXTENSIONS = {
    '.py', '.js', '.ts', '.html', '.css', '.scss', 
    '.json', '.md', '.java', '.cpp', '.sql', '.xml', '.yaml', '.txt'
}
# -----------------

def get_file_header(path):
    return f"\n{'='*50}\nFILE: {path}\n{'='*50}\n"

def pack_project():
    part_num = 1
    current_size = 0
    current_file = None
    
    # Функция открытия нового части
    def open_new_part():
        nonlocal part_num, current_size, current_file
        if current_file:
            current_file.close()
        filename = f'project_part_{part_num}.txt'
        current_file = open(filename, 'w', encoding='utf-8')
        current_size = 0
        print(f"Created: {filename}")
        part_num += 1

    open_new_part()

    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for file in files:
            if file in IGNORE_FILES or file.startswith('project_part_'):
                continue
            
            if not any(file.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
                continue

            file_path = os.path.join(root, file)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as infile:
                    content = infile.read()
                    header = get_file_header(file_path)
                    text_chunk = header + content + "\n"
                    chunk_size = len(text_chunk.encode('utf-8'))

                    # Если добавление этого файла превысит лимит — создаем новый том
                    if current_size + chunk_size > MAX_SIZE_BYTES:
                        open_new_part()
                    
                    current_file.write(text_chunk)
                    current_size += chunk_size
                    
            except Exception as e:
                print(f"Skipping {file_path}: {e}")

    if current_file:
        current_file.close()
    
    print(f"\n✅ Готово! Проект разбит на {part_num-1} частей.")
    print("Кидай их по одной, и я буду анализировать.")

if __name__ == "__main__":
    pack_project()