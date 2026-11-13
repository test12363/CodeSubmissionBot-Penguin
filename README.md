<div align="center">
#  📦 Discord Code Submission & Verification Bot

**A modular, production-ready Discord bot for multi-file code submissions, automated syntax/security analysis, ZIP packaging, and staff moderation.**

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Discord.py](https://img.shields.io/badge/discord.py-2.3%2B-5865F2?style=for-the-badge&logo=discord&logoColor=white)
![Status](https://img.shields.io/badge/Status-Production_Ready-2EA44F?style=for-the-badge)
</div>

---

## ✨ Key Features

* **🔒 Private Dynamic Workspaces** — Automatically creates private channels (`#purpose-username`) restricted to the author and two configurable staff roles.
* **📂 Multi-File & Multi-Part Support** — Submit unlimited files (`.py`, `.js`, `.txt`, `.env`, `.json`, `.html`, `.css`) up to **50,000 characters per file**, using either an exact part counter or free-paste (`idk`) mode.
* **🔍 Automated A-to-Z Code Scanner** — Safely validates Python (AST), JSON, and web bracket structures without executing untrusted code, while scanning for exposed Discord Bot Tokens.
* **⚡ One-Click Staff Actions**:
  * **✔️ Accept** — Automatically grants a reward role to the author and compiles all files into a clean `.zip` archive.
  * **✖️ Decline** — Applies an automatic 30-minute timeout (mute) to the author and deletes the workspace.
* **♻️ Persistent UI** — Buttons and dropdowns survive bot restarts seamlessly.

---

## 📁 Project Structure

```text
CodeSubmissionBot/
├── 📄 bot.py              # Main entry point, event listeners & !setup command
├── 🎨 ui_components.py    # Modals, dropdowns, persistent buttons & ZIP builder
├── 🔍 analyzer.py         # Static syntax validator & token leak scanner
├── ⚙️ config.json         # Easy configuration file (Token, Role IDs, Limits)
├── 📦 requirements.txt    # Python dependencies
└── 📘 README.md           # Documentation
```

---

## 🚀 Quick Setup Guide

### Step 1 — Install Dependencies
Ensure **Python 3.10+** is installed, then run:
```bash
pip install -r requirements.txt
```

### Step 2 — Discord Developer Portal
1. Open the **[Discord Developer Portal](https://discord.com/developers/home)** and select your application.
2. Go to the **Bot** tab and enable all **3 Privileged Gateway Intents**:
   * `Presence Intent`
   * `Server Members Intent`
   * `Message Content Intent`
3. In your Discord server settings, ensure the bot's role is placed **higher** than the reward role and regular member roles.

### Step 3 — Configure `config.json`
Open `config.json` and replace the placeholder IDs with your own:

| Key | Description | Example |
| :--- | :--- | :--- |
| `token` | Your Discord Bot Token | `"MTI4N..."` |
| `prefix` | Command prefix for admin setup | `"!"` |
| `category_id` | Category ID where private channels spawn | `123456789012345678` |
| `admin_role_1_id` | First staff role pinged & allowed to review | `123456789012345678` |
| `admin_role_2_id` | Second staff role pinged & allowed to review | `123456789012345678` |
| `reward_role_id` | Role automatically granted upon acceptance | `123456789012345678` |
| `max_chars_per_file` | Maximum characters allowed per file | `50000` |
| `mute_duration_minutes` | Timeout duration when a project is declined | `30` |

### Step 4 — Launch & Spawn Panel
1. Start the bot in your terminal:
   ```bash
   python bot.py
   ```
2. Navigate to your public submission channel on Discord and type:
   ```text
   !setup
   ```
   *(Requires Administrator permission. This spawns the permanent submission embed.)*
