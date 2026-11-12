
"""
====================================================================
MODULE: analyzer.py
PURPOSE: Static code syntax verification and security scanner.
DESCRIPTION: Validates Python (AST), JSON, and web bracket structures
             safely without executing untrusted user code, and scans
             for accidentally exposed Discord Bot Tokens.
====================================================================
"""

import ast
import json
import re


def analyze_code_file(filename: str, content: str) -> str:
    """
    Analyzes a single code file and returns a formatted status report.
    
    Parameters:
        filename (str): Full name of the file (e.g., 'main.py').
        content (str): The raw text content of the file.
        
    Returns:
        str: A multi-line report ready to be embedded in Discord.
    """
    report_lines = []
    # Extract the file extension (e.g., 'py', 'json', 'js')
    extension = filename.split(".")[-1].lower() if "." in filename else ""

    # ----------------------------------------------------------------
    # 1. SYNTAX & STRUCTURE CHECKS BY FILE EXTENSION
    # ----------------------------------------------------------------
    if extension == "py":
        # Uses Python's built-in Abstract Syntax Tree (AST) to validate syntax safely
        try:
            ast.parse(content)
            report_lines.append("✅ **Syntaxe Python :** Valide (aucune erreur détectée).")
        except SyntaxError as error:
            report_lines.append(f"❌ **Erreur Python (Ligne {error.lineno}) :** `{error.msg}`")

    elif extension == "json":
        # Validates strict JSON formatting (quotes, commas, brackets)
        try:
            json.loads(content)
            report_lines.append("✅ **Syntaxe JSON :** Valide.")
        except json.JSONDecodeError as error:
            report_lines.append(f"❌ **Erreur JSON (Ligne {error.lineno}) :** `{error.msg}`")

    elif extension in ["js", "html", "css"]:
        # Checks if curly braces {} and parentheses () are properly closed
        balanced_braces = content.count("{") == content.count("}")
        balanced_parens = content.count("(") == content.count(")")
        if not balanced_braces or not balanced_parens:
            report_lines.append("⚠️ **Structure :** Accolades `{}` ou parenthèses `()` mal fermées.")
        else:
            report_lines.append(f"✅ **Structure {extension.upper()} :** Parenthèses et accolades équilibrées.")

    else:
        # Fallback for .txt, .env, or other plain text configuration files
        report_lines.append(f"ℹ️ **Fichier .{extension} :** Enregistré (aucune vérification syntaxique requise).")

    # ----------------------------------------------------------------
    # 2. SECURITY SCANNER (DISCORD TOKEN LEAK DETECTION)
    # ----------------------------------------------------------------
    # Regex matching standard Discord bot token structure
    discord_token_regex = r"[MN][A-Za-z\d]{23}\.[\w-]{6}\.[\w-]{27}"
    if re.search(discord_token_regex, content):
        report_lines.append("🚨 **Alerte Sécurité :** Un **Token Discord** semble exposé en clair dans ce fichier !")

    return "\n".join(report_lines)
