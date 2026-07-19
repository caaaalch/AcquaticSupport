import os
import asyncio

import discord
from discord.ext import commands
from discord.ui import Button, View
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")


# ======================
# CONFIG
# ======================

PANEL_ROLE_ID = 1528389285798220017
STAFF_ROLE_ID = 1528389285798220017

SUPPORT_CATEGORY_ID = 1525198804746244339
REQUEST_CHANNEL_ID = 1525198804746244340
LOG_CHANNEL_ID = 1528390401160118343


# memoria assistenze
support_channels = {}


# ======================
# BOT
# ======================

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.voice_states = True


bot = commands.Bot(
    command_prefix="!",
    intents=intents
)



# ======================
# CHIUSURA
# ======================

class CloseSupportView(View):

    def __init__(self):
        super().__init__(timeout=None)


    @discord.ui.button(
        label="🔒 Chiudi assistenza",
        style=discord.ButtonStyle.red,
        custom_id="close_support"
    )
    async def close(
        self,
        interaction: discord.Interaction,
        button: Button
    ):

        user = interaction.user
        guild = interaction.guild

        staff_role = guild.get_role(
            STAFF_ROLE_ID
        )


        channel_id = None


        for voice_id, owner_id in support_channels.items():

            if owner_id == user.id:
                channel_id = voice_id
                break


            if staff_role in user.roles:
                channel_id = voice_id
                break



        if channel_id is None:

            await interaction.response.send_message(
                "❌ Non puoi chiudere questa assistenza.",
                ephemeral=True
            )

            return



        channel = guild.get_channel(
            channel_id
        )


        log = guild.get_channel(
            LOG_CHANNEL_ID
        )


        if log:

            await log.send(
                f"🔒 **Assistenza chiusa**\n"
                f"Da: {user.mention}\n"
                f"Canale: `{channel.name}`"
            )


        await interaction.response.send_message(
            "✅ Assistenza chiusa.",
            ephemeral=True
        )


        if channel:

            await channel.delete()



        support_channels.pop(
            channel_id,
            None
        )





# ======================
# APERTURA
# ======================

class SupportView(View):

    def __init__(self):
        super().__init__(timeout=None)



    @discord.ui.button(
        label="🎧 Richiedi assistenza",
        style=discord.ButtonStyle.green,
        custom_id="support_open"
    )
    async def open(
        self,
        interaction: discord.Interaction,
        button: Button
    ):

        guild = interaction.guild
        user = interaction.user



        # controlla doppio ticket

        if user.id in support_channels.values():

            await interaction.response.send_message(
                "❌ Hai già un'assistenza aperta.",
                ephemeral=True
            )

            return



        category = guild.get_channel(
            SUPPORT_CATEGORY_ID
        )


        staff_role = guild.get_role(
            STAFF_ROLE_ID
        )



        permissions = {

            guild.default_role:
            discord.PermissionOverwrite(
                view_channel=False
            ),


            user:
            discord.PermissionOverwrite(
                view_channel=True,
                connect=True,
                speak=True
            ),


            staff_role:
            discord.PermissionOverwrite(
                view_channel=True,
                connect=True,
                speak=True
            )

        }



        voice = await guild.create_voice_channel(
            name=f"assistenza-{user.name}",
            category=category,
            overwrites=permissions
        )



        support_channels[voice.id] = user.id



        # ping staff

        request = guild.get_channel(
            REQUEST_CHANNEL_ID
        )


        if request:

            await request.send(

                f"🚨 **Nuova richiesta assistenza!**\n"
                f"{staff_role.mention}\n"
                f"Utente: {user.mention}\n"
                f"Canale: {voice.mention}",

                allowed_mentions=discord.AllowedMentions(
                    roles=True,
                    users=True
                )

            )



        # risposta privata

        embed = discord.Embed(

            title="🎧 Assistenza aperta",

            description=
            f"Il tuo canale è stato creato:\n\n"
            f"{voice.mention}\n\n"
            "Quando hai finito premi il pulsante.",

            color=discord.Color.blue()

        )



        await interaction.response.send_message(

            embed=embed,

            view=CloseSupportView(),

            ephemeral=True

        )



        # sposta

        if user.voice:

            await user.move_to(
                voice
            )





# ======================
# AUTO DELETE USCITA
# ======================

@bot.event
async def on_voice_state_update(
    member,
    before,
    after
):

    if before.channel is None:
        return


    channel = before.channel


    if channel.id not in support_channels:
        return



    owner_id = support_channels[channel.id]



    if member.id == owner_id:


        await asyncio.sleep(5)



        if len(channel.members) == 0:


            log = channel.guild.get_channel(
                LOG_CHANNEL_ID
            )


            if log:

                await log.send(
                    f"🗑️ Assistenza terminata automaticamente\n"
                    f"Utente: {member.mention}\n"
                    f"Canale: `{channel.name}`"
                )


            await channel.delete()


            support_channels.pop(
                channel.id,
                None
            )





# ======================
# READY
# ======================

@bot.event
async def on_ready():

    bot.add_view(
        SupportView()
    )

    bot.add_view(
        CloseSupportView()
    )

    print(
        f"{bot.user} online!"
    )





# ======================
# PANNELLO
# ======================

@bot.command()
async def pannello(ctx):

    role = ctx.guild.get_role(
        PANEL_ROLE_ID
    )


    if role not in ctx.author.roles:

        await ctx.send(
            "❌ Non hai il permesso.",
            delete_after=5
        )

        return



    embed = discord.Embed(

        title="🎧 Supporto",

        description=
        "Premi il pulsante per richiedere assistenza.",

        color=discord.Color.blue()

    )


    await ctx.send(

        embed=embed,

        view=SupportView()

    )





bot.run(TOKEN)