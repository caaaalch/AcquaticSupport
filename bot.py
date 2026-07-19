import os

import discord
from discord.ext import commands
from discord.ui import Button, View
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")

# ID ruolo che può creare il pannello
SUPPORT_PANEL_ROLE = 1528389285798220017

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
        await interaction.response.send_message(
            "✅ Richiesta assistenza ricevuta!",
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