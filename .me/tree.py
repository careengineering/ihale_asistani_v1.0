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

# Klasör yapısını oku ve ignore edilenleri atla
def generate_tree(path, spec, prefix=''):
    tree_str = ''
    entries = sorted(os.listdir(path))
    for index, entry in enumerate(entries):
        full_path = os.path.join(path, entry)
        relative_path = os.path.relpath(full_path, start='.')
        if spec.match_file(relative_path):
            continue
        connector = '└── ' if index == len(entries) - 1 else '├── '
        tree_str += f"{prefix}{connector}{entry}\n"
        if os.path.isdir(full_path):
            extension = '    ' if index == len(entries) - 1 else '│   '
            tree_str += generate_tree(full_path, spec, prefix + extension)
    return tree_str

# Ana klasör yolu (örn: '.')
base_path = '.'
spec = load_gitignore(base_path)
tree_output = generate_tree(base_path, spec)

# Sonucu dosyaya yaz
with open('directory_structure.txt', 'w', encoding='utf-8') as f:
    f.write(tree_output)

print("Klasör yapısı ('.gitignore' dikkate alınarak) 'directory_structure.txt' dosyasına yazıldı.")
