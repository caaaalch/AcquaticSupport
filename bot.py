import os

import discord
from discord.ext import commands
from discord.ui import Button, View
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")

# Configurazione
SUPPORT_PANEL_ROLE = 1528389285798220017
SUPPORT_CATEGORY_ID = 1525198804746244339
STAFF_ROLE_ID = 1528389285798220017

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


class SupportView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🎧 Richiedi assistenza",
        style=discord.ButtonStyle.green,
        custom_id="support_button"
    )
    async def support(
        self,
        interaction: discord.Interaction,
        button: Button
    ):

        guild = interaction.guild
        user = interaction.user

        # Controlla se ha già un'assistenza aperta
        existing_channel = discord.utils.get(
            guild.voice_channels,
            name=f"assistenza-{user.name}"
        )

        if existing_channel:
            await interaction.response.send_message(
                "❌ Hai già una richiesta di assistenza aperta.",
                ephemeral=True
            )
            return

        category = guild.get_channel(SUPPORT_CATEGORY_ID)
        staff_role = guild.get_role(STAFF_ROLE_ID)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                view_channel=False
            ),

            user: discord.PermissionOverwrite(
                view_channel=True,
                connect=True,
                speak=True
            ),

            staff_role: discord.PermissionOverwrite(
                view_channel=True,
                connect=True,
                speak=True
            )
        }

        channel = await guild.create_voice_channel(
            name=f"assistenza-{user.name}",
            category=category,
            overwrites=overwrites
        )

        await interaction.response.send_message(
            f"✅ Canale creato: {channel.mention}",
            ephemeral=True
        )

        # Sposta l'utente nel vocale
        if user.voice:
            await user.move_to(channel)
        else:
            await interaction.followup.send(
                "🎧 Entra nel canale appena creato per iniziare l'assistenza.",
                ephemeral=True
            )


@bot.event
async def on_ready():
    bot.add_view(SupportView())
    print(f"{bot.user} è online!")


@bot.command()
async def pannello(ctx):

    ruolo = ctx.guild.get_role(SUPPORT_PANEL_ROLE)

    if ruolo not in ctx.author.roles:
        await ctx.send(
            "❌ Non hai il permesso di creare il pannello assistenza.",
            delete_after=5
        )
        return

    embed = discord.Embed(
        title="🎧 Assistenza",
        description="Premi il pulsante qui sotto per richiedere assistenza.",
        color=discord.Color.blue()
    )

    embed.set_footer(
        text="Sistema assistenza"
    )

    await ctx.send(
        embed=embed,
        view=SupportView()
    )


bot.run(TOKEN)