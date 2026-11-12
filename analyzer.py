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
    Analyzes a single code file and returns a formatted status report in English.
    """
    report_lines = []
    extension = filename.split(".")[-1].lower() if "." in filename else ""

    # 1. Syntax & Structure Verification
    if extension == "py":
        try:
            ast.parse(content)
            report_lines.append("✅ **Python Syntax:** Valid (no syntax errors detected).")
        except SyntaxError as error:
            report_lines.append(f"❌ **Python Error (Line {error.lineno}):** `{error.msg}`")

    elif extension == "json":
        try:
            json.loads(content)
            report_lines.append("✅ **JSON Syntax:** Valid.")
        except json.JSONDecodeError as error:
            report_lines.append(f"❌ **JSON Error (Line {error.lineno}):** `{error.msg}`")

    elif extension in ["js", "html", "css"]:
        balanced_braces = content.count("{") == content.count("}")
        balanced_parens = content.count("(") == content.count(")")
        if not balanced_braces or not balanced_parens:
            report_lines.append("⚠️ **Structure Warning:** Unclosed curly braces `{}` or parentheses `()`.")
        else:
            report_lines.append(f"✅ **{extension.upper()} Structure:** Braces and parentheses are properly balanced.")

    else:
        report_lines.append(f"ℹ️ **.{extension} File:** Saved (no syntax check required for plain text).")

    # 2. Security Verification (Exposed Discord Bot Tokens)
    discord_token_regex = r"[MN][A-Za-z\d]{23}\.[\w-]{6}\.[\w-]{27}"
    if re.search(discord_token_regex, content):
        report_lines.append("🚨 **Security Alert:** A **Discord Bot Token** appears to be exposed in plain text!")

    return "\n".join(report_lines)
