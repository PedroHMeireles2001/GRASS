import os
import json
import re


def minify_python(code):
    """Remove comentários, docstrings e espaços em branco desnecessários."""
    code = re.sub(r'(""".*?"""|\'\'\'.*?\'\'\')', '', code, flags=re.DOTALL)
    code = re.sub(r'#.*', '', code)
    lines = [line.rstrip() for line in code.splitlines() if line.strip()]
    return "\n".join(lines)

def generate_optimized_context():
    # Diretórios críticos a serem incluídos por completo (adicionado src/engine/ui)
    critical_dirs = [
        'src/engine/scene', 
        'src/model', 
        'src/engine/ui'
    ]
    
    # Caminhos específicos para arquivos avulsos solicitados
    specific_files = [
        'src/utils.py',
        'src/engine/ai/chat.py',
        'src/engine/ai/tools.py',
        'src/main.py'
    ]
    
    # Arquivos individuais adicionais mantidos por compatibilidade
    must_include = [
        'CharacterCreator.py', 
        'CombatScene.py', 
        'constants.py'
    ]
    
    context = {
        "repo": "GRASS",
        "files": []
    }

    for root, _, files in os.walk('src'):
        rel_root = root.replace(os.sep, '/')
        
        # Verifica se a pasta atual faz parte dos diretórios críticos
        is_critical_path = any(d in rel_root for d in critical_dirs)
        
        for file in files:
            if not file.endswith('.py'): continue
            
            file_path = os.path.join(root, file).replace(os.sep, '/')
            
            # Condição expandida: diretório crítico, arquivo essencial ou caminho específico
            if is_critical_path or file in must_include or file_path in specific_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        raw_code = f.read()
                        minified = raw_code.strip()

                        context["files"].append({
                            "p": file_path, 
                            "c": minified   
                        })
                except Exception as e:
                    print(f"Erro ao processar {file}: {e}")

    # Salva o JSON compacto
    output_name = 'grass_context_minified-raw-strip.json'
    with open(output_name, 'w', encoding='utf-8') as f:
        json.dump(context, f, separators=(',', ':'), ensure_ascii=False)
    
    size_kb = os.path.getsize(output_name) / 1024
    print(f"✅ Gerado: {output_name} ({size_kb:.1f} KB)")
    print(f"📁 Arquivos incluídos: {len(context['files'])}")

if __name__ == "__main__":
    generate_optimized_context()