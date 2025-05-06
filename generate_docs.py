"""
Script para gerar arquivos HTML a partir dos arquivos markdown.
"""
import os
import re

def read_file(file_path):
    """Lê o conteúdo de um arquivo."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(file_path, content):
    """Escreve conteúdo em um arquivo."""
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def extract_title(markdown_content):
    """Extrai o título do conteúdo markdown."""
    match = re.search(r'^# (.+)$', markdown_content, re.MULTILINE)
    if match:
        return match.group(1)
    return "Documentação"

def generate_html_from_markdown(markdown_file, template_file, output_file):
    """Gera um arquivo HTML a partir de um arquivo markdown usando um template."""
    markdown_content = read_file(markdown_file)
    template_content = read_file(template_file)
    
    title = extract_title(markdown_content)
    
    # Escape backticks in markdown content to avoid breaking the JavaScript template literal
    markdown_content = markdown_content.replace('`', '\\`')
    
    # Replace placeholders in template
    html_content = template_content.replace('{{TITLE}}', title)
    html_content = html_content.replace('{{CONTENT}}', markdown_content)
    
    write_file(output_file, html_content)
    print(f"Generated {output_file} from {markdown_file}")

def main():
    """Função principal."""
    # Diretórios
    docs_dir = 'docs'
    template_file = 'assets/help_docs/template.html'
    output_dir = 'assets/help_docs'
    
    # Verificar se os diretórios existem
    if not os.path.exists(docs_dir):
        print(f"Directory {docs_dir} does not exist.")
        return
    
    if not os.path.exists(template_file):
        print(f"Template file {template_file} does not exist.")
        return
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Processar cada arquivo markdown
    for filename in os.listdir(docs_dir):
        if filename.endswith('.md'):
            markdown_file = os.path.join(docs_dir, filename)
            output_file = os.path.join(output_dir, filename.replace('.md', '.html'))
            generate_html_from_markdown(markdown_file, template_file, output_file)

if __name__ == '__main__':
    main()
