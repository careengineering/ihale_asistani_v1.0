import os
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern

# .gitignore dosyasını oku ve pathspec oluştur
def load_gitignore(path):
    gitignore_path = os.path.join(path, '.gitignore')
    if not os.path.exists(gitignore_path):
        return PathSpec.from_lines(GitWildMatchPattern, [])
    with open(gitignore_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    return PathSpec.from_lines(GitWildMatchPattern, lines)

# İçeriği atlanacak klasörler (yalnızca isimlerini göstereceğiz)
skip_content_dirs = ['.git', '.venv']

# Klasör yapısını oku ve ignore edilenleri atla
def generate_tree(path, spec, prefix=''):
    tree_str = ''
    entries = sorted(os.listdir(path))
    filtered_entries = []
    # Filtrelenmiş girişler için ignore ve skip kontrolü
    for entry in entries:
        full_path = os.path.join(path, entry)
        relative_path = os.path.relpath(full_path, start='.')
        if spec.match_file(relative_path):
            continue
        filtered_entries.append(entry)

    for index, entry in enumerate(filtered_entries):
        full_path = os.path.join(path, entry)
        connector = '└── ' if index == len(filtered_entries) - 1 else '├── '
        tree_str += f"{prefix}{connector}{entry}\n"
        # Eğer klasör ve içeriği atlanacak klasörler listesinde değilse içeriği göster
        if os.path.isdir(full_path) and entry not in skip_content_dirs:
            extension = '    ' if index == len(filtered_entries) - 1 else '│   '
            tree_str += generate_tree(full_path, spec, prefix + extension)
    return tree_str

# Ana klasör yolu (örn: '.')
base_path = '.'
spec = load_gitignore(base_path)
tree_output = generate_tree(base_path, spec)

# Sonucu dosyaya yaz
output_file_path = os.path.join(os.getcwd(), 'directory_structure.txt')
with open(output_file_path, 'w', encoding='utf-8') as f:
    f.write(tree_output)

print(f"Klasör yapısı ('.gitignore' dikkate alınarak) '{output_file_path}' dosyasına yazıldı.")

