
"""
====================================================================
MODULE: bot.py (MAIN ENTRY POINT)
PURPOSE: Initializes the Discord bot, registers persistent views,
         listens for multi-part code messages, and provides !setup.
====================================================================
"""

import discord
from discord.ext import commands
import json
from ui_components import (
    active_projects,
    StartPanelView,
    FileManagerView,
    FinishIdkView,
    AdminReviewView,
    complete_current_file
)

# Load configuration settings from config.json
with open("config.json", "r", encoding="utf-8") as config_file:
    CONFIG = json.load(config_file)


class CodeSubmissionBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True  # Required to read pasted code in chat
        intents.members = True          # Required to grant roles and apply timeouts
        super().__init__(command_prefix=CONFIG["prefix"], intents=intents)

    async def setup_hook(self):
        """Registers all persistent UI views so buttons survive bot restarts."""
        self.add_view(StartPanelView(CONFIG))
        self.add_view(FileManagerView(CONFIG))
        self.add_view(FinishIdkView(CONFIG))
        self.add_view(AdminReviewView(CONFIG))

    async def on_ready(self):
        print(f"[SUCCESS] Bot connected as {self.user} (ID: {self.user.id})")

    async def on_message(self, message: discord.Message):
        """Captures incoming code messages inside active submission channels."""
        if message.author.bot:
            return

        project = active_projects.get(message.channel.id)
        if project and project["listening"] and message.author.id == project["author_id"]:
            raw_content = message.content

            # Automatically strip Discord markdown code block wrappers (```python ... ```)
            if raw_content.startswith("```") and raw_content.endswith("```"):
                lines = raw_content.split("\n")
                raw_content = "\n".join(lines[1:-1])

            # Enforce the 50,000 character limit per individual file
            max_chars = CONFIG["max_chars_per_file"]
            if len(project["buffer"]) + len(raw_content) > max_chars:
                await message.reply(f"❌ **Limit Exceeded!** This file would exceed the **{max_chars:,} character** limit.")
                return

            # Append chunk to buffer and acknowledge with a reaction
            project["buffer"] += raw_content + "\n"
            project["received_parts"] += 1
            await message.add_reaction("📥")

            # Auto-finalize if the user specified an exact number of parts
            if project["expected_parts"] > 0:
                if project["received_parts"] >= project["expected_parts"]:
                    await complete_current_file(message.channel, project, CONFIG)
                else:
                    await message.channel.send(
                        f"📥 Part **{project['received_parts']}/{project['expected_parts']}** received. Send the next part!",
                        delete_after=5
                    )

        await self.process_commands(message)


bot = CodeSubmissionBot()


@bot.command(name="setup")
@commands.has_permissions(administrator=True)
async def setup_panel(ctx: commands.Context):
    """Admin command to spawn the permanent submission embed in the current channel."""
    max_chars = CONFIG["max_chars_per_file"]
    embed = discord.Embed(
        title="📦 Code Submission & Verification",
        description=(
            "Want to submit a script or project? Click the button below to open your private workspace.\n\n"
            f"• **Capacity:** {max_chars:,} characters per file (multi-file supported).\n"
            "• **Extensions:** `.py`, `.js`, `.txt`, `.env`, `.json`, `.html`, `.css`.\n"
            "• **Verification:** Automatic syntax and security check before staff review."
        ),
        color=discord.Color.green()
    )
    await ctx.send(embed=embed, view=StartPanelView(CONFIG))
    await ctx.message.delete()


if __name__ == "__main__":
    bot.run(CONFIG["token"])
