import os
import discord
from discord.embeds import EmbedProxy
import discord.embeds
from discord.ext import commands, tasks
from discord.ui import Button, View
from discord import app_commands
import asyncio
from enum import Enum
from datetime import datetime, timedelta
import pandas as pd
import random
import aiohttp
import json

# Load stats from JSON (or set defaults if file doesn't exist)
stats_file = "stats.json"

# Load stats from JSON (or set defaults if file doesn't exist)
if os.path.exists(stats_file):
    with open(stats_file, "r") as f:
        data = json.load(f)
        ac = data.get("ac", 0)
        user_ac = data.get("user_ac", {})
        cl = data.get("cl", 0)
        user_cl = data.get("user_cl", {})
else:
    ac = 1
    user_ac = {}
    cl = 1
    user_cl = {}
def save_stats():
    with open(stats_file, "w") as f:
        json.dump({
            "ac": ac,
            "user_ac": user_ac,
            "cl": cl,
            "user_cl": user_cl
        }, f, indent=4)
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

emails = {}

resign_confirmation = {}
resign_reason = {}

icount = 0
hrd_casenumber = 0
duilogcounter = 0

if os.path.exists('infractions.csv'):
    infraction_df = pd.read_csv('infractions.csv', dtype={'MessageID': str})  # Ensure MessageID is read as string
    if not infraction_df.empty:
        icount = infraction_df['InfractionID'].max()
else:
    infraction_df = pd.DataFrame(columns=[
        'InfractionID',
        'TrooperID',
        'TrooperMention',
        'InfractionType',
        'Reason',
        'IssuedBy',
        'IssuedByID',
        'MessageID',
        'Staff Notes',
        'User Notes'
    ])

# Save DataFrame
def save_infractions():
    infraction_df.to_csv('infractions.csv', index=False)

if os.path.exists('cadet_exam.csv'):
    cadet_exam_df = pd.read_csv('cadet_exam.csv')
else:
    cadet_exam_df = pd.DataFrame(columns=['Cadet', 'Result', 'Notes'])

def save_cadetexam():
    cadet_exam_df.to_csv('cadet_exam.csv', index=False)

if os.path.exists('sergeant_exam.csv'):
    sergeant_exam_df = pd.read_csv('sergeant_exam.csv')
else:
    sergeant_exam_df = pd.DataFrame(columns=['User', 'Result', 'Notes'])

def save_sergeantexam():
    sergeant_exam_df.to_csv('sergeant_exam.csv', index=False)

if os.path.exists('retirement_view.csv'):
    retirement_view_df = pd.read_csv('retirement_view.csv')
else:
    retirement_view_df = pd.DataFrame(columns=['User', 'Reason', 'Primary Division', 'Secondary Division', 'Rank'])

def save_retirementview():
    retirement_view_df.to_csv('retirement_view.csv', index=False)

# Your Guild ID here
gid = 1087222212148338688  # Replace with your actual guild ID
infraction_df["Staff Notes"] = "Nil"
infraction_df["User Notes"] = "Nil"
save_infractions()
attendingcadets = set()
tt_determiner = 0
host = ''
trainingglobaltbd = None

awaiting_probation = set()

dm = True

API_KEY='9a6Ut4OFxUajIvftxebFsvCoIiJX7GBn50VoQSteTHIXu1KuZXlKaGJHY2lPaUpTVXpJMU5pSXNJbXRwWkNJNkluTnBaeTB5TURJeExUQTNMVEV6VkRFNE9qVXhPalE1V2lJc0luUjVjQ0k2SWtwWFZDSjkuZXlKaVlYTmxRWEJwUzJWNUlqb2lPV0UyVlhRMFQwWjRWV0ZxU1habWRIaGxZa1p6ZGtOdlNXbEtXRGRIUW00MU1GWnZVVk4wWlZSSVNWaDFNVXQxSWl3aWIzZHVaWEpKWkNJNklqRXdOamN6TmpjMk1qY2lMQ0poZFdRaU9pSlNiMkpzYjNoSmJuUmxjbTVoYkNJc0ltbHpjeUk2SWtOc2IzVmtRWFYwYUdWdWRHbGpZWFJwYjI1VFpYSjJhV05sSWl3aVpYaHdJam94TnpVeE1qQTJNRFkyTENKcFlYUWlPakUzTlRFeU1ESTBOallzSW01aVppSTZNVGMxTVRJd01qUTJObjAubVpCMTFNNlpEMHdhVWNmMzRmWXU4blhFRU9mYWt5YVVwcldleDFpQUFVTnROUjRqSVQ1ZDYwd2loVkdHT3B6SE5YZHFhNUhIc2RGa3pwSmdyRFpyRXBJU2NXUXFpSE9DWHdqX1U5Qkh5c29Kd1gtLVltRVd2eU1zWjRYZU8yRWpUR1AzT3NBQTdVekdZUld4TEtmeVRLdzRZYWJVcGxZSmdwc2pkUjdDTlFMaTR6Q2JRbGR5LXpRMFUxVUM3R2FmVzdfM3UyV0lKUEFWMFZVdVN5RHltRW1SZ19IM0lVVVdjcnRBZ3l2WGp6NE9mZFphQVlQR1lUQ3pmMko0eEx5Ui1WUXNmblcxaVlJX2k0SDNHb1AzclFmR0hUcjQ2UVJKQ2l6UTc2QlN2a3B3MmlUdmRvQ0lJc19pX21LNTBBR3JUWmNLTzEzc3V4SEtWMHRuNkVCbGhB'
GROUP_ID='17406762'

HEADERS = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
}


class intype(Enum):
    Activity_Notice = 'Activity Notice'
    Notice = 'Notice'
    Warning = 'Warning'
    Strike = 'Strike'
    Demotion = 'Demotion'
    Division_Removal = 'Division Removal'
    Termination = 'Termination'
    Blacklist = 'Blacklist'

class trainingresult(Enum):
    Passed = 'Passed'
    Failed = 'Failed'

class trainingtype(Enum):
    Basic_Training = "Basic Training"
    Advanced_Training = "Advanced Training"

class pagetype(Enum):
    CID = 'Criminal Investigation Department'
    SWAT = 'Special Weapons and Tactics'
    Supervisors = 'Supervisors'

class cadetexamresult(Enum):
    Passed = 'Passed'
    Failed = 'Failed'

class sergeantexamresult(Enum):
    Passed = 'Passed'
    Failed = 'Failed'

class intoxicated(Enum):
    Yes = 'Yes'
    No = 'No'

class hrdlogtypes(Enum):
    Appeal = 'Appeal'
    Reinstatement = 'Reinstatement'
    Transfer = 'Transfer'
    Retirement = 'Retirement'

class hrdlogoutcome(Enum):
    Approved = 'Approved'
    Denied = 'Denied'
    Voided = 'Voided'
    Lower_Sustained = 'Lower Sustained'

bot = commands.Bot(command_prefix='-', intents=intents)

@bot.event
async def on_command(ctx):
    embed = discord.Embed(
        title=f'Command used by {ctx.author.display_name}',
        description=f'Command: {ctx.command}\nChannel: {ctx.channel.mention}',
        color=discord.Color.yellow()
    ) 
    channel = await bot.fetch_channel(1157078258479796265)
    await channel.send(embed=embed)

@bot.event
async def on_app_command_completion(interaction: discord.Interaction, command: app_commands.Command):
    member = interaction.guild.get_member(interaction.user.id)
    embed = discord.Embed(
        title=f'Command used by {member.display_name}',
        description=f'Command: {command.name}\nChannel: {interaction.channel.mention}',
        color=discord.Color.yellow()
    )
    channel = await bot.fetch_channel(1157078258479796265)
    await channel.send(embed=embed)
    
@bot.event
async def on_member_remove(member):
    role = member.guild.get_role(1087222212177694864)
    if role in member.roles:
        global icount, infraction_df

        infraction_channel = await member.guild.fetch_channel(1158015047902179389)
        icount += 1

        embed = discord.Embed(
            title=f'__Infraction Log #{icount}__',
            description=f'**Trooper**\n{member}\n\n**Infraction**\nBlacklist\n\n**Reason**\nAbandoning Employment\n\n**Issued by**\nWSP Automation\n\n-# This is an automated infraction.',
            color=discord.Color.yellow()
        )

        infraction_msg = await infraction_channel.send(embed=embed)
        thread = await infraction_msg.create_thread(
            name=f'Infraction #{icount} - Evidence'
        )

        new_entry = {
            'InfractionID': icount,
            'TrooperID': member.id,
            'TrooperMention': member.mention,
            'InfractionType': 'Blacklist',
            'Reason': 'Abandoning Employment',
            'IssuedBy': 'WSP Automation',
            'IssuedByID': 'WSP Automation',
            'MessageID': str(infraction_msg.id)  # Store as string
        }

        infraction_df = pd.concat([infraction_df, pd.DataFrame([new_entry])], ignore_index=True)
        save_infractions()
    else:
        print('just doing this to avoid syntax error :>')

@tasks.loop(seconds=0)
async def send_division_reminder():
    guild = bot.get_guild(gid)
    if guild is None:
        print("Guild not found.")
        return
    emoji = discord.utils.get(guild.emojis, name="w_information")
    channel = await bot.fetch_channel(1178083490542137474)
    channel2 = await bot.fetch_channel(1139084621695422574)
    divisions = [1272100535020945491, 1130263152290971648, 1189261114370961560,1197727148677541958, 1126588703763079239, 1130261043952746559, 1388343323709800498, 1134648458486231040, 1166452249409634417, ]
    for div in divisions:
        role = guild.get_role(div)
        await channel.send(f"{emoji} Howdy {role.mention}! It's your turn to post in {channel2.mention}")
        await asyncio.sleep(172800)

@tasks.loop(hours=24)
async def update_trooper_count():
    guild = bot.get_guild(1087222212148338688)
    role = guild.get_role(1087222212177694864)
    count = len(role.members)

    channel = guild.get_channel(1161257813960573000)
    channel2 = guild.get_channel(1161260465121415198)
    await channel.edit(name=f'Troopers: {count} / 215')
    await channel2.edit(name=f'Members: {guild.member_count}')

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    if dm:
        guild = discord.Object(id=gid)
        await bot.tree.sync(guild=guild)
        print("Commands synced")
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="100+ Troopers"))
        update_trooper_count.start()
    else:
        print('impossible mate, how did u get here -?')

@bot.tree.command(name='addemail', description='Add the email of a trooper.', guild=discord.Object(id=gid))
@app_commands.describe(trooper='Username of the trooper.', email='Email of the trooper.')

async def addemail(interaction: discord.Interaction, trooper: discord.User, email: str):
    # Correct role fetching
    dc_role = interaction.guild.get_role(1087222212198678566)

    # Convert the user to a guild member to access their roles
    member = interaction.guild.get_member(interaction.user.id)

    if dc_role not in member.roles:
        await interaction.response.send_message('No permission!', ephemeral=True)
        return

    if trooper.id not in emails:
        emails[trooper.id] = email
        se = discord.Embed(
            title='__Added email successfully!__',
            description=f'Trooper: {trooper}\nEmail: {email}\nAdded by: {interaction.user}',
            color=discord.Color.yellow()
        )
        await interaction.response.send_message(embed=se)
        await interaction.followup.send('Email added successfully!', ephemeral=True)
    else:
        await interaction.response.send_message('Trooper already has an email added. Use `/resetemail` to reset their email.', ephemeral=True)

@bot.tree.command(name='resetemail', description="Reset a trooper's email.", guild=discord.Object(id=gid))
@app_commands.describe(trooper='Username of targetted trooper.', newemail='New email of targetted trooper.', reason='Reason for change.')

async def resetemail(interaction: discord.Interaction, trooper: discord.User, newemail: str, reason: str):
    if trooper.id not in emails:
        await interaction.response.send_message("Trooper doesn't have a email linked. Link it using `/addemail`.", ephemeral=True)
    else:
        ab = Button(label='Accept', style=discord.ButtonStyle.green)
        async def ab_c(interaction:discord.Interaction):
            r_eb = discord.Embed(
                title='__Email Reset!__',
                description=f'Trooper: {trooper}\nOld Email: {emails[trooper.id]}\nNew Email: {newemail}\nReason: {reason}',
                color= discord.Color.yellow()
            )
            await interaction.response.send_message(embed=r_eb)
            emails[trooper.id] = newemail

        ab.callback = ab_c

        remv = View()
        remv.add_item(ab)
        msg = await interaction.response.send_message(f'Are you sure you want to update the email?\nOld Email: {emails[trooper.id]}\nNew Emails: {newemail}\nReason: {reason}\n\nDismiss the message to discard the change request.', view=remv, ephemeral=True)


@bot.tree.command(name='checkemail', description='Check email of a trooper.', guild=discord.Object(id=gid))
@app_commands.describe(trooper='Trooper name.')

async def checkemail(interaction: discord.Interaction, trooper: discord.User):
    if trooper.id not in emails:
        await interaction.response.send_message("Selected trooper doesn't have a email. Add their email using `/addemail`.",ephemeral=True)
    else:
        emailcb = emails[trooper.id]
        await interaction.response.send_message(f"Email of {trooper} is: {emailcb}",ephemeral=True)

@bot.tree.command(name='infraction', description='Log an infraction.', guild=discord.Object(id=gid))
@app_commands.describe(trooper='Trooper to infract.', infraction='Infraction type', reason='Reason for infraction.')
async def infraction(interaction: discord.Interaction, trooper: discord.User, infraction: intype, reason: str):
    global icount, infraction_df

    infraction_channel = await interaction.guild.fetch_channel(1158015047902179389)
    icount += 1

    embed = discord.Embed(
        title=f'__Infraction Log #{icount}__',
        description=f'**Trooper**\n{trooper.mention}\n\n**Infraction**\n{infraction.value}\n\n**Reason**\n{reason}\n\n**Issued by**\n{interaction.user.mention}',
        color=discord.Color.yellow()
    )
    to_userembed = discord.Embed(
        title=f'__Infraction Log #{icount}__',
        description=f'**Trooper**\n{trooper.mention}\n\n**Infraction**\n{infraction.value}\n\n**Reason**\n{reason}',
        color=discord.Color.yellow()
    )

    infraction_msg = await infraction_channel.send(embed=embed)
    await interaction.response.send_message('Infraction Logged!', ephemeral=True)
    thread = await infraction_msg.create_thread(
        name=f'Infraction #{icount} - Evidence'
    )

    try:
        await trooper.send(embed=to_userembed)
    except discord.HTTPException as e:
        if e.code == 50007:
            await interaction.followup.send(f"`Automatic DM failed. Please DM the user manually.`")
        else:
            raise  # re-raise the exception if it's not error 50007

    new_entry = {
        'InfractionID': icount,
        'TrooperID': trooper.id,
        'TrooperMention': trooper.mention,
        'InfractionType': infraction.value,
        'Reason': reason,
        'IssuedBy': interaction.user.mention,
        'IssuedByID': interaction.user.id,
        'MessageID': str(infraction_msg.id)  # Store as string
    }

    infraction_df = pd.concat([infraction_df, pd.DataFrame([new_entry])], ignore_index=True)
    save_infractions()

# Void Infraction Command
@bot.tree.command(name='infractionvoid', description='Void an infraction.', guild=discord.Object(id=gid))
@app_commands.describe(infraction_id='Infraction ID.', reason='Reason for voiding the infraction.')
async def infractionvoid(interaction: discord.Interaction, infraction_id: int, reason: str):
    await interaction.response.defer(ephemeral=True)
    global infraction_df

    if infraction_id in infraction_df['InfractionID'].values:
        infraction_channel = await interaction.guild.fetch_channel(1158015047902179389)
        row = infraction_df[infraction_df['InfractionID'] == infraction_id].iloc[0]

        msg_id = int(row['MessageID'])
        try:
            msg = await infraction_channel.fetch_message(msg_id)
        except discord.NotFound:
            await interaction.followup.send('Original infraction message not found.', ephemeral=True)
            return

        embed = discord.Embed(
            title=f'__Infraction #{infraction_id}__',
            description=f'**__Trooper__**\n{row["TrooperMention"]}\n\n**__Infraction Type__**\n~~{row["InfractionType"]}~~\n\n**__Reason__**\n{row["Reason"]}\n\n-# Voided by {interaction.user.mention}',
            color=discord.Color.yellow()
        )

        await msg.edit(embed=embed)

        infraction_df.loc[infraction_df['InfractionID'] == infraction_id, 'InfractionType'] = 'VOIDED'
        infraction_df.loc[infraction_df['InfractionID'] == infraction_id, 'Reason'] = f'Voided: {reason}'
        save_infractions()

        await interaction.followup.send(f'Infraction {infraction_id} voided successfully!', ephemeral=True)
    else:
        await interaction.followup.send(f'No infraction with ID {infraction_id} found.', ephemeral=True)

# Edit Infraction Command
@bot.tree.command(name='infractionedit', description='Edit an infraction.', guild=discord.Object(id=gid))
@app_commands.describe(infraction_id='Infraction ID.', infraction='New infraction type.', reason='New reason.')
async def infractionedit(interaction: discord.Interaction, infraction_id: int, infraction: intype, reason: str):
    await interaction.response.defer(ephemeral=True)
    global infraction_df

    if infraction_id in infraction_df['InfractionID'].values:
        infraction_channel = await interaction.guild.fetch_channel(1158015047902179389)
        row = infraction_df[infraction_df['InfractionID'] == infraction_id].iloc[0]

        msg_id = int(row['MessageID'])
        try:
            msg = await infraction_channel.fetch_message(msg_id)
        except discord.NotFound:
            await interaction.followup.send('Original infraction not found.', ephemeral=True)
            return

        embed = discord.Embed(
            title=f'__Infraction #{infraction_id}__',
            description=f'**__Trooper__**\n{row["TrooperMention"]}\n\n**__Infraction__**\n{infraction.value}\n\n**__Reason__**\n{reason}\n\n**__Issued by__**\n{row["IssuedBy"]}\n\n-# Edited by {interaction.user.mention}',
            color=discord.Color.yellow()
        )

        await msg.edit(embed=embed)

        infraction_df.loc[infraction_df['InfractionID'] == infraction_id, 'InfractionType'] = infraction.value
        infraction_df.loc[infraction_df['InfractionID'] == infraction_id, 'Reason'] = reason
        save_infractions()

        await interaction.followup.send(f'Infraction {infraction_id} has been edited successfully.', ephemeral=True)
    else:
        await interaction.followup.send(f'No infraction with ID {infraction_id} found.', ephemeral=True)

# Infraction History Command
@bot.tree.command(name='infractionhistory', description='Check the infraction history of a trooper.', guild=discord.Object(id=gid))
@app_commands.describe(trooper='Trooper to check history.')
async def infractionhistory(interaction: discord.Interaction, trooper: discord.User):
    user_df = infraction_df[infraction_df['TrooperID'] == trooper.id]

    if user_df.empty:
        embed = discord.Embed(
            title=f'Infraction History of {trooper}',
            description='No infraction history.',
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    description = ''
    for _, row in user_df.iterrows():
        description += f"**Infraction ID:** {row['InfractionID']}\n**Infraction:** {row['InfractionType']}\n**Reason:** {row['Reason']}\n**Issued by:** {row['IssuedBy']}\n\n"

    embed = discord.Embed(
        title=f'Infraction History of {trooper}',
        description=description,
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

# My Infractions Command
@bot.tree.command(name='myinfractions', description='Check your own infraction history.', guild=discord.Object(id=gid))
async def myinfractions(interaction: discord.Interaction):
    user_df = infraction_df[infraction_df['TrooperID'] == interaction.user.id]

    if user_df.empty:
        embed = discord.Embed(
            title=f'Infraction History of {interaction.user}',
            description='No infraction history.',
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    description = ''
    for _, row in user_df.iterrows():
        description += f"**Infraction ID:** {row['InfractionID']}\n**Infraction:** {row['InfractionType']}\n**Reason:** {row['Reason']}\n**Issued by:** {row['IssuedBy']}\n\n"

    embed = discord.Embed(
        title=f'Infraction History of {interaction.user}',
        description=description,
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name='logarrest', description='Log a arrest.', guild=discord.Object(id=gid))
@app_commands.describe(
    troopers_involved='Troopers involved at scene.',
    suspects='Name of the suspect arrested.',
    description='Summary of what led to the arrest.',
    charges='Charges filed against the suspect.',
    mugshot='Mugshot of the suspect.'
)
async def logarrest(interaction: discord.Interaction, troopers_involved: str, suspects: str, description: str, charges: str, mugshot: discord.Attachment):
    global ac
    arrest_channel = await interaction.guild.fetch_channel(1090451609445740614)
    bl_time = datetime.now().strftime('%#m/%#d/%Y %#I:%M %p')

    ae = discord.Embed(
        title=f'__Arrest Log #{ac}__',
        description=f'__**Troopers Involved**__\n{troopers_involved}\n\n__**Suspect(s)**__\n{suspects}\n\n__**Description**__\n{description}\n\n__**Charges**__: {charges}',
        color=discord.Color.yellow()
    )
    ae.set_image(url=mugshot.url)
    ae.set_footer(text=bl_time)
    ae.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)

    ac += 1
    user_ac[str(interaction.user.id)] = user_ac.get(str(interaction.user.id), 0) + 1
    save_stats()  # Save after updating

    await arrest_channel.send(embed=ae)
    await interaction.response.send_message('Arrest Logged!', ephemeral=True)


@bot.tree.command(name='logcitation', description='Log a citation.', guild=discord.Object(id=gid))
@app_commands.describe(
    troopers_involved='Troopers involved at scene.',
    suspects='Name of the suspect arrested.',
    description='Summary of what led to the arrest.',
    charges='Charges filed against the suspect.',
    citation_photo='Picture of citation.'
)
async def logcitation(interaction: discord.Interaction, troopers_involved: str, suspects: str, description: str, charges: str, citation_photo: discord.Attachment):
    global cl
    citation_channel = await interaction.guild.fetch_channel(1155444676321611876)
    bl_time = datetime.now().strftime('%#m/%#d/%Y %#I:%M %p')

    ae = discord.Embed(
        title=f'__Citation Log #{cl}__',
        description=f'__**Troopers Involved**__\n{troopers_involved}\n\n__**Suspect(s)**__\n{suspects}\n\n__**Description**__\n{description}\n\n__**Charges**__: {charges}',
        color=discord.Color.yellow()
    )
    ae.set_image(url=citation_photo.url)
    ae.set_footer(text=bl_time)
    ae.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)

    cl += 1
    user_cl[str(interaction.user.id)] = user_cl.get(str(interaction.user.id), 0) + 1
    save_stats()  # Save after updating

    await citation_channel.send(embed=ae)
    await interaction.response.send_message('Citation logged!', ephemeral=True)


@bot.tree.command(name='check_arrest_stat', guild=discord.Object(id=gid))
async def check_arrest_stats(interaction: discord.Interaction):
    await interaction.response.send_message(f"Total department arrest count is {ac-1}", ephemeral=True)


@bot.tree.command(name='check_citation_stat', guild=discord.Object(id=gid))
async def check_citation_stats(interaction: discord.Interaction):
    await interaction.response.send_message(f"Total department citation count is {cl-1}", ephemeral=True)


@bot.tree.command(name='check_user_stat', guild=discord.Object(id=gid))
@app_commands.describe(trooper='Trooper to check stat for.')
async def check_user_stat(interaction: discord.Interaction, trooper: discord.User):
    arrests = user_ac.get(str(trooper.id), 0)
    citations = user_cl.get(str(trooper.id), 0)
    member = await interaction.guild.fetch_member(trooper.id)
    await interaction.response.send_message(
        f'Total arrests for {member.display_name} is: {arrests}\n\nTotal citations for {trooper} is {citations}',
        ephemeral=True
    )


@bot.tree.command(name='stat_leaderboard', description='Arrest and Citation Stat Leaderboard', guild=discord.Object(id=gid))
async def stat_leaderboard(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True, ephemeral=True)
    if not user_ac and not user_cl:
        await interaction.followup.send("No arrests or citations have been logged yet.", ephemeral=True)
        return

    # Arrest Leaderboard
    arrest_lb = ""
    if user_ac:
        sorted_arrests = sorted(user_ac.items(), key=lambda x: x[1], reverse=True)
        for index, (user_id, count) in enumerate(sorted_arrests, start=1):
            user = await bot.fetch_user(int(user_id))
            member = await interaction.guild.fetch_member(user.id)
            arrest_lb += f"**{index}. {member.display_name}** {count} arrests\n"
    else:
        arrest_lb = "No arrests logged yet."

    # Citation Leaderboard
    citation_lb = ""
    if user_cl:
        sorted_citations = sorted(user_cl.items(), key=lambda x: x[1], reverse=True)
        for index, (user_id, count) in enumerate(sorted_citations, start=1):
            user = await bot.fetch_user(int(user_id))
            member = await interaction.guild.fetch_member(user.id)
            citation_lb += f"**{index}. {member.display_name}** {count} citations\n"
    else:
        citation_lb = "No citations logged yet."

    embed = discord.Embed(
        title="Arrest & Citation Stats Leaderboard",
        color=discord.Color.blue()
    )
    embed.add_field(name="__Arrest Leaderboard__", value=arrest_lb, inline=False)
    embed.add_field(name="__Citation Leaderboard__", value=citation_lb, inline=False)

    await interaction.followup.send(embed=embed, ephemeral=True)

# Training Division Modules

@bot.command(name='training', description='Start training.')
async def training(ctx, *, msg=None):
    global attendingcadets
    global trainingglobaltbd

    bt_cc = ctx.guild.get_role(1135039042694684783)
    at_cc = ctx.guild.get_role(1308369459836223538)

    attendee_count = 0
    attendingcadets = set()  # make sure it's initialized

    # Embed
    bt_eb = discord.Embed(
        title='__Training!__',
        description=f'A Training is currently being hosted! React below if you are able to attend.\n\n'
                    f'Host: {ctx.author.mention}\n\n'
                    f'Attendees: {attendee_count}',
        color=discord.Color.yellow()
    )

    # View + Button
    at_view = View(timeout=None)
    abt = Button(label='Attend', style=discord.ButtonStyle.green)
    view_attendees = Button(label='View Attendees', style = discord.ButtonStyle.grey)
    at_view.add_item(abt)
    at_view.add_item(view_attendees)

    # Send training message
    tbe = await ctx.send(f"CC: {bt_cc.mention}", embed=bt_eb, view=at_view)
    await ctx.message.delete()

    # --- Callback function ---
    async def view_attendees_callback(interaction: discord.Interaction):
        mentions = "\n".join(user.mention for user in attendingcadets)
        view_cadets_embed = discord.Embed(
            title='Attending Cadets',
            description=mentions,
            color = discord.Color.blue()
        )
        await interaction.response.send_message(embed=view_cadets_embed, ephemeral=True)
    async def abtcb(interaction: discord.Interaction):
        nonlocal attendee_count

        if interaction.user in attendingcadets:
            # Already attending -> show "remove attendance" option
            rbt = Button(label='Remove Attendance', style=discord.ButtonStyle.red)

            async def rbtcb(interaction2: discord.Interaction):
                nonlocal attendee_count
                attendingcadets.remove(interaction2.user)
                attendee_count -= 1

                bt_eb_updated = discord.Embed(
                    title='__Training!__',
                    description=f'A Training is currently being hosted! React below if you are able to attend.\n\n'
                                f'Host: {ctx.author.mention}\n\n'
                                f'Attendees: {attendee_count}',
                    color=discord.Color.yellow()
                )

                await tbe.edit(embed=bt_eb_updated, view=at_view)
                await interaction2.response.send_message('Attendance removed!', ephemeral=True)

            rbt.callback = rbtcb
            rbtview = View(timeout=None)
            rbtview.add_item(rbt)

            await interaction.response.send_message(
                "Your attendance has already been marked! Click below to remove your attendance.",
                view=rbtview,
                ephemeral=True
            )
        else:
            # Mark attendance
            attendingcadets.add(interaction.user)
            attendee_count += 1

            bt_eb_updated = discord.Embed(
                title='__Training!__',
                description=f'A Training is currently being hosted! React below if you are able to attend.\n\n'
                            f'Host: {ctx.author.mention}\n\n'
                            f'Attendees: {attendee_count}',
                color=discord.Color.yellow()
            )

            await tbe.edit(embed=bt_eb_updated, view=at_view)
            await interaction.response.send_message('Attendance marked!', ephemeral=True)

    # Attach callback AFTER sending message
    abt.callback = abtcb
    view_attendees.callback = view_attendees_callback
    trainingglobaltbd = {"channel": tbe.channel.id, "message": tbe.id}

@bot.command(name='host')
async def host(ctx):
    global attendingcadets
    global host
    global tt_determiner
    global trainingglobaltbd

    if not attendingcadets:
        await ctx.send('Action failed. No attendees found.')
        return

    await ctx.message.delete()

    pings = '\n'.join(user.mention for user in attendingcadets)

    training_embed = discord.Embed(
        title=f'Training has started!',
        description=f'The Training hosted by {host} has started! '
                    f'Hop on PD and wait in the meeting room.\n\n'
                    f'Server Code: `WSPB`\n\n'
                    f'Attendees:\n{pings}\n\n'
                    f'You are required to attend!',
        color=discord.Color.yellow()
    )

    # delete old training message if it exists
    if trainingglobaltbd is not None:
        try:
            channel_id = trainingglobaltbd["channel"]
            message_id = trainingglobaltbd["message"]

            channel = await bot.fetch_channel(channel_id)
            message = await channel.fetch_message(message_id)
            await message.delete()
        except discord.NotFound:
            await ctx.send("Training message already deleted.")
        trainingglobaltbd = None

    # send new start embed
    await ctx.send(pings, embed=training_embed)

    attendingcadets.clear()
    host = None
    tt_determiner = 0
@bot.command(name='ra')
async def ra(ctx):
    RAhost_cc = ctx.guild.get_role(1135039129130897498)
    host = ctx.author
    tbd5 = ctx.message
    ra_embed = discord.Embed(
        title='Ride along!',
        description= f'Ride along is being hosted by {ctx.author.mention}! Press the button below if you can attend!',
        color=discord.Color.yellow()
    )
    await tbd5.delete()
    attendbutton = Button(label='Attend', style=discord.ButtonStyle.green)
    abview = View()
    abview.add_item(attendbutton)
    tbd6 = await ctx.send(f"CC: {RAhost_cc.mention}",embed=ra_embed, view=abview)
    async def onabpress(interaction:discord.Interaction):
        RA_embed = discord.Embed(
            title='Ride Along Started!',
            description=f'Ride along hosted by {host.mention} has been claimed by {interaction.user.mention}! Join SRP and join PD and wait in the PD waiting room.',
            color = discord.Color.yellow()
        )
        await ctx.send(embed=RA_embed)
        await tbd6.delete()
    attendbutton.callback = onabpress

@bot.tree.command(name='logtraining', description="Log a cadet's training.", guild=discord.Object(id=gid))
@app_commands.describe(cadet='Name of cadet.',description='Training description.', result='Result of the training.')

async def logtraining(interaction: discord.Interaction, cadet: discord.Member, description: str, result: trainingresult):
    bt_logtime = datetime.now().strftime('%#m/%#d/%Y %#I:%M %p')
    bt_resultlog_embed = discord.Embed(
        title='__Training Log__',
        description=f'**__Trainer__**: {interaction.user.mention}\n**__Cadet__**: {cadet.mention}\n**__Description__**: {description}\n**__Result__**: {result.value}',
        color=discord.Color.yellow()
    )
    member = interaction.guild.get_member(interaction.user.id)
    bt_resultlog_embed.set_author(name= member.display_name, icon_url=interaction.user.avatar.url)
    bt_resultlog_embed.set_footer(text=bt_logtime)
    channel = await interaction.guild.fetch_channel(1090452810581147729)
    tomentionrole = interaction.guild.get_role(1130263152290971648)
    await channel.send(f'CC: {tomentionrole.mention}',embed=bt_resultlog_embed)
    await interaction.response.send_message('Logged training sucessfully!',ephemeral=True)
    if result.value == 'Passed':
        remove_bt_role = interaction.guild.get_role(1135039042694684783)
        add_ra_role = interaction.guild.get_role(1135039129130897498)
        await cadet.add_roles(add_ra_role)
        await cadet.remove_roles(remove_bt_role)
        await interaction.followup.send(f'Added *Needs Ride Along* role to {cadet.display_name}!',ephemeral=True)
    else:
        return
@bot.tree.command(name='logra', description='Logs an RA.',guild=discord.Object(id=gid))
@app_commands.describe(cadet='Name of cadet who participated in RA.',description='What happened during the RA?', start_time = 'RA start time.', end_time='RA end time.', score='Total score of RA.', result='Result of RA.')

async def logra(interaction:discord.Interaction, cadet: discord.User, description: str, start_time: str, end_time: str, score: int, result: trainingresult):
    ral_channel = await interaction.guild.fetch_channel(1132955979785449532)
    ra_embed = discord.Embed(
        title= 'Ride along log!',
        description=f'**__Cadet__:** {cadet.mention}\n**__Start Time__:** {start_time}\n**__End Time__:** {end_time}\n**__Description__:** {description}\n**__Score__:** {score}%\n**__Result__:** {result.value}',
        color= discord.Color.yellow()
    )
    ra_logtime = datetime.now().strftime('%#m/%#d/%Y %#I:%M %p')
    ra_embed.set_author(name=interaction.user, icon_url=interaction.user.avatar.url)
    ra_embed.set_footer(text=ra_logtime)
    if result.value == 'Passed':
        RA_cc = interaction.guild.get_role(1130263152290971648)
        await interaction.response.send_message(f'Cadet {cadet.display_name} automatically rolled!',ephemeral=True)
        await ral_channel.send(f"CC: {RA_cc.mention}", embed = ra_embed)
        await interaction.followup.send('Logged RA!', ephemeral=True)
    else:
        RA_cc = interaction.guild.get_role(1130263152290971648)
        await ral_channel.send(f"CC: {RA_cc.mention}", embed=ra_embed)
        await interaction.followup.send('Logged RA!', ephemeral=True)

@bot.command(name='purge')
async def purge(ctx, amount: int):
    if amount < 1:
        await ctx.send('Please specify a number greater than 0.', delete_after=5)
        return

    await ctx.channel.purge(limit=amount + 1)  # +1 to include the command message itself
    confirmation = await ctx.send(f'Deleted {amount} message(s).', delete_after=3)

@bot.tree.command(name='page', description='Send a page request!', guild=discord.Object(id=gid))
@app_commands.describe(requesting='Who are you requesting?', postal='Postal code for page request.', reason='Reason for page request.')

async def page(interaction:discord.Interaction, requesting: pagetype, postal: str, reason: str):
    if requesting.value == 'Criminal Investigation Department':
        ping = interaction.guild.get_role(1126591372942651562)
    elif requesting.value == 'Special Weapons and Tactics':
        ping = interaction.guild.get_role(1126588712613072947)
    elif requesting.value == 'Supervisors':
        ping = interaction.guild.get_role(1087222212177694868)
    
    requester = interaction.guild.get_member(interaction.user.id)

    page_embed = discord.Embed(
        title=f'{requesting.value} has been paged by {requester.display_name}',
        description=f'Postal: {postal}\nReason: {reason}',
        color= discord.Color.yellow()
    )

    page_channel = await interaction.guild.fetch_channel(1167256499316330566)
    await page_channel.send(ping.mention, embed=page_embed)
    await interaction.response.send_message(f'Successfully paged {requesting.value}', ephemeral=True)

@bot.tree.command(name='resign', description='Resign from your position here at WSP.', guild=discord.Object(id=gid))
@app_commands.describe(reason='Reason for retirement.')
async def resign(interaction: discord.Interaction, reason: str = None):
    resignation_code = str(random.randint(1000, 10000))
    resign_confirmation[interaction.user.id] = resignation_code

    if reason is None:
        real_reason = 'No reason provided.'
    else:
        real_reason = reason

    resign_reason[interaction.user.id] = real_reason

    await interaction.response.send_message(f'Send `-confirm {resignation_code}` within 30 seconds to complete resignation.', ephemeral=True)

    await asyncio.sleep(30)

    if resign_confirmation.get(interaction.user.id) is not None:
        await interaction.user.send('Resignation Timed Out! Try again using `/resign`')
        resign_confirmation.pop(interaction.user.id, None)
        resign_reason.pop(interaction.user.id, None)

@bot.command(name='confirm')
async def confirm(ctx, *, msg):
    global retirement_view_df
    

    if ctx.author.id not in resign_confirmation or ctx.author.id not in resign_reason:
        await ctx.send('You do not have a pending resignation request.')
        return
    roles = '\n'.join(role.mention for role in ctx.author.roles if role.name != '@everyone')
    dc = ctx.guild.get_role(1087222212198678566)
    adat = ctx.guild.get_role(1166452472378826835)
    swat = ctx.guild.get_role(1126588712613072947)
    patrol = ctx.guild.get_role(1126591623824932945)
    training = ctx.guild.get_role(1130263150378369105)
    cid = ctx.guild.get_role(1126591372942651562)
    tzd = ctx.guild.get_role(1197726231622332426)
    ops = ctx.guild.get_role(1134648918521692230)
    state_employee = ctx.guild.get_role(1087222212177694864)
    former_employee = ctx.guild.get_role(1141096572361384016)
    wsp_role = ctx.guild.get_role(1088013032472457266)
    bar1 = ctx.guild.get_role(1338402064945905765)
    bar2 = ctx.guild.get_role(1338402064656633939)
    bar3 = ctx.guild.get_role(1338402065042505750)

    pt = ctx.guild.get_role(1133180972985229383)
    trooper = ctx.guild.get_role(1087222212177694865)
    mt = ctx.guild.get_role(1133181261297504286)
    corp = ctx.guild.get_role(1088026363384049685)
    serg = ctx.guild.get_role(1087222212177694869)
    lt = ctx.guild.get_role(1087222212198678558)
    cpt = ctx.guild.get_role(1090505585109245993)

    swat_secondary = ctx.guild.get_role(1258825049004310559)
    training_secondary = ctx.guild.get_role(1189267500001673326)
    cid_secondary = ctx.guild.get_role(1360555505734647818)
    ops_secondary = ctx.guild.get_role(1173057887065612318)

    if msg.strip() == resign_confirmation[ctx.author.id]:
        resign_target = ctx.guild.get_member(ctx.author.id)

        division = 'No division found.'
        division_secondary = 'No secondary division.'
        rank = 'No rank found.'

        # Primary Division
        if adat in resign_target.roles:
            division = 'Aggressive Driving Apprehension Team'
            await resign_target.remove_roles(adat)
        elif swat in resign_target.roles:
            division = 'Special Weapons and Tactics'
            await resign_target.remove_roles(swat)
        elif patrol in resign_target.roles:
            division = 'Patrol Division'
            await resign_target.remove_roles(patrol)
        elif training in resign_target.roles:
            division = 'Training Division'
            await resign_target.remove_roles(training)
        elif cid in resign_target.roles:
            division = 'Criminal Investigation Department'
            await resign_target.remove_roles(cid)
        elif tzd in resign_target.roles:
            division = 'Target Zero Division'
            await resign_target.remove_roles(tzd)
        elif ops in resign_target.roles:
            division = 'Office of Professional Standards'
            await resign_target.remove_roles(ops)

        # Secondary Division
        if swat_secondary in resign_target.roles:
            division_secondary = 'Special Weapons and Tactics'
            await resign_target.remove_roles(swat_secondary)
        elif training_secondary in resign_target.roles:
            division_secondary = 'Training Division'
            await resign_target.remove_roles(training_secondary)
        elif cid_secondary in resign_target.roles:
            division_secondary = 'Criminal Investigation Department'
            await resign_target.remove_roles(cid_secondary)
        elif ops_secondary in resign_target.roles:
            division_secondary = 'Office of Professional Standards'
            await resign_target.remove_roles(ops_secondary)

        # Rank
        if pt in resign_target.roles:
            rank = 'Probationary Trooper'
            await resign_target.remove_roles(pt)
        elif trooper in resign_target.roles:
            rank = 'Trooper'
            await resign_target.remove_roles(trooper)
        elif mt in resign_target.roles:
            rank = 'Master Trooper'
            await resign_target.remove_roles(mt)
        elif corp in resign_target.roles:
            rank = 'Corporal'
            await resign_target.remove_roles(corp)
        elif serg in resign_target.roles:
            rank = 'Sergeant'
            await resign_target.remove_roles(serg)
        elif lt in resign_target.roles:
            rank = 'Lieutenant'
            await resign_target.remove_roles(lt)
        elif cpt in resign_target.roles:
            rank = 'Captain'
            await resign_target.remove_roles(cpt)

        # State, WSP, and Bars
        await resign_target.remove_roles(state_employee)
        await resign_target.add_roles(former_employee)
        await resign_target.remove_roles(wsp_role, bar1, bar2, bar3)

        view_rolesbutton = Button(label='View Roles ', style=discord.ButtonStyle.green)
        async def view_rolescallback(interaction:discord.Interaction):
            member = interaction.guild.get_member(interaction.user.id)
            embed = discord.Embed(
                title=f"{member.display_name}'s Roles",
                description=roles,
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        view=View(timeout=None)
        view.add_item(view_rolesbutton)
        view_rolesbutton.callback = view_rolescallback

        resign_embed = discord.Embed(
            title='Resignation Log',
            description=f'**__Trooper__**: {ctx.author.display_name}\n'
                        f'**__Reason__**: {resign_reason[ctx.author.id]}\n'
                        f'**__Division__**: {division}\n'
                        f'**__Secondary Division__**: {division_secondary}\n'
                        f'**__Rank__**: {rank}\n\n'
                        f'Please complete the resignation process.',
            color=discord.Color.yellow()
        )

        retirement_entry = {
            'User': resign_target,
            'Reason': resign_reason[ctx.author.id],
            'Primary Division': division,
            'Secondary Division': division_secondary,
            'Rank': rank
        }

        retirement_view_df = pd.concat([retirement_view_df, pd.DataFrame([retirement_entry])], ignore_index=True)
        save_retirementview()

        resign_channel = await ctx.guild.fetch_channel(1181394493468057641)
        await resign_channel.send(embed=resign_embed, view=view)
        await ctx.author.send('You have resigned successfully in WSP! Please wait while Department Command fully processes your resignation!')

        resign_confirmation.pop(ctx.author.id, None)
        resign_reason.pop(ctx.author.id, None)
    else:
        await ctx.send('Invalid resignation code.')

    await ctx.message.delete()

@bot.tree.command(name='cadetexamresult', description='Submit a cadet exam result.', guild=discord.Object(id=gid))
@app_commands.describe(cadet='Cadet name.', result='Result of the exam.', notes='Notes of the exam.')

async def cadetexamresult(interaction:discord.Interaction, cadet:discord.User, result: cadetexamresult, notes: str):
    global cadet_exam_df

    cadetresult_entry = {
        'Cadet': cadet.id,
        'Result': result.value,
        'Notes': notes
    }
    cadet_exam_df = pd.concat([cadet_exam_df, pd.DataFrame([cadetresult_entry])], ignore_index=True)
    save_cadetexam()

    if result.value == 'Passed':
        embed_color = discord.Color.green()
    else:
        embed_color = discord.Color.red()

    touser_embed = discord.Embed(
        title='Cadet Exam Result',
        color = embed_color
    )

    examiner = interaction.guild.get_member(interaction.user.id)

    touser_embed.add_field(name='**__Cadet__**', value=f'{cadet.display_name} ({cadet.id})', inline=True)
    touser_embed.add_field(name='**__Result__**', value=result.value, inline=True)
    touser_embed.add_field(name='**__Notes__**', value=notes, inline=True)
    
    tolog_embed = discord.Embed(
        title='Cadet Exam Result',
        color = embed_color
    )

    tolog_embed.add_field(name='**__Cadet__**', value=f'{cadet.display_name} ({cadet.id})', inline=True)
    tolog_embed.add_field(name='**__Result__**', value=result.value, inline=True)
    tolog_embed.add_field(name='**__Notes__**', value=notes, inline=True)

    tolog_embed.set_footer(text=f'Examiner: {examiner.display_name} | {examiner.id}')

    await cadet.send(embed=touser_embed)
    await interaction.response.send_message('Logged exam results.', ephemeral=True)

    exam_log = await interaction.guild.fetch_channel(1231748344217604186)
    await exam_log.send(embed=tolog_embed)

@bot.tree.command(name='viewcadetexam', description='View the cadet exam of a cadet.',guild=discord.Object(id=gid))
@app_commands.describe(cadet='Cadet to check.')

async def viewcadetexam(interaction:discord.Interaction, cadet:discord.User):
    try:

        global cadet_exam_df

        user_df = cadet_exam_df[cadet_exam_df['Cadet'] == cadet.id]

        if user_df.empty:
            no_exam_embed = discord.Embed(
                title=f'Cadet Exam History for {cadet.display_name}',
                description='No exam records found for this cadet.',
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=no_exam_embed,ephemeral=True)
            return

        hist_embed = discord.Embed(
            title=f'Cadet Exam History for {cadet.display_name}',
            color=discord.Color.blue()
        )

        exam_hist = ''
        for idx,row in user_df.iterrows():
            hist_embed.add_field(name='Cadet', value=cadet.display_name, inline=True)
            hist_embed.add_field(name='Result', value=row['Result'], inline=True)
            hist_embed.add_field(name='Notes', value=row['Notes'], inline=True)
        
        await interaction.response.send_message(embed=hist_embed, ephemeral=True)
    except Exception:
        exception_embed = discord.Embed(
            title=f'Error using `/`',
            description=f"```{Exception}```",
            color=discord.Color.red()
        )
        channel = await interaction.guild.fetch_channel(1389599317311881276)
        await channel.send(exception_embed)

@bot.tree.command(name='sergeantexamresult', description='Log a sergeant exam.', guild=discord.Object(id=gid))
@app_commands.describe(user='Username of exam taker.', result='Result of the exam.', notes='Exam notes.')
async def sergeantexamresult(interaction: discord.Interaction, user: discord.User, result: sergeantexamresult, notes: str):
    try:
        await interaction.response.defer(ephemeral=True)
        global sergeant_exam_df

        sergeantexam_entry = {
            'User': user.id,  # Store user ID, not username
            'Result': result.value,
            'Notes': notes
        }

        sergeant_exam_df = pd.concat([sergeant_exam_df, pd.DataFrame([sergeantexam_entry])], ignore_index=True)
        save_sergeantexam()

        embed_color = discord.Color.green() if result.value == 'Passed' else discord.Color.red()

        touser_embed = discord.Embed(
            title='Sergeant Exam Result',
            color=embed_color
        )

        examiner = interaction.guild.get_member(interaction.user.id)

        touser_embed.add_field(name='**__User__**', value=f'{user.display_name} ({user.id})', inline=True)
        touser_embed.add_field(name='**__Result__**', value=result.value, inline=True)
        touser_embed.add_field(name='**__Notes__**', value=notes, inline=True)

        tolog_embed = discord.Embed(
            title='Sergeant Exam Result',
            color=embed_color
        )

        tolog_embed.add_field(name='**__User__**', value=f'{user.display_name} ({user.id})', inline=True)
        tolog_embed.add_field(name='**__Result__**', value=result.value, inline=True)
        tolog_embed.add_field(name='**__Notes__**', value=notes, inline=True)

        tolog_embed.set_footer(text=f'Examiner: {examiner.display_name} | {examiner.id}')

        try:
            await user.send(embed=touser_embed)
        except discord.Forbidden:
            await interaction.followup.send('Could not send a DM to the user. Please make sure their DMs are open.', ephemeral=True)

        await interaction.followup.send('Logged exam results.', ephemeral=True)

        exam_log = await interaction.guild.fetch_channel(1231748344217604186)
        await exam_log.send(embed=tolog_embed)
    except Exception:
        exception_embed = discord.Embed(
            title=f'Error using `/sergeantexamresult`',
            description=f"```{Exception}```",
            color=discord.Color.red()
        )
        channel = await interaction.guild.fetch_channel(1389599317311881276)
        await channel.send(exception_embed)


@bot.tree.command(name='viewsergeantexam', description='View the sergeant exam of a user.', guild=discord.Object(id=gid))
@app_commands.describe(user='User to check.')
async def viewsergeantexam(interaction: discord.Interaction, user: discord.User):
    try:

        await interaction.response.defer(ephemeral=True)
        global sergeant_exam_df

        user_df = sergeant_exam_df[sergeant_exam_df['User'] == user.id]

        if user_df.empty:
            no_exam_embed = discord.Embed(
                title=f'Sergeant Exam History: {user.display_name}',
                description='No exam records found for this user.',
                color=discord.Color.blue()
            )
            await interaction.followup.send(embed=no_exam_embed, ephemeral=True)
            return

        hist_embed = discord.Embed(
            title=f'Sergeant Exam History for {user.display_name}',
            color=discord.Color.blue()
        )

        for idx, row in user_df.iterrows():
            hist_embed.add_field(name='User', value=user.display_name, inline=True)
            hist_embed.add_field(name='Result', value=row['Result'], inline=True)
            hist_embed.add_field(name='Notes', value=row['Notes'], inline=True)

        await interaction.followup.send(embed=hist_embed, ephemeral=True)
    except Exception:
        exception_embed = discord.Embed(
            title=f'Error using `/viewsergeantexam`',
            description=f"```{Exception}```",
            color=discord.Color.red()
        )
        channel = await interaction.guild.fetch_channel(1389599317311881276)
        await channel.send(exception_embed)
@bot.tree.command(name='trooperfeedback', description='Give feedback about a trooper.',guild=discord.Object(id=gid))
@app_commands.describe(trooper='Trooper to give feedback to.', rating='Rating you wish to give.', feedback='Feedback description.')

async def trooperfeedback(interaction:discord.Interaction, trooper: discord.User, rating: int, feedback: str):
    try:
        if (rating>5) or (rating<=0):
            await interaction.response.send_message('Please enter a valid rating value (1 to 5)',ephemeral=True)
            return

        feedback_embed = discord.Embed(
            title='**__WSP Trooper Feedback__**',
            color = discord.Color.yellow()
        )

        feedback_embed.add_field(name='**Trooper**', value=trooper.mention, inline=True)
        feedback_embed.add_field(name='**Rating**', value=rating, inline=True)
        feedback_embed.add_field(name='**Feedback**', value=feedback, inline=False)

        feedback_giver = interaction.guild.get_member(interaction.user.id)

        feedback_embed.set_footer(icon_url=feedback_giver.display_avatar,text=f'Feedback by: {feedback_giver.display_name}')

        feedback_channel = await interaction.guild.fetch_channel(1146830003267440660)

        await feedback_channel.send(embed=feedback_embed)
    except Exception:
        exception_embed = discord.Embed(
            title=f'Error using `/trooperfeedback`',
            description=f"```{Exception}```",
            color=discord.Color.red()
        )
        channel = await interaction.guild.fetch_channel(1389599317311881276)
        await channel.send(exception_embed)

@bot.tree.command(name='viewretirement', description='View the retirement of a user.', guild=discord.Object(id=gid))
@app_commands.describe(user='User to check retirement of.')

async def viewretirement(interaction:discord.Interaction, user: discord.User):
    try:
        await interaction.response.defer(ephemeral=True)
        global retirement_view_df

        user_df = retirement_view_df[retirement_view_df['User'] == user]

        if retirement_view_df.empty:
            no_exam_embed = discord.Embed(
                title=f'Retirement History for {user.display_name}',
                description='No retirement records found for this user.',
                color=discord.Color.blue()
            )
            await interaction.followup.send(embed=no_exam_embed, ephemeral=True)
            return

        desc = ''

        for idx, row in user_df.iterrows():
            desc = f"User: {row['User']}\nReason: {row['Reason']}\nPrimary Division: {row['Primary Division']}\nSecondary Division: {row['Secondary Division']}\nRank: {row['Rank']}"
        
        embed = discord.Embed(
            title=f'Retirement history of {user}',
            description= desc,
            color=discord.Color.blue()
        )

        await interaction.followup.send(embed=embed)
    except Exception:
        exception_embed = discord.Embed(
            title=f'Error using `/viewretirement`',
            description=f"```{Exception}```",
            color=discord.Color.red()
        )
        channel = await interaction.guild.fetch_channel(1389599317311881276)
        await channel.send(exception_embed)
@bot.tree.command(name='startprobation', description='Allowed TD and Patrol Command to start the probation of a trooper.', guild=discord.Object(id=gid))
@app_commands.describe(cadet='Cadet to start probation for.')

async def startprobation(interaction:discord.Interaction, cadet: discord.User):
    try:
        interaction_user = interaction.guild.get_member(interaction.user.id)
        start_dt = datetime.now()
        end_dt = start_dt + timedelta(days=7)
        start_time = start_dt.strftime('%#m/%#d/%Y %#I:%M %p')
        endtime = end_dt.strftime('%#m/%#d/%Y %#I:%M %p')
        start_embed = discord.Embed(
            title=f'__Probation started for {cadet.display_name}__',
            description=f'**Cadet**: {cadet.display_name} | {cadet.id}\n**Started on**: {start_time}\n**Ends on**: {endtime}\n**Initiated by**: {interaction_user.display_name}',
            color = discord.Color.yellow()
        )
        start_embed.set_author(name=cadet.display_name, icon_url=cadet.display_avatar.url)
        channel = await interaction.guild.fetch_channel(1388183244238885015) # TO BE CHANGED
        await channel.send(embed=start_embed)
        await interaction.response.send_message(f'Started {cadet.display_name} probation!', ephemeral=True)
        awaiting_probation.add(cadet.id)
        await asyncio.sleep(60*60*24*7)
        if cadet.id in awaiting_probation:

            end_embed = discord.Embed(
                title=f'__Probation ended for {cadet.display_name}__',
                description=f'**Cadet**: {cadet.display_name} | {cadet.id}\n**Started on**: {start_time}\n**Ended on**: {endtime}\n**Initiated by**: {interaction_user.display_name}]\n\nPlease complete their probation.',
                color = discord.Color.yellow()
            )

            patrol_role = interaction.guild.get_role(1130261043952746559)

            await channel.send(patrol_role.mention, embed=end_embed)
        else:
            return
    except Exception:
        exception_embed = discord.Embed(
            title=f'Error using `/startprobation`',
            description=f"```{Exception}```",
            color=discord.Color.red()
        )
        channel = await interaction.guild.fetch_channel(1389599317311881276)
        await channel.send(exception_embed)

@bot.tree.command(name='stopprobation', description='Stop the probation of a trooper.',guild=discord.Object(id=gid))
@app_commands.describe(trooper='Trooper to stop probation on.', reason='Reason of stopping probation.')

async def stopprobation(interaction:discord.Interaction, trooper: discord.User, reason: str):
    try:
        interaction_user = interaction.guild.get_member(interaction.user.id)
        if trooper.id not in awaiting_probation:
            await interaction.response.send_message('Trooper is not in probation.',ephemeral=True)
            return
        stop_embed = discord.Embed(
            title=f'Probation stopped for {trooper.display_name}',
            description=f'**Trooper**: {trooper.display_name}\n**Reason**: {reason}\n**Stopped by**: {interaction_user.display_name}',
            color=discord.Color.yellow()
        )

        patrol_role = interaction.guild.get_role(1130261043952746559)
        channel = await interaction.guild.fetch_channel(1388183244238885015) # TO BE CHANGED
        await channel.send(patrol_role.mention, embed=stop_embed)
        await interaction.response.send_message(f'Removed {trooper.display_name} from probation.',ephemeral=True)
        awaiting_probation.remove(trooper.id)
    except Exception:
        exception_embed = discord.Embed(
            title=f'Error using `/stopprobation`',
            description=f"```{Exception}```",
            color=discord.Color.red()
        )
        channel = await interaction.guild.fetch_channel(1389599317311881276)
        await channel.send(exception_embed)

@bot.tree.command(name='hrdlog', description='Log Human Resource Department cases.', guild=discord.Object(id=gid))
@app_commands.describe(case_number = 'Case number', type='Case type.', ticket_opener='Who opened the ticket?', ticket_reviewer='Who handled the ticket?', outcome='Ticket outcome.', reason='Reason for the outcome.', additional_notes = 'Additional Notes.')

async def hrdlog(interaction:discord.Interaction,case_number: int, type: hrdlogtypes, ticket_opener: discord.User, ticket_reviewer: discord.User, outcome: hrdlogoutcome, reason: str, additional_notes: str = None):
    try:
        interaction_user = interaction.guild.get_member(interaction.user.id)
        interaction_time = datetime.now().strftime('%#m/%#d/%Y %#I:%M %p')

        if additional_notes == None:
            truean = 'No additional notes provided.'
        else:
            truean = additional_notes
        hrdlogembed = discord.Embed(
            title=f'Case #{case_number}',
            description=f'**Case Type**: {type.value}\n**Ticket Opener**: {ticket_opener.display_name}\n**Ticket Reviewer**: {ticket_reviewer.display_name}\n**Outcome**: {outcome.value}\n**Reason**: {reason}\n**Additional Notes**: {truean}',
            color=discord.Color.yellow()
        )

        hrdlogembed.set_author(name=interaction_user.display_name, icon_url=interaction_user.display_avatar)
        hrdlogembed.set_footer(text=interaction_time)

        channel = await interaction.guild.fetch_channel(1251185583313784873)
        hrdc_ping = interaction.guild.get_role(1272100535020945491)
        await channel.send(f'CC: {hrdc_ping.mention}',embed=hrdlogembed)

        await interaction.response.send_message(f'Logged case #{hrd_casenumber} successfully.', ephemeral=True)
    except Exception as e:
        exception_embed = discord.Embed(
            title=f'Error using `/hrdlog`',
            description=f"```Error: {e}\nUsed by: {interaction.user}```",
            color=discord.Color.red()
        )
        channel = await interaction.guild.fetch_channel(1389599317311881276)
        await channel.send(embed=exception_embed)
@bot.command(name="accept")
async def accept(ctx, username: str):
    try:
        user = ctx.guild.get_member(ctx.author.id)
        dc_role = ctx.guild.get_role(1087222212198678566)
        td_role = ctx.guild.get_role(1130263150378369105)
        wsp_automation_role = ctx.guild.get_role(1383493172906164427)

        if dc_role in user.roles or td_role in user.roles or wsp_automation_role in user.roles:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "usernames": [username],
                    "excludeBannedUsers": True
                }
                async with session.post("https://users.roblox.com/v1/usernames/users", json=payload) as resp:
                    if resp.status != 200:
                        await ctx.send("Failed to contact Roblox.",delete_after=5)
                        return
                    data = await resp.json()
                    if not data.get("data"):
                        await ctx.send("Invalid Roblox username.",delete_after=5)
                        return
                    user_id = data["data"][0]["id"]

                async with session.get(f"https://apis.roblox.com/cloud/v2/groups/{GROUP_ID}/join-requests", headers=HEADERS) as resp:
                    if resp.status != 200:
                        await ctx.send("Failed to fetch join requests.",delete_after=5)
                        return

                    join_data = await resp.json()

                    print(join_data)

                    pending_ids = []
                    for item in join_data.get("groupJoinRequests", []):
                        if "user" in item and item["user"].startswith("users/"):
                            pending_ids.append(item["user"].split("/")[-1])

                if str(user_id) not in pending_ids:
                    await ctx.send("That user does not have a pending join request.",delete_after=5)
                    return

                accept_url = f"https://apis.roblox.com/cloud/v2/groups/{GROUP_ID}/join-requests/{user_id}:accept"
                async with session.post(accept_url, headers=HEADERS, json={}) as accept_resp:
                    if accept_resp.status in [204,200]:
                        await ctx.send(f"Accepted `{username}` into the group!",delete_after=5)
                    else:
                        error_text = await accept_resp.text()
                        await ctx.send(f"Error: `{error_text}`")
                await ctx.message.delete()
        else:
            await ctx.send('No permissions!', delete_after=5)
    except Exception:
        exception_embed = discord.Embed(
            title=f'Error using `-accept`',
            description=f"This is quite literally impossible, I don't know how we got here, but here you go: `{Exception}`",
            color=discord.Color.red()
        )
        channel = await ctx.guild.fetch_channel(1389599317311881276)
        await channel.send(exception_embed)

@bot.tree.command(name='duilog', guild=discord.Object(id=gid))
@app_commands.describe(suspect='Suspect involved.', reason='Reason for DUI test.', location='Location of DUI test.', intoxicated='Were they intoxicated?')

async def duilog(interaction:discord.Interaction, suspect:str, reason: str, location: str, intoxicated: intoxicated):
    global duilogcounter
    duilogcounter = duilogcounter+1
    testing_trooper = interaction.guild.get_member(interaction.user.id)
    log_time = datetime.now().strftime('%#m/%#d/%Y %#I:%M %p')
    logembed = discord.Embed(
        title=f'__DUI Log #{duilogcounter}__',
        description=f'**Suspect Involved**\n{suspect}\n\n**Reason**\n{reason}\n\n**Location**\n{location}\n\n**Were they intoxicated?**\n{intoxicated.value}',
        color=discord.Color.yellow()
    )

    logembed.set_author(name=f'Testing Trooper: {testing_trooper.display_name}', icon_url=testing_trooper.display_avatar)
    logembed.set_footer(text=log_time)

    channel = await interaction.guild.fetch_channel(1317171645416476783)
    await channel.send(embed=logembed)
    await interaction.response.send_message('DUI logged!',ephemeral=True)

@bot.tree.command(name='feedback', description='Send feedback directly to the developer.', guild=discord.Object(id=gid))
@app_commands.describe(feedback='What is your feedback? It can include suggestions, bug reports, or general feedback.')

async def feedback(interaction:discord.Interaction,feedback:str):
    user = interaction.guild.get_member(interaction.user.id)
    fb_emb = discord.Embed(
        title=f'Feedback received',
        description=f'User: {user.display_name}\nFeedback: {feedback}',
        color=discord.Color.green()
    )

    dev = await interaction.guild.fetch_member(749176943353528352)
    await dev.send(embed=fb_emb)
    await interaction.response.send_message('Feedback sent sucessfully! Thank you for your feedback. You will be contacted in the future if needed.',ephemeral=True)

@bot.command(name='sendrrembedwithrrroles')
async def sendrrembedwithrrroles(ctx):
    Bot_dev_role = ctx.guild.get_role(1383493172906164427)
    member = ctx.guild.get_member(749176943353528352)
    if ctx.author.guild_permissions.administrator or Bot_dev_role in member.roles:
        embed = discord.Embed(
            title='**Reaction Roles**',
            description="Select a button below to assign yourself a reaction role. You'll receive a notification whenever that role is mentioned.",
            color=discord.Color.yellow()
        )
        QOTD_ping = Button(label='QOTD', style=discord.ButtonStyle.gray)
        async def QOTD_callback(interaction:discord.Interaction):
            QOTD_role = interaction.guild.get_role(1158850023598080092)
            member = interaction.guild.get_member(interaction.user.id)
            if QOTD_role not in member.roles:
                await member.add_roles(QOTD_role)
                await interaction.response.send_message('Added QOTD role!',ephemeral=True)
            elif QOTD_role in member.roles:
                await member.remove_roles(QOTD_role)
                await interaction.response.send_message('Removed QOTD role!',ephemeral=True)

        event_ping = Button(label='Event Ping', style=discord.ButtonStyle.gray)
        async def event_callback(interaction:discord.Interaction):
            event_role = interaction.guild.get_role(1399407993514233958)
            member = interaction.guild.get_member(interaction.user.id)
            if event_role not in member.roles:
                await member.add_roles(event_role)
                await interaction.response.send_message('Added Event Ping role!',ephemeral=True)
            elif event_role in member.roles:
                await member.remove_roles(event_role)
                await interaction.response.send_message('Removed Event Ping role!',ephemeral=True)

        press_ping = Button(label='Press Ping', style=discord.ButtonStyle.gray)
        async def press_callback(interaction:discord.Interaction):
            press_role = interaction.guild.get_role(1401950277518753962)
            member = interaction.guild.get_member(interaction.user.id)
            if press_role not in member.roles:
                await member.add_roles(press_role)
                await interaction.response.send_message('Added Press Ping role!',ephemeral=True)
            elif press_role in member.roles:
                await member.remove_roles(press_role)
                await interaction.response.send_message('Removed Press Ping role!',ephemeral=True)
        
        weaklyreport_ping = Button(label='Weekly Reports Ping', style=discord.ButtonStyle.gray)
        async def weakly_callback(interaction:discord.Interaction):
            weaklyreport_ping_role = interaction.guild.get_role(1401950176985219072)
            member = interaction.guild.get_member(interaction.user.id)
            if weaklyreport_ping_role not in member.roles:
                await member.add_roles(weaklyreport_ping_role)
                await interaction.response.send_message('Added Weekly Reports Ping role!',ephemeral=True)
            elif weaklyreport_ping_role in member.roles:
                await member.remove_roles(weaklyreport_ping_role)
                await interaction.response.send_message('Removed Weekly Reports Ping role!',ephemeral=True)
            
        QOTD_ping.callback = QOTD_callback
        event_ping.callback = event_callback
        press_ping.callback = press_callback
        weaklyreport_ping.callback = weakly_callback
        view=View(timeout=None)
        view.add_item(QOTD_ping)
        view.add_item(event_ping)
        view.add_item(press_ping)
        view.add_item(weaklyreport_ping)
        message = ctx.message
        await ctx.send(embed=embed, view=view)
        await message.delete()

@bot.command(name='start_loop')
async def start_loop(ctx):
    Bot_dev_role = ctx.guild.get_role(1383493172906164427)
    member = ctx.guild.get_member(749176943353528352)
    if ctx.author.guild_permissions.administrator or Bot_dev_role in member.roles:
        send_division_reminder.start()
        await ctx.send('Started division reminder loop', delete_after=5)
    else:
        await ctx.send('No permissions!', delete_after=5)

bot.run()
