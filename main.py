
from flask import Flask
from threading import Thread
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "ABI Bot Online"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

Thread(target=run_web).start()



TOKEN = os.getenv("DISCORD_TOKEN")

LOG_CHANNEL_ID = 1515642768527982653
HISTORY_FILE = "history.json"

RANK_ROLES = {
    "rookie": 1513566672844488716,
    "vanguard": 1513566820706029681,
    "elite": 1513569166395703506,
    "expert": 1513566960774807672,
    "master": 1513567054743994538,
    "ace": 1513567283379962046,
    "hero": 1513903640421859348,
    "legend": 1513567432189415625,
}

RANK_ORDER = {
    "rookie": 1,
    "vanguard": 2,
    "elite": 3,
    "expert": 4,
    "master": 5,
    "ace": 6,
    "hero": 7,
    "legend": 8
}


# =========================
# HISTORY
# =========================

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return {}

    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_history(data):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# =========================
# DROPDOWN
# =========================

class RankSelect(Select):

    def __init__(self, member):

        self.member = member

        options = [
            discord.SelectOption(label="Rookie", emoji="🥉", value="rookie"),
            discord.SelectOption(label="Vanguard", emoji="🛡️", value="vanguard"),
            discord.SelectOption(label="Elite", emoji="🔵", value="elite"),
            discord.SelectOption(label="Expert", emoji="🟣", value="expert"),
            discord.SelectOption(label="Master", emoji="🟡", value="master"),
            discord.SelectOption(label="Ace", emoji="🔴", value="ace"),
            discord.SelectOption(label="Hero", emoji="🔥", value="hero"),
            discord.SelectOption(label="Legend", emoji="💎", value="legend"),
        ]

        super().__init__(
            placeholder="Vyber ABI rank...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):

        rank = self.values[0]

        for role_id in RANK_ROLES.values():

            role = interaction.guild.get_role(role_id)

            if role and role in self.member.roles:
                await self.member.remove_roles(role)

        role = interaction.guild.get_role(RANK_ROLES[rank])

        if role:
            await self.member.add_roles(role)

        history = load_history()

        user_id = str(self.member.id)

        if user_id not in history:
            history[user_id] = []

        history[user_id].append({
            "rank": rank,
            "admin": str(interaction.user),
            "date": datetime.now().strftime("%d.%m.%Y %H:%M")
        })

        save_history(history)

        log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)

        if log_channel:

            embed = discord.Embed(
                title="📝 Rank Log",
                color=discord.Color.orange()
            )

            embed.add_field(
                name="Admin",
                value=interaction.user.mention,
                inline=False
            )

            embed.add_field(
                name="Hráč",
                value=self.member.mention,
                inline=False
            )

            embed.add_field(
                name="Nový rank",
                value=rank.title(),
                inline=False
            )

            await log_channel.send(embed=embed)

        await interaction.response.send_message(
            f"✅ {self.member.mention} získal rank **{rank.title()}**",
            ephemeral=True
        )


class RankView(View):

    def __init__(self, member):
        super().__init__(timeout=60)
        self.add_item(RankSelect(member))


# =========================
# BOT
# =========================

class MyClient(discord.Client):

    def __init__(self):

        intents = discord.Intents.default()
        intents.members = True

        super().__init__(intents=intents)

        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):

        synced = await self.tree.sync()

        print(f"Synced {len(synced)} commands")

        for cmd in synced:
            print(f"- {cmd.name}")


client = MyClient()


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")


# =========================
# SETRANK
# =========================

@client.tree.command(
    name="setrank",
    description="Nastaví ABI rank hráči"
)
async def setrank(
    interaction: discord.Interaction,
    member: discord.Member
):

    if not interaction.user.guild_permissions.administrator:

        await interaction.response.send_message(
            "❌ Pouze administrátoři.",
            ephemeral=True
        )
        return

    await interaction.response.send_message(
        f"Vyber rank pro {member.mention}",
        view=RankView(member),
        ephemeral=True
    )


# =========================
# RANK
# =========================

@client.tree.command(
    name="rank",
    description="Zobrazí rank hráče"
)
async def rank(
    interaction: discord.Interaction,
    member: discord.Member = None
):

    if member is None:
        member = interaction.user

    current_rank = None

    for rank_name, role_id in RANK_ROLES.items():

        role = interaction.guild.get_role(role_id)

        if role and role in member.roles:
            current_rank = rank_name

    if not current_rank:

        await interaction.response.send_message(
            f"{member.mention} nemá žádný ABI rank."
        )
        return

    embed = discord.Embed(
        title="🏅 ABI Rank",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="Hráč",
        value=member.mention,
        inline=False
    )

    embed.add_field(
        name="Rank",
        value=current_rank.title(),
        inline=False
    )

    await interaction.response.send_message(embed=embed)


# =========================
# STATS
# =========================

@client.tree.command(
    name="stats",
    description="Statistiky ranků"
)
async def stats(interaction: discord.Interaction):

    embed = discord.Embed(
        title="📊 ABI Rank Statistiky",
        color=discord.Color.blue()
    )

    for rank_name, role_id in RANK_ROLES.items():

        role = interaction.guild.get_role(role_id)

        count = len(role.members) if role else 0

        embed.add_field(
            name=rank_name.title(),
            value=f"{count} hráčů",
            inline=True
        )

    await interaction.response.send_message(embed=embed)


# =========================
# HISTORY
# =========================

@client.tree.command(
    name="history",
    description="Historie ranků hráče"
)
async def history(
    interaction: discord.Interaction,
    member: discord.Member
):

    if not interaction.user.guild_permissions.administrator:

        await interaction.response.send_message(
            "❌ Pouze administrátoři.",
            ephemeral=True
        )
        return

    data = load_history()

    user_id = str(member.id)

    if user_id not in data:

        await interaction.response.send_message(
            "Žádná historie."
        )
        return

    embed = discord.Embed(
        title=f"📜 Historie - {member.display_name}",
        color=discord.Color.purple()
    )

    text = ""

    for entry in data[user_id][-10:]:

        text += (
            f"**{entry['rank'].title()}**\n"
            f"👤 {entry['admin']}\n"
            f"📅 {entry['date']}\n\n"
        )

    embed.description = text

    await interaction.response.send_message(embed=embed)


# =========================
# LEADERBOARD
# =========================

@client.tree.command(
    name="leaderboard",
    description="Top hráči podle ranku"
)
async def leaderboard(interaction: discord.Interaction):

    await interaction.response.defer()

    leaderboard_data = []

    for member in interaction.guild.members:

        highest_rank = None
        highest_value = 0

        for rank_name, role_id in RANK_ROLES.items():

            role = interaction.guild.get_role(role_id)

            if role and role in member.roles:

                if RANK_ORDER[rank_name] > highest_value:
                    highest_value = RANK_ORDER[rank_name]
                    highest_rank = rank_name

        if highest_rank:
            leaderboard_data.append(
                (member, highest_rank, highest_value)
            )

    leaderboard_data.sort(
        key=lambda x: x[2],
        reverse=True
    )

    embed = discord.Embed(
        title="🏆 Arena Breakout Infinite Leaderboard",
        color=discord.Color.gold()
    )

    medals = ["🥇", "🥈", "🥉"]

    text = ""

    for i, (member, rank_name, _) in enumerate(
        leaderboard_data[:10],
        start=1
    ):

        if i <= 3:
            place = medals[i - 1]
        else:
            place = f"`#{i}`"

        text += f"{place} {member.mention} — **{rank_name.title()}**\n"

    embed.description = text if text else "Nikdo nemá rank."

    await interaction.followup.send(embed=embed)


client.run(TOKEN)
