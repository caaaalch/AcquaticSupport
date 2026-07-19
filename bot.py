import os

import discord
from discord.ext import commands
from discord.ui import Button, View
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")

# CONFIGURAZIONE ID
PANEL_ROLE_ID = 1528389285798220017
STAFF_ROLE_ID = 1528389285798220017

SUPPORT_CATEGORY_ID = 1525198804746244339
REQUEST_CHANNEL_ID = 1525198804746244340
LOG_CHANNEL_ID = 1528390401160118343


# salva proprietari assistenze
support_owners = {}


intents = discord.Intents.default()
intents.members = True
intents.message_content = True


bot = commands.Bot(
    command_prefix="!",
    intents=intents
)



# ==========================
# CHIUSURA ASSISTENZA
# ==========================

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

        channel = interaction.guild.get_channel(
            support_owners.get(interaction.user.id)
        )

        user = interaction.user

        staff_role = interaction.guild.get_role(
            STAFF_ROLE_ID
        )


        # controlla permessi

        allowed = False


        if staff_role in user.roles:
            allowed = True


        if interaction.user.id in support_owners:
            allowed = True



        if not allowed:
            await interaction.response.send_message(
                "❌ Non puoi chiudere questa assistenza.",
                ephemeral=True
            )
            return



        log = interaction.guild.get_channel(
            LOG_CHANNEL_ID
        )


        if log:

            embed = discord.Embed(
                title="🔒 Assistenza chiusa",
                color=discord.Color.red()
            )

            embed.add_field(
                name="Chiusa da",
                value=user.mention
            )

            await log.send(
                embed=embed
            )


        await interaction.response.send_message(
            "✅ Assistenza chiusa.",
            ephemeral=True
        )


        if channel:
            await channel.delete()



# ==========================
# APERTURA ASSISTENZA
# ==========================

class SupportView(View):

    def __init__(self):
        super().__init__(timeout=None)



    @discord.ui.button(
        label="🎧 Richiedi assistenza",
        style=discord.ButtonStyle.green,
        custom_id="open_support"
    )
    async def support(
        self,
        interaction: discord.Interaction,
        button: Button
    ):

        guild = interaction.guild
        user = interaction.user


        # evita doppioni

        for owner in support_owners:
            if owner == user.id:

                await interaction.response.send_message(
                    "❌ Hai già una assistenza aperta.",
                    ephemeral=True
                )

                return



        category = guild.get_channel(
            SUPPORT_CATEGORY_ID
        )


        staff_role = guild.get_role(
            STAFF_ROLE_ID
        )



        overwrites = {

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
            overwrites=overwrites
        )


        # salva proprietario

        support_owners[user.id] = voice.id



        # avviso staff

        request_channel = guild.get_channel(
            REQUEST_CHANNEL_ID
        )


        if request_channel:

            await request_channel.send(
                f"🚨 Nuova richiesta assistenza!\n\n"
                f"{staff_role.mention}\n"
                f"Utente: {user.mention}\n"
                f"Canale: {voice.mention}"
            )



        # messaggio privato

        embed = discord.Embed(
            title="🎧 Assistenza aperta",
            description=
            f"Il tuo canale è stato creato:\n\n"
            f"{voice.mention}\n\n"
            "Quando hai finito premi il pulsante qui sotto.",
            color=discord.Color.blue()
        )


        await interaction.response.send_message(
            embed=embed,
            view=CloseSupportView(),
            ephemeral=True
        )



        # sposta utente

        if user.voice:

            await user.move_to(
                voice
            )





# ==========================
# READY
# ==========================

@bot.event
async def on_ready():

    bot.add_view(
        SupportView()
    )

    bot.add_view(
        CloseSupportView()
    )

    print(
        f"{bot.user} è online!"
    )





# ==========================
# CREAZIONE PANNELLO
# ==========================

@bot.command()
async def pannello(ctx):

    role = ctx.guild.get_role(
        PANEL_ROLE_ID
    )


    if role not in ctx.author.roles:

        await ctx.send(
            "❌ Non puoi creare il pannello.",
            delete_after=5
        )

        return



    embed = discord.Embed(
        title="🎧 Supporto",
        description=
        "Premi il pulsante qui sotto per richiedere assistenza.",
        color=discord.Color.blue()
    )


    await ctx.send(
        embed=embed,
        view=SupportView()
    )





bot.run(TOKEN)