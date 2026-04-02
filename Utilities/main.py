# ===================== IMPORTS =====================
import os
import json
import discord
import requests
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button, Modal, TextInput
import pandas as pd
from enum import Enum
from datetime import datetime
# ===================== CONFIG =====================
TOKEN = "PUT_YOUR_TOKEN_HERE"  # DO NOT LEAK
GUILD_ID = 1454759644630094017
DATA_FILE = "data.json"

CATEGORY_MAP = {
    "Order Livery": 1455208530825973926,
    "Order ELS": 1455208548211495088,
    "Order Clothing": 1455208567513677886,
    "Order Graphics": 1455208602985037824,
    "Order Discord Server": 1455208627714527313,
    "Order Bots": 1455208644181229589,
}

ROLE_MAP = {
    "Order Livery": 1455534453312061664,
    "Order ELS": 1455534478112981073,
    "Order Clothing": 1455534493908865126,
    "Order Graphics": 1455534537701593141,
    "Order Discord Server": 1455534516197130250,
    "Order Bots": 1455534561382371348,
}

ROLE_IDS = [
    1457277167615610882,  # DJ
    1457277197164478588,  # D
    1457277214537285632,  # SD
    1457277250713030820,  # LD
    1457277281520062484,  # TA
    1457277332778913874,  # JA
    1457277355927146641,  # A
    1457277396683325515,  # SA
    1457277414651727924,  # HA
    1457277437602824225,  # JM
    1457277458192535697,  # M
    1457277480674005224,  # SM
    1457277502933438584,  # CM
    1457277527352672277,  # EXE
    1457277553742970951,  # OWN
]


# Data --
def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump({
                "ticket_counter": 0,
                "claims": {}
            }, f, indent=4)

    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def next_ticket():
    data = load_data()
    data["ticket_counter"] += 1
    save_data(data)
    return f"{data['ticket_counter']:04d}"

if os.path.exists('infractions.csv'):
    infraction_df = pd.read_csv('infractions.csv', dtype={'MessageID': str})  # Ensure MessageID is read as string
    if not infraction_df.empty:
        icount = infraction_df['InfractionID'].max()
else:
    infraction_df = pd.DataFrame(columns=[
        'InfractionID',
        'staffID',
        'staffMention',
        'InfractionType',
        'Reason',
        'IssuedBy',
        'IssuedByID',
        'MessageID',
        'staff Notes',
        'User Notes'
    ])
    icount = 0

def save_infractions():
    infraction_df.to_csv('infractions.csv', index=False)

class infraction_type(Enum):
    warning = 'Warning'
    strike = 'Strike'
    demotion = 'Demotion'
    termination = 'Termination'
    blacklist = 'Blacklist'

infraction_channel_id = 1457274907317637294 # *
infraction_permissions_role = 1455199885035966494 # * 

PROMOTION_FILE = "promotions.json"

def load_promotions():
    if not os.path.exists(PROMOTION_FILE):
        return {}
    with open(PROMOTION_FILE, "r") as f:
        return json.load(f)

def save_promotions(data):
    with open(PROMOTION_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_current_role_index(member: discord.Member):
    for role in member.roles:
        if role.id in ROLE_IDS:
            return ROLE_IDS.index(role.id)
    return None

def get_role(guild, role_id):
    return guild.get_role(role_id)

# -----
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

class MyBot(commands.Bot):
    async def setup_hook(self):
        self.add_view(TicketView())
        self.tree.add_command(promotion_group, guild=discord.Object(id=GUILD_ID))
        await self.tree.sync(guild=discord.Object(id=GUILD_ID))

bot = MyBot(command_prefix="!", intents=intents)



contracts = {}

class ContractView(View):
    def __init__(self, contract_id: int):
        super().__init__(timeout=None)
        self.contract_id = contract_id

    @discord.ui.button(
        label="Accept Contract",
        style=discord.ButtonStyle.success,
        emoji="✅"
    )
    async def accept(
        self,
        interaction: discord.Interaction,
        button: Button
    ):
        contract = contracts[self.contract_id]

        if interaction.user.id != contract["customer_id"]:
            return await interaction.response.send_message(
                "❌ Only the customer can accept this contract.",
                ephemeral=True
            )

        embed = contract["embed"]
        embed.add_field(
            name="Status",
            value=f"🟢 **Accepted by {interaction.user.mention}**",
            inline=False
        )
        embed.color = discord.Color.green()

        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.send_message(
            "✅ Contract accepted.",
            ephemeral=True
        )

    @discord.ui.button(
        label="Reject Contract",
        style=discord.ButtonStyle.danger,
        emoji="❌"
    )
    async def reject(
        self,
        interaction: discord.Interaction,
        button: Button
    ):
        contract = contracts[self.contract_id]

        if interaction.user.id != contract["customer_id"]:
            return await interaction.response.send_message(
                "❌ Only the customer can reject this contract.",
                ephemeral=True
            )

        embed = contract["embed"]
        embed.add_field(
            name="Status",
            value=f"🔴 **Rejected by {interaction.user.mention}**",
            inline=False
        )
        embed.color = discord.Color.red()

        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.send_message(
            "❌ Contract rejected.",
            ephemeral=True
        )

@bot.tree.command(
    name="contract",
    description="Send an order confirmation contract",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(
    customer="Customer",
    designer="Designer",
    designs="Number of designs",
    days="Estimated time (days)",
    subtotal="Sub-total price",
    final_price="Final price"
)
async def contract(
    interaction: discord.Interaction,
    customer: discord.Member,
    designer: discord.Member,
    designs: int,
    days: int,
    subtotal: int,
    final_price: int
):
    embed = discord.Embed(
        title="Evil Creations Order Confirmation",
        description=(
            f"Hey there, {customer.mention}!\n\n"
            "Your designer has requested an order confirmation.\n"
            "View the details below. Please review and accept or reject this contract."
        ),
        color=0xf5a623
    )

    embed.add_field(
        name="👤 Customer",
        value=customer.mention,
        inline=True
    )
    embed.add_field(
        name="🎨 Designer",
        value=designer.mention,
        inline=True
    )
    embed.add_field(
        name="⭐ Designs",
        value=str(designs),
        inline=True
    )

    embed.add_field(
        name="⏱ Estimated Time",
        value=f"{days}d",
        inline=True
    )
    embed.add_field(
        name="💰 Sub-Total",
        value=str(subtotal),
        inline=True
    )
    embed.add_field(
        name="💵 Final Price",
        value=str(final_price),
        inline=True
    )

    embed.set_footer(
        text=(
            "Please review the contract details above and click Accept or Reject below.\n"
        )
    )

    contract_id = len(contracts) + 1
    contracts[contract_id] = {
        "customer_id": customer.id,
        "embed": embed
    }

    await interaction.response.send_message(
        embed=embed,
        view=ContractView(contract_id)
    )


# ===================== TICKETS =====================
class TicketSelect(discord.ui.Select):
    def __init__(self):
        super().__init__(
            placeholder="Choose a service",
            options=[
                discord.SelectOption(label=k, value=k)
                for k in CATEGORY_MAP
            ],
            custom_id="ticket-select"
        )

    async def callback(self, interaction: discord.Interaction):
        choice = self.values[0]
        guild = interaction.guild

        category = guild.get_channel(CATEGORY_MAP[choice])
        role = guild.get_role(ROLE_MAP[choice])

        channel = await guild.create_text_channel(
            name=f"🔴-{interaction.user.name}-{next_ticket()}",
            category=category,
            overwrites={
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                interaction.user: discord.PermissionOverwrite(view_channel=True),
                guild.me: discord.PermissionOverwrite(view_channel=True),
                role: discord.PermissionOverwrite(view_channel=True)
            }
        )

        embed = discord.Embed(
            title="Order Ticket",
            description="Thank you for choosing Evil Creations. Please fill out the following format accurately and make sure to be as clear as possible.\n\n**Format:**\n```Order Description:\nBudget:\nDeadline:\nReferences:```",
            color=discord.Color.green()
        )

        await channel.send(content=role.mention, embed=embed)

        await interaction.response.send_message(
            f"🎟 Ticket created: {channel.mention}",
            ephemeral=True
        )


class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())

# ===================== CLAIM / UNCLAIM =====================
@bot.tree.command(name="claimticket", guild=discord.Object(id=GUILD_ID))
async def claimticket(interaction: discord.Interaction):
    data = load_data()
    cid = str(interaction.channel.id)

    if cid in data["claims"]:
        return await interaction.response.send_message("❌ Already claimed.", ephemeral=True)

    data["claims"][cid] = interaction.user.id
    save_data(data)

    await interaction.channel.edit(name=interaction.channel.name.replace("🔴", "🟢"))
    await interaction.response.send_message(f"✅ Claimed by {interaction.user.mention}")

@bot.tree.command(name="unclaimticket", guild=discord.Object(id=GUILD_ID))
async def unclaimticket(interaction: discord.Interaction):
    data = load_data()
    cid = str(interaction.channel.id)

    if data["claims"].get(cid) != interaction.user.id:
        return await interaction.response.send_message("❌ Not your ticket.", ephemeral=True)

    del data["claims"][cid]
    save_data(data)

    await interaction.channel.edit(name=interaction.channel.name.replace("🟢", "🔴"))
    await interaction.response.send_message("🔓 Ticket unclaimed")

# ===================== PAYMENT CHECK =====================
def get_roblox_user_id(username):
    r = requests.post(
        "https://users.roblox.com/v1/usernames/users",
        json={"usernames": [username]}
    )
    data = r.json().get("data")
    return data[0]["id"] if data else None

def owns_gamepass(uid, gid):
    r = requests.get(f"https://inventory.roblox.com/v1/users/{uid}/items/GamePass/{gid}")
    return bool(r.json().get("data"))

@bot.tree.command(name="fetch_payment_status", guild=discord.Object(id=GUILD_ID))
async def fetch_payment_status(
    interaction: discord.Interaction,
    roblox_username: str,
    gamepass_id: int
):
    uid = get_roblox_user_id(roblox_username)
    if not uid:
        return await interaction.response.send_message(
            "❌ Roblox user not found.", ephemeral=True
        )

    paid = owns_gamepass(uid, gamepass_id)
    await interaction.response.send_message(
        embed=discord.Embed(
            title="Payment Status",
            description=f"**Status:** {'🟢 Paid' if paid else '🔴 Not Paid'}",
            color=discord.Color.green() if paid else discord.Color.red()
        )
    )

# ===================== TAX =====================
@bot.tree.command(name="tax", guild=discord.Object(id=GUILD_ID))
async def tax(interaction: discord.Interaction, amount: int, designs: int):

    if 0 >= designs:
        await interaction.response.send_message('Invalid order amount.')

    tax = int(amount/0.7)
    if designs <10 and designs >=1:
        preset = 0.05
    elif designs >= 11 and designs <25:
        preset = 0.10
    else:
        preset = 0.25
    

    dtax = int(tax*preset)

    Embed = discord.Embed(
        title='Tax calculator',
        color=discord.Color.gold()
    )

    Embed.add_field(name='Standard Tax', value=tax,inline=True)
    Embed.add_field(name='Designer Tax', value=dtax,inline=True)
    Embed.add_field(name='Total', value=tax+dtax,inline=False)
    
    await interaction.response.send_message(embed=Embed, ephemeral=True)

# ===================== USER ADD =====================
@bot.tree.command(name="useradd", guild=discord.Object(id=GUILD_ID))
async def useradd(interaction: discord.Interaction, user: discord.Member):
    await interaction.channel.set_permissions(
        user, view_channel=True, send_messages=True
    )
    await interaction.response.send_message(f"✅ {user.mention} added to ticket.")

@bot.tree.command(name='infraction', description='Log an infraction.', guild=discord.Object(id=GUILD_ID))
@app_commands.describe(staff='staff to infract.', infraction='Infraction type', reason='Reason for infraction.')
async def infraction(interaction: discord.Interaction, staff: discord.User, infraction: infraction_type, reason: str):
    global icount, infraction_df

    infraction_channel = interaction.guild.get_channel(infraction_channel_id)
    icount += 1

    needed_role = interaction.guild.get_role(infraction_permissions_role)
    member = interaction.guild.get_member(interaction.user.id)
    
    if needed_role not in member.roles:
        await interaction.response.send_message('Missing permissions. Contact department administration if you think this is a mistake.')
        return

    embed = discord.Embed(
        title=f'__Infraction Log #{icount}__',
        description=f'**staff**\n{staff.mention}\n\n**Infraction**\n{infraction.value}\n\n**Reason**\n{reason}\n\n**Issued by**\n{interaction.user.mention}',
        color=discord.Color.red()
    )
    to_userembed = discord.Embed(
        title=f'__Infraction Log #{icount}__',
        description=f'**staff**\n{staff.mention}\n\n**Infraction**\n{infraction.value}\n\n**Reason**\n{reason}',
        color=discord.Color.red()
    )

    infraction_msg = await infraction_channel.send(embed=embed)
    await interaction.response.send_message('Infraction Logged!', ephemeral=True)
    thread = await infraction_msg.create_thread(
        name=f'Infraction #{icount} - Evidence'
    )
    try:
        await staff.send(embed=to_userembed)
    except discord.HTTPException as e:
        if e.code == 50007:
            await interaction.followup.send(f"`Automatic DM failed. Please DM the user manually.`")
        else:
            raise  # re-raise the exception if it's not error 50007

    new_entry = {
        'InfractionID': icount,
        'staffID': staff.id,
        'staffMention': staff.mention,
        'InfractionType': infraction.value,
        'Reason': reason,
        'IssuedBy': interaction.user.mention,
        'IssuedByID': interaction.user.id,
        'MessageID': str(infraction_msg.id)  # Store as string
    }

    infraction_df = pd.concat([infraction_df, pd.DataFrame([new_entry])], ignore_index=True)
    save_infractions()
@bot.tree.command(name='infractionvoid', description='Void an infraction.', guild=discord.Object(id=GUILD_ID))
@app_commands.describe(infraction_id='Infraction ID.', reason='Reason for voiding the infraction.')
async def infractionvoid(interaction: discord.Interaction, infraction_id: int, reason: str):
    await interaction.response.defer(ephemeral=True)
    global infraction_df

    needed_role = interaction.guild.get_role(infraction_permissions_role)
    member = interaction.guild.get_member(interaction.user.id)
    
    if needed_role not in member.roles:
        await interaction.response.send_message('Missing permissions. Contact department administration if you think this is a mistake.')

    if infraction_id in infraction_df['InfractionID'].values:
        infraction_channel = await interaction.guild.fetch_channel(infraction_channel_id)
        row = infraction_df[infraction_df['InfractionID'] == infraction_id].iloc[0]

        msg_id = int(row['MessageID'])
        try:
            msg = await infraction_channel.fetch_message(msg_id)
        except discord.NotFound:
            await interaction.followup.send('Original infraction message not found.', ephemeral=True)
            return

        embed = discord.Embed(
            title=f'__Infraction #{infraction_id}__',
            description=f'**__staff__**\n{row["staffMention"]}\n\n**__Infraction Type__**\n~~{row["InfractionType"]}~~\n\n**__Reason__**\n{row["Reason"]}\n\n-# Voided by {interaction.user.mention}',
            color=discord.Color.red()
        )

        await msg.edit(embed=embed)

        infraction_df.loc[infraction_df['InfractionID'] == infraction_id, 'InfractionType'] = 'VOIDED'
        infraction_df.loc[infraction_df['InfractionID'] == infraction_id, 'Reason'] = f'Voided: {reason}'
        save_infractions()

        await interaction.followup.send(f'Infraction {infraction_id} voided successfully!', ephemeral=True)
    else:
        await interaction.followup.send(f'No infraction with ID {infraction_id} found.', ephemeral=True)

# Edit Infraction Command
@bot.tree.command(name='infractionedit', description='Edit an infraction.', guild=discord.Object(id=GUILD_ID))
@app_commands.describe(infraction_id='Infraction ID.', infraction='New infraction type.', reason='New reason.')
async def infractionedit(interaction: discord.Interaction, infraction_id: int, infraction: infraction_type, reason: str):
    await interaction.response.defer(ephemeral=True)
    global infraction_df

    needed_role = interaction.guild.get_role(infraction_permissions_role)
    member = interaction.guild.get_member(interaction.user.id)
    
    if needed_role not in member.roles:
        await interaction.response.send_message('Missing permissions. Contact department administration if you think this is a mistake.')

    if infraction_id in infraction_df['InfractionID'].values:
        infraction_channel = await interaction.guild.fetch_channel(infraction_channel_id)
        row = infraction_df[infraction_df['InfractionID'] == infraction_id].iloc[0]

        msg_id = int(row['MessageID'])
        try:
            msg = await infraction_channel.fetch_message(msg_id)
        except discord.NotFound:
            await interaction.followup.send('Original infraction not found.', ephemeral=True)
            return

        embed = discord.Embed(
            title=f'__Infraction #{infraction_id}__',
            description=f'**__staff__**\n{row["staffMention"]}\n\n**__Infraction__**\n{infraction.value}\n\n**__Reason__**\n{reason}\n\n**__Issued by__**\n{row["IssuedBy"]}\n\n-# Edited by {interaction.user.mention}',
            color=discord.Color.red()
        )

        await msg.edit(embed=embed)

        infraction_df.loc[infraction_df['InfractionID'] == infraction_id, 'InfractionType'] = infraction.value
        infraction_df.loc[infraction_df['InfractionID'] == infraction_id, 'Reason'] = reason
        save_infractions()

        await interaction.followup.send(f'Infraction {infraction_id} has been edited successfully.', ephemeral=True)
    else:
        await interaction.followup.send(f'No infraction with ID {infraction_id} found.', ephemeral=True)

# Infraction History Command
@bot.tree.command(name='infractionhistory', description='Check the infraction history of a staff.', guild=discord.Object(id=GUILD_ID))
@app_commands.describe(staff='staff to check history.')
async def infractionhistory(interaction: discord.Interaction, staff: discord.User):
    user_df = infraction_df[infraction_df['staffID'] == staff.id]

    if user_df.empty:
        embed = discord.Embed(
            title=f'Infraction History of {staff}',
            description='No infraction history.',
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    description = ''
    for _, row in user_df.iterrows():
        description += f"**Infraction ID:** {row['InfractionID']}\n**Infraction:** {row['InfractionType']}\n**Reason:** {row['Reason']}\n**Issued by:** {row['IssuedBy']}\n\n"

    embed = discord.Embed(
        title=f'Infraction History of {staff}',
        description=description,
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

class PromotionGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="promotion", description="Promotion management")

promotion_group = PromotionGroup()

RANK_CHOICES_STR = [
    app_commands.Choice(name="Junior Designer", value="1457277167615610882"),
    app_commands.Choice(name="Designer", value="1457277197164478588"),
    app_commands.Choice(name="Senior Designer", value="1457277214537285632"),
    app_commands.Choice(name="Lead Designer", value="1457277250713030820"),
    app_commands.Choice(name="Trial Admin", value="1457277281520062484"),
    app_commands.Choice(name="Junior Admin", value="1457277332778913874"),
    app_commands.Choice(name="Admin", value="1457277355927146641"),
    app_commands.Choice(name="Senior Admin", value="1457277396683325515"),
    app_commands.Choice(name="Head Admin", value="1457277414651727924"),
    app_commands.Choice(name="Junior Manager", value="1457277437602824225"),
    app_commands.Choice(name="Manager", value="1457277458192535697"),
    app_commands.Choice(name="Senior Manager", value="1457277480674005224"),
    app_commands.Choice(name="Community Manager", value="1457277502933438584"),
    app_commands.Choice(name="Executive", value="1457277527352672277"),
    app_commands.Choice(name="Owner", value="1457277553742970951"),
]


@promotion_group.command(name="issue", description="Promote a user")
@app_commands.describe(
    member="Member to promote",
    from_rank="Current rank",
    to_rank="New rank",
    reason="Reason for promotion"
)
@app_commands.choices(from_rank=RANK_CHOICES_STR, to_rank=RANK_CHOICES_STR)
async def promotion_issue(
    interaction: discord.Interaction,
    member: discord.Member,
    from_rank: str,  # Changed to str
    to_rank: str,    # Changed to str
    reason: str
):
    guild = interaction.guild
    promotions = load_promotions()

    from_role_id = int(from_rank)  # Convert string to int
    to_role_id = int(to_rank)      # Convert string to int

    from_index = ROLE_IDS.index(from_role_id)
    to_index = ROLE_IDS.index(to_role_id)

    if to_index <= from_index:
        await interaction.response.send_message(
            "❌ `To Rank` must be higher than `From Rank`.",
            ephemeral=True
        )
        return

    old_role = guild.get_role(from_role_id)
    new_role = guild.get_role(to_role_id)

    if not old_role or not new_role:
        await interaction.response.send_message(
            "❌ One or more roles were not found.",
            ephemeral=True
        )
        return

    if old_role not in member.roles:
        await interaction.response.send_message(
            f"❌ User does not have **{old_role.name}**.",
            ephemeral=True
        )
        return

    await member.remove_roles(old_role)
    await member.add_roles(new_role)

    promotions[str(member.id)] = {
        "old_role": old_role.id,
        "new_role": new_role.id,
        "by": interaction.user.id,
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat()
    }

    save_promotions(promotions)

    embed = discord.Embed(
        title="✅ Promotion Issued",
        color=discord.Color.green()
    )
    embed.add_field(name="User", value=member.mention, inline=False)
    embed.add_field(name="From", value=old_role.name, inline=True)
    embed.add_field(name="To", value=new_role.name, inline=True)
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.set_footer(text=f"Issued by {interaction.user}")

    await interaction.response.send_message(embed=embed)

@promotion_group.command(name="view", description="View a user's promotion history")
@app_commands.describe(member="Member to view")
async def promotions_view(
    interaction: discord.Interaction,
    member: discord.Member
):
    promotions = load_promotions()
    data = promotions.get(str(member.id))

    if not data:
        await interaction.response.send_message(
            "❌ No promotions found for this user.",
            ephemeral=True
        )
        return

    guild = interaction.guild
    old_role = get_role(guild, data["old_role"])
    new_role = get_role(guild, data["new_role"])

    embed = discord.Embed(
        title="📜 Promotion Record",
        color=discord.Color.blurple()
    )
    embed.add_field(name="User", value=member.mention)
    embed.add_field(name="From", value=old_role.name)
    embed.add_field(name="To", value=new_role.name)
    embed.add_field(name="Reason", value=data["reason"])
    embed.add_field(
        name="Issued By",
        value=f"<@{data['by']}>"
    )
    embed.add_field(
        name="Date",
        value=data["timestamp"]
    )

    await interaction.response.send_message(embed=embed,ephemeral=True)
@promotion_group.command(name="void", description="Void a promotion and revert rank")
@app_commands.describe(member="Member to revert")
async def promotions_void(
    interaction: discord.Interaction,
    member: discord.Member
):
    promotions = load_promotions()
    data = promotions.get(str(member.id))

    if not data:
        await interaction.response.send_message(
            "❌ No promotion found to void.",
            ephemeral=True
        )
        return

    guild = interaction.guild
    new_role = get_role(guild, data["new_role"])
    old_role = get_role(guild, data["old_role"])

    await member.remove_roles(new_role)
    await member.add_roles(old_role)

    promotions.pop(str(member.id))
    save_promotions(promotions)

    embed = discord.Embed(
        title="🗑️ Promotion Voided",
        color=discord.Color.red()
    )
    embed.add_field(name="User", value=member.mention)
    embed.add_field(name="Reverted To", value=old_role.name)

    await interaction.response.send_message(embed=embed)


ROBLOX_API_KEY = ""
ROBLOX_GROUP_ID = 33724769

def get_roblox_user_id(username: str):
    r = requests.post(
        "https://users.roblox.com/v1/usernames/users",
        json={
            "usernames": [username],
            "excludeBannedUsers": True
        }
    )
    data = r.json().get("data")
    return data[0]["id"] if data else None

def get_membership_id(user_id: int):
    url = f"https://apis.roblox.com/cloud/v2/groups/{ROBLOX_GROUP_ID}/memberships:getMembership"
    headers = {
        "x-api-key": ROBLOX_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {"userId": str(user_id)}
    r = requests.post(url, headers=headers, json=payload)
    print("STATUS:", r.status_code)
    print("BODY:", r.text)
    if r.status_code != 200:
        return None
    data = r.json()
    return data.get("membershipId")


def set_group_rank(user_id: int, role_id: int):
    membership_id = get_membership_id(user_id)
    if not membership_id:
        return 404, "User is not a member of the group."

    url = (
        f"https://apis.roblox.com/cloud/v2/groups/"
        f"{ROBLOX_GROUP_ID}/memberships/{membership_id}:setRole"
    )

    headers = {
        "x-api-key": ROBLOX_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "roleId": str(role_id)
    }

    r = requests.patch(url, headers=headers, json=payload)
    return r.status_code, r.text


@bot.tree.command(
    name="setrank",
    description="Set a user's Roblox group rank",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(
    roblox_username="Roblox username",
    role_id="Roblox group role ID"
)
async def setrank(
    interaction: discord.Interaction,
    roblox_username: str,
    role_id: int
):
    await interaction.response.defer(ephemeral=True)

    # 🔒 Permission check (reuse your admin role)
    required_role = interaction.guild.get_role(infraction_permissions_role)
    if required_role not in interaction.user.roles:
        return await interaction.followup.send(
            "❌ You do not have permission to use this command.",
            ephemeral=True
        )

    user_id = get_roblox_user_id(roblox_username)
    if not user_id:
        return await interaction.followup.send(
            "❌ Roblox user not found.",
            ephemeral=True
        )

    status, response = set_group_rank(user_id, role_id)

    if status == 200:
        embed = discord.Embed(
            title="✅ Rank Updated",
            color=discord.Color.green()
        )
        embed.add_field(name="User", value=roblox_username)
        embed.add_field(name="Role ID", value=str(role_id))
        embed.set_footer(text="Roblox Open Cloud API")

        await interaction.followup.send(embed=embed, ephemeral=True)
    else:
        await interaction.followup.send(
            f"❌ Failed to update rank.\n```{response}```",
            ephemeral=True
        )

@bot.tree.command(
    name="orderlog",
    description="Log a completed order",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(
    customer="Customer who ordered",
    designer="Designer who worked on it",
    price="Final price (after tax)",
    notes="Extra notes (optional)"
)
async def orderlog(
    interaction: discord.Interaction,
    customer: discord.Member,
    designer: discord.Member,
    price: int,
    notes: str = "None"
):
    channel = interaction.guild.get_channel(1457274907317637294)
    if channel is None:
        return await interaction.response.send_message(
            "❌ Order log channel not found. Contact administration.",
            ephemeral=True
        )

    # 🔍 Detect order type from customer's roles
    product = None
    for role_name, role_id in ROLE_MAP.items():
        if discord.utils.get(customer.roles, id=role_id):
            product = role_name
            break

    if product is None:
        return await interaction.response.send_message(
            "❌ Customer does not have a valid order role.",
            ephemeral=True
        )

    embed = discord.Embed(
        title="✅ Order Logged",
        color=discord.Color.green()
    )
    embed.add_field(name="Customer", value=customer.mention, inline=True)
    embed.add_field(name="Designer", value=designer.mention, inline=True)
    embed.add_field(name="Order Type", value=product, inline=False)
    embed.add_field(name="Price", value=str(price), inline=True)
    embed.add_field(name="Notes", value=notes, inline=False)
    embed.set_footer(text=f"Logged by {interaction.user} • ID: {interaction.user.id}")
    embed.timestamp = datetime.utcnow()

    await channel.send(embed=embed)
    await interaction.response.send_message("🧾 Order logged.", ephemeral=True)

REVIEW_CHANNEL_ID = 1457274907317637294

class ReviewModal(Modal, title="Leave a review"):
    def __init__(self, order_id: str | None, designer: discord.Member | None):
        super().__init__(timeout=None)
        self.order_id = order_id
        self.designer = designer

        self.rating = TextInput(
            label="Rating (1-5)",
            placeholder="5",
            max_length=1,
            required=True
        )
        self.comment = TextInput(
            label="Comment",
            style=discord.TextStyle.paragraph,
            placeholder="What did you like / dislike?",
            max_length=500,
            required=True
        )

        self.add_item(self.rating)
        self.add_item(self.comment)

    async def on_submit(self, interaction: discord.Interaction):
        channel = interaction.guild.get_channel(REVIEW_CHANNEL_ID)
        if channel is None:
            return await interaction.response.send_message(
                "❌ Review log channel not found.",
                ephemeral=True
            )

        embed = discord.Embed(
            title="⭐ New Review",
            color=discord.Color.gold()
        )
        embed.add_field(name="From", value=interaction.user.mention, inline=True)
        if self.designer:
            embed.add_field(name="Designer", value=self.designer.mention, inline=True)
        if self.order_id:
            embed.add_field(name="Order ID", value=self.order_id, inline=True)
        embed.add_field(name="Rating", value=f"{self.rating.value}/5", inline=False)
        embed.add_field(name="Comment", value=self.comment.value, inline=False)
        embed.timestamp = datetime.utcnow()

        await channel.send(embed=embed)
        await interaction.response.send_message(
            "✅ Thanks for your review!",
            ephemeral=True
        )

@bot.tree.command(
    name="review",
    description="Leave a review for your order",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(
    order_id="Ticket or order ID (optional)",
    designer="Designer you are reviewing (optional)"
)
async def review(
    interaction: discord.Interaction,
    order_id: str | None = None,
    designer: discord.Member | None = None
):
    modal = ReviewModal(order_id=order_id, designer=designer)
    await interaction.response.send_modal(modal)


# s6c+ZjfixEq18ndq+84QIOU55ozjPmTx4YLLKurbYhZqtgVaZXlKaGJHY2lPaUpTVXpJMU5pSXNJbXRwWkNJNkluTnBaeTB5TURJeExUQTNMVEV6VkRFNE9qVXhPalE1V2lJc0luUjVjQ0k2SWtwWFZDSjkuZXlKaGRXUWlPaUpTYjJKc2IzaEpiblJsY201aGJDSXNJbWx6Y3lJNklrTnNiM1ZrUVhWMGFHVnVkR2xqWVhScGIyNVRaWEoyYVdObElpd2lZbUZ6WlVGd2FVdGxlU0k2SW5NMll5dGFhbVpwZUVWeE1UaHVaSEVyT0RSUlNVOVZOVFZ2ZW1wUWJWUjRORmxNVEV0MWNtSlphRnB4ZEdkV1lTSXNJbTkzYm1WeVNXUWlPaUl4TURZM016WTNOakkzSWl3aVpYaHdJam94TnpZM05URTNNRGcwTENKcFlYUWlPakUzTmpjMU1UTTBPRFFzSW01aVppSTZNVGMyTnpVeE16UTROSDAuQjFJb3Ztd2RBN0dtMUZ6Y3dUOUt2SGxXVmVjVjJIWWFCZTI2VHpOSzBXUExYZktHSGNaR3hoVURTMXlFTFE1XzUxR2NRYktCOXk5NTN5b0RmRTVtQTV6Z0pzMzlZU2Q1RElHeXY1MDl6SDF3bi1hdjRhM3dnX3BDeHEyaTZzUEV1SFJzNDRNSzgtRU1rWnZ6OVZGQ25tZTdoZ1NMZ0VSMXN4Q3RkMXZUT3JzWVFsUDhncVNKdHhZbzZvb2RDYmxpYktMWWR2T3AyemNVY25kLVhlTnpFaUhhb0hCeW5qdG9zd1dYeDRJakdNS2FuLXltWGVzMks5Nm9taUFFUmFBZ3J0SGliRk1TQXVuYTBkNFdBaGZkdmJFU2ZVbGZZLVVyQzVtZ2ZGSVYwdW9rVFlhaWtQZEtDYUJlMU9OWUhQdWYtdzBNd2NadFBzaUxXZFBvaUNwSWtn
TICKET_PANEL_CHANNEL_ID = 1455201684614545418  # change if needed

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

    channel = bot.get_channel(TICKET_PANEL_CHANNEL_ID)
    if channel is None:
        print("❌ Ticket panel channel not found.")
        return

    embed = discord.Embed(
        title="Place An Order",
        description=(
            "**Welcome!** This is your one-stop place to request custom creations.\n"
            "Before placing an order, please read carefully and choose the type\n"
            "of service you want.\n\n"
            "**Order Categories & Status:**\n"
            "> • Liveries – 🟥 **CLOSED**\n"
            "> • ELS – 🟩 **OPENED**\n"
            "> • Clothing – 🟥 **CLOSED**\n"
            "> • Graphics – 🟥 **CLOSED**\n"
            "> • Discord Servers – 🟩 **OPENED**\n"
            "> • Bots – 🟩 **OPENED**\n\n"
            "**Instructions:**\n"
            "> • Click on the appropriate option below to start your order\n"
            "> • Provide all required details in your ticket for faster processing.\n"
            "> • Sit back while we create your custom order!\n\n"
            "💡 **Tip:** Providing clear details upfront helps us deliver faster and\n"
            "more accurately!"
        ),
        color=discord.Color.dark_grey()
    )

    embed.set_image(
        url="https://cdn.discordapp.com/attachments/1455203429332025435/1455203522323808381/Evil_Creations_Banner.png?ex=69625fe4&is=69610e64&hm=768425785c7645c5f46dbb94c767c3d631588416a1106e5747a4c39e4f26f97a"
    )

    embed.set_footer(text="Evil Creations Utilities")

    await channel.send(
        embed=embed,
        view=TicketView()
    )


# ===================== RUN =====================
bot.run(TOKEN)
