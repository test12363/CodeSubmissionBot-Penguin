
"""
====================================================================
MODULE: ui_components.py (PART 1/3)
PURPOSE: Imports, active project storage, and initial submission modal.
====================================================================
"""

import discord
from discord import ui
import zipfile
import io
import re
from datetime import timedelta
from analyzer import analyze_code_file

# In-memory dictionary tracking active submission channels: {channel_id: project_dict}
active_projects = {}


# ====================================================================
# 1. INITIAL SUBMISSION MODAL (CREATES PRIVATE CHANNEL)
# ====================================================================
class ProjectSubmissionModal(ui.Modal, title="New Code Submission"):
    purpose = ui.TextInput(
        label="What is this project for? (Channel Name)",
        placeholder="e.g., music bot, auto role...",
        max_length=25
    )
    tags = ui.TextInput(
        label="Keywords (Tags)",
        placeholder="e.g., python, discord, api",
        max_length=100
    )
    description = ui.TextInput(
        label="Detailed Project Explanation",
        style=discord.TextStyle.paragraph,
        placeholder="Explain how your code works...",
        max_length=1000
    )

    def __init__(self, config: dict):
        super().__init__()
        self.config = config

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        category = guild.get_channel(self.config["category_id"])

        clean_purpose = re.sub(r'[^a-zA-Z0-9-]', '-', self.purpose.value.lower()).strip('-')
        clean_user = re.sub(r'[^a-zA-Z0-9-]', '', interaction.user.name.lower())
        channel_name = f"{clean_purpose}-{clean_user}"[:90]

        admin_1 = guild.get_role(self.config["admin_role_1_id"])
        admin_2 = guild.get_role(self.config["admin_role_2_id"])

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        if admin_1:
            overwrites[admin_1] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        if admin_2:
            overwrites[admin_2] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        channel = await guild.create_text_channel(name=channel_name, category=category, overwrites=overwrites)

        active_projects[channel.id] = {
            "author_id": interaction.user.id,
            "purpose": self.purpose.value,
            "tags": self.tags.value,
            "description": self.description.value,
            "files": {},
            "current_file": None,
            "buffer": "",
            "expected_parts": 0,
            "received_parts": 0,
            "listening": False
        }

        await interaction.response.send_message(f"✅ Your private workspace is ready: {channel.mention}", ephemeral=True)

        mentions = f"{interaction.user.mention} "
        if admin_1:
            mentions += f"{admin_1.mention} "
        if admin_2:
            mentions += f"{admin_2.mention}"

        embed = discord.Embed(
            title=f"🛠️ Project: {self.purpose.value}",
            description=(
                f"**Author:** {interaction.user.mention}\n"
                f"**Keywords:** `{self.tags.value}`\n"
                f"**Description:**\n{self.description.value}"
            ),
            color=discord.Color.blurple()
        )
        embed.add_field(name="Saved Files", value="*No files added yet.*", inline=False)

        await channel.send(content=mentions, embed=embed, view=FileManagerView(self.config))

  # ====================================================================
# 2. FILE CONFIGURATION MODAL (FILENAME & NUMBER OF PARTS)
# ====================================================================
class FileConfigModal(ui.Modal, title="File Configuration"):
    filename = ui.TextInput(
        label="File Name (without extension)",
        placeholder="e.g., main, config, index...",
        max_length=40
    )
    parts = ui.TextInput(
        label="How many parts is your code split into?",
        placeholder="Enter a number (e.g., 3) or type: idk",
        max_length=10
    )

    def __init__(self, extension: str, config: dict):
        super().__init__()
        self.extension = extension
        self.config = config

    async def on_submit(self, interaction: discord.Interaction):
        project = active_projects.get(interaction.channel.id)
        if not project:
            return await interaction.response.send_message("❌ Project not found.", ephemeral=True)

        clean_name = re.sub(r'[^a-zA-Z0-9_-]', '', self.filename.value) or "script"
        full_filename = ".env" if self.extension == ".env" else f"{clean_name}{self.extension}"

        parts_input = self.parts.value.strip().lower()
        if parts_input.isdigit() and int(parts_input) > 0:
            expected = int(parts_input)
            mode_info = f"in **{expected} part(s)**."
        else:
            expected = 0
            mode_info = "in **free mode (`idk`)**. Click **Finish File** when you are done pasting."

        project["current_file"] = full_filename
        project["buffer"] = ""
        project["expected_parts"] = expected
        project["received_parts"] = 0
        project["listening"] = True

        max_chars = self.config["max_chars_per_file"]
        view = FinishIdkView(self.config) if expected == 0 else None

        await interaction.response.send_message(
            f"✍️ **Recording `{full_filename}`** ({mode_info})\n"
            f"Paste your code in the chat now (Max **{max_chars:,} characters** for this file):",
            view=view
        )


# ====================================================================
# 3. EXTENSION DROPDOWN & FILE MANAGEMENT VIEWS
# ====================================================================
class ExtensionDropdown(ui.Select):
    def __init__(self, config: dict):
        self.config = config
        options = [
            discord.SelectOption(label=".py (Python)", value=".py", emoji="🐍"),
            discord.SelectOption(label=".js (JavaScript)", value=".js", emoji="📜"),
            discord.SelectOption(label=".txt (Text)", value=".txt", emoji="📄"),
            discord.SelectOption(label=".env (Environment)", value=".env", emoji="⚙️"),
            discord.SelectOption(label=".json (Data)", value=".json", emoji="🔧"),
            discord.SelectOption(label=".html (Web)", value=".html", emoji="🌐"),
            discord.SelectOption(label=".css (Stylesheet)", value=".css", emoji="🎨"),
        ]
        super().__init__(placeholder="Select the file extension...", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(FileConfigModal(self.values[0], self.config))


class ExtensionView(ui.View):
    def __init__(self, config: dict):
        super().__init__(timeout=120)
        self.add_item(ExtensionDropdown(config))


class FinishIdkView(ui.View):
    def __init__(self, config: dict):
        super().__init__(timeout=None)
        self.config = config

    @ui.button(label="Finish File", style=discord.ButtonStyle.success, emoji="🛑", custom_id="finish_idk_btn")
    async def finish_idk_button(self, interaction: discord.Interaction, button: ui.Button):
        project = active_projects.get(interaction.channel.id)
        if not project or interaction.user.id != project["author_id"]:
            return await interaction.response.send_message("❌ Only the project author can do this.", ephemeral=True)

        await complete_current_file(interaction.channel, project, self.config, interaction)


class FileManagerView(ui.View):
    def __init__(self, config: dict):
        super().__init__(timeout=None)
        self.config = config

    @ui.button(label="Add a File", style=discord.ButtonStyle.primary, emoji="📄", custom_id="add_file_btn")
    async def add_file_button(self, interaction: discord.Interaction, button: ui.Button):
        project = active_projects.get(interaction.channel.id)
        if not project or interaction.user.id != project["author_id"]:
            return await interaction.response.send_message("❌ Only the project author can add files.", ephemeral=True)
        if project["listening"]:
            return await interaction.response.send_message("⚠️ Please finish the current file first.", ephemeral=True)

        await interaction.response.send_message("Choose your file format:", view=ExtensionView(self.config), ephemeral=True)

    @ui.button(label="Submit to Admins", style=discord.ButtonStyle.success, emoji="✅", custom_id="submit_admins_btn")
    async def submit_admins_button(self, interaction: discord.Interaction, button: ui.Button):
        project = active_projects.get(interaction.channel.id)
        if not project or interaction.user.id != project["author_id"]:
            return await interaction.response.send_message("❌ Only the project author can submit.", ephemeral=True)
        if not project["files"]:
            return await interaction.response.send_message("❌ You must add at least one file before submitting.", ephemeral=True)

        reports = []
        for fname, code in project["files"].items():
            reports.append(f"**📄 `{fname}` ({len(code):,} characters):**\n{analyze_code_file(fname, code)}")

        embed = discord.Embed(
            title="🔍 Code Verification Complete — Awaiting Staff Review",
            description="\n\n".join(reports)[:4000],
            color=discord.Color.gold()
        )
        await interaction.response.send_message(embed=embed, view=AdminReviewView(self.config))


# ====================================================================
# 4. ADMIN DECISION PANEL (ACCEPT = ROLE + ZIP | DECLINE = MUTE + DELETE)
# ====================================================================
class AdminReviewView(ui.View):
    def __init__(self, config: dict):
        super().__init__(timeout=None)
        self.config = config

    def has_admin_access(self, member: discord.Member) -> bool:
        user_roles = [r.id for r in member.roles]
        return (
            self.config["admin_role_1_id"] in user_roles
            or self.config["admin_role_2_id"] in user_roles
            or member.guild_permissions.administrator
        )

    @ui.button(label="Accept", style=discord.ButtonStyle.success, emoji="✔️", custom_id="admin_accept_btn")
    async def accept_button(self, interaction: discord.Interaction, button: ui.Button):
        if not self.has_admin_access(interaction.user):
            return await interaction.response.send_message("❌ Restricted to staff administrators.", ephemeral=True)

        project = active_projects.get(interaction.channel.id)
        if not project:
            return await interaction.response.send_message("❌ Project not found or already processed.", ephemeral=True)

        guild = interaction.guild
        author = guild.get_member(project["author_id"])
        reward_role = guild.get_role(self.config["reward_role_id"])

        if author and reward_role:
            try:
                await author.add_roles(reward_role)
            except discord.Forbidden:
                pass

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for fname, code in project["files"].items():
                zip_file.writestr(fname, code)
        zip_buffer.seek(0)

        zip_attachment = discord.File(fp=zip_buffer, filename=f"{interaction.channel.name}.zip")

        await interaction.response.send_message(
            f"✅ **Project accepted by {interaction.user.mention}!**\n"
            f"Role granted: {reward_role.mention if reward_role else 'None'}.\n"
            f"Here is the complete project archive:",
            file=zip_attachment
        )
        del active_projects[interaction.channel.id]

    @ui.button(label="Decline", style=discord.ButtonStyle.danger, emoji="✖️", custom_id="admin_decline_btn")
    async def decline_button(self, interaction: discord.Interaction, button: ui.Button):
        if not self.has_admin_access(interaction.user):
            return await interaction.response.send_message("❌ Restricted to staff administrators.", ephemeral=True)

        project = active_projects.get(interaction.channel.id)
        guild = interaction.guild
        mute_mins = self.config["mute_duration_minutes"]

        if project:
            author = guild.get_member(project["author_id"])
            if author:
                try:
                    await author.timeout(timedelta(minutes=mute_mins), reason=f"Project declined by {interaction.user.name}")
                except discord.Forbidden:
                    pass
            del active_projects[interaction.channel.id]

        await interaction.response.send_message(f"✖️ Project declined. Author has been muted for {mute_mins} minutes. Deleting channel...")
        await interaction.channel.delete()


# ====================================================================
# 5. START PANEL VIEW & FILE FINALIZATION HELPER
# ====================================================================
class StartPanelView(ui.View):
    def __init__(self, config: dict):
        super().__init__(timeout=None)
        self.config = config

    @ui.button(label="Submit a Project", style=discord.ButtonStyle.success, emoji="📦", custom_id="open_submission_btn")
    async def open_submission(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(ProjectSubmissionModal(self.config))


async def complete_current_file(channel: discord.TextChannel, project: dict, config: dict, interaction: discord.Interaction = None):
    fname = project["current_file"]
    code = project["buffer"]
    max_chars = config["max_chars_per_file"]

    project["files"][fname] = code
    project["listening"] = False
    project["current_file"] = None
    project["buffer"] = ""

    analysis = analyze_code_file(fname, code)
    summary = (
        f"✅ **File `{fname}` saved ({len(code):,} / {max_chars:,} characters)!**\n\n"
        f"**🔍 Automatic Code Analysis:**\n{analysis}\n\n"
        f"What would you like to do next?"
    )

    if interaction:
        await interaction.response.send_message(summary, view=FileManagerView(config))
    else:
        await channel.send(summary, view=FileManagerView(config))
