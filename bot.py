import os
import json
import asyncio
from datetime import datetime

import discord
from discord.ext import commands
from discord.ui import Button, View
from dotenv import load_dotenv


load_dotenv()

TOKEN = os.getenv("TOKEN")


# =========================
# CONFIGURAZIONE
# =========================

PANEL_ROLE_ID = 1528389285798220017
STAFF_ROLE_ID = 1528389285798220017

SUPPORT_CATEGORY_ID = 1525198804746244339

REQUEST_CHANNEL_ID = 1525198804746244340

LOG_CHANNEL_ID = 1528390401160118343


TICKETS_FILE = "tickets.json"



# =========================
# DATABASE JSON
# =========================

def load_tickets():

    try:
        with open(
            TICKETS_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except:

        return {}



def save_tickets():

    with open(
        TICKETS_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            tickets,
            f,
            indent=4
        )



tickets = load_tickets()



# =========================
# BOT
# =========================


intents = discord.Intents.default()

intents.members = True
intents.message_content = True
intents.voice_states = True


bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

# =========================
# VIEW CHIUSURA
# =========================

class CloseTicketView(View):

    def __init__(self):
        super().__init__(timeout=None)


    @discord.ui.button(
        label="🔒 Chiudi assistenza",
        style=discord.ButtonStyle.red,
        custom_id="close_ticket"
    )
    async def close_ticket(
        self,
        interaction: discord.Interaction,
        button: Button
    ):

        channel = interaction.guild.get_channel(
            tickets[str(interaction.guild.id)]["channel"]
        )

        await close_ticket(
            interaction,
            channel
        )



# =========================
# VIEW APERTURA
# =========================

class SupportView(View):

    def __init__(self):
        super().__init__(timeout=None)


    @discord.ui.button(
        label="🎧 Richiedi assistenza",
        style=discord.ButtonStyle.green,
        custom_id="open_ticket"
    )
    async def open_ticket(
        self,
        interaction: discord.Interaction,
        button: Button
    ):


        guild = interaction.guild
        user = interaction.user



        # controllo ticket già aperto

        for ticket in tickets.values():

            if ticket.get("user") == user.id:

                await interaction.response.send_message(
                    "❌ Hai già una richiesta di assistenza aperta.",
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



        # crea dati ticket

        tickets[str(voice.id)] = {

            "guild": guild.id,

            "user": user.id,

            "channel": voice.id,

            "claimed": None,

            "staff": [],

            "created": datetime.now().timestamp(),

            "message": None

        }


        save_tickets()



        # messaggio richiesta staff

        request_channel = guild.get_channel(
            REQUEST_CHANNEL_ID
        )


        embed = discord.Embed(

            title="🚨 Nuova richiesta assistenza",

            color=discord.Color.orange(),

            timestamp=datetime.now()

        )


        embed.add_field(

            name="👤 Utente",

            value=user.mention,

            inline=False

        )


        embed.add_field(

            name="🔊 Canale",

            value=voice.mention,

            inline=False

        )


        embed.add_field(

            name="📌 Stato",

            value="⏳ In attesa di uno staff",

            inline=False

        )


        msg = await request_channel.send(

            content=staff_role.mention,

            embed=embed,

            allowed_mentions=discord.AllowedMentions(
                roles=True
            )

        )


        tickets[str(voice.id)]["message"] = msg.id

        save_tickets()



        # risposta privata utente

        private = discord.Embed(

            title="🎧 Assistenza creata",

            description=
            f"Il tuo canale è stato creato:\n\n"
            f"{voice.mention}\n\n"
            "Attendi l'arrivo dello staff.",

            color=discord.Color.blue()

        )


        await interaction.response.send_message(

            embed=private,

            view=CloseTicketView(),

            ephemeral=True

        )



        # sposta utente

        if user.voice:

            await user.move_to(
                voice
            )
            
# =========================
# FUNZIONE CHIUSURA
# =========================

async def close_ticket(interaction, channel):

    if channel is None:
        return


    ticket = tickets.get(
        str(channel.id)
    )


    if ticket is None:
        return



    guild = interaction.guild


    log = guild.get_channel(
        LOG_CHANNEL_ID
    )



    duration = int(
        datetime.now().timestamp()
        -
        ticket["created"]
    )


    minutes = duration // 60



    staff_text = "Nessuno"


    if ticket["staff"]:

        staff_text = " ".join(
            f"<@{x}>"
            for x in ticket["staff"]
        )



    embed = discord.Embed(

        title="🔒 Assistenza terminata",

        color=discord.Color.red(),

        timestamp=datetime.now()

    )


    embed.add_field(

        name="👤 Utente",

        value=f"<@{ticket['user']}>",

        inline=False

    )


    embed.add_field(

        name="🛡️ Staff partecipante",

        value=staff_text,

        inline=False

    )


    embed.add_field(

        name="⏱️ Durata",

        value=f"{minutes} minuti",

        inline=False

    )


    embed.add_field(

        name="📁 Canale",

        value=channel.name,

        inline=False

    )


    if log:

        await log.send(
            embed=embed
        )



    tickets.pop(
        str(channel.id),
        None
    )


    save_tickets()



    await channel.delete()






# =========================
# CLAIM STAFF
# =========================

@bot.event
async def on_voice_state_update(
    member,
    before,
    after
):


    # entrato in vocale

    if after.channel is not None:


        channel = after.channel


        ticket = tickets.get(
            str(channel.id)
        )


        if ticket:


            staff_role = channel.guild.get_role(
                STAFF_ROLE_ID
            )



            if staff_role in member.roles:


                if member.id not in ticket["staff"]:

                    ticket["staff"].append(
                        member.id
                    )



                if ticket["claimed"] is None:


                    ticket["claimed"] = member.id



                    request = channel.guild.get_channel(
                        REQUEST_CHANNEL_ID
                    )


                    if request:


                        try:

                            msg = await request.fetch_message(
                                ticket["message"]
                            )


                            embed = msg.embeds[0]


                            embed.color = discord.Color.green()


                            for field in embed.fields:

                                if field.name == "📌 Stato":

                                    embed.set_field_at(

                                        embed.fields.index(field),

                                        name="📌 Stato",

                                        value=
                                        f"🟢 Claimato da {member.mention}",

                                        inline=False

                                    )


                            await msg.edit(
                                embed=embed
                            )


                        except:

                            pass



                save_tickets()



    # uscita utente

    if before.channel is not None:


        channel = before.channel


        ticket = tickets.get(
            str(channel.id)
        )


        if ticket:


            if member.id == ticket["user"]:


                await asyncio.sleep(5)


                if len(channel.members) == 0:


                    fake_interaction = type(
                        "obj",
                        (),
                        {
                            "guild": channel.guild
                        }
                    )()


                    await close_ticket(
                        fake_interaction,
                        channel
                    )





# =========================
# READY
# =========================


@bot.event
async def on_ready():


    bot.add_view(
        SupportView()
    )


    bot.add_view(
        CloseTicketView()
    )


    print(
        f"{bot.user} online!"
    )





# =========================
# CREAZIONE PANNELLO
# =========================


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

        title="🎧 Centro Assistenza",

        description=
        "Hai bisogno di aiuto?\n\n"
        "Premi il pulsante qui sotto per aprire una chiamata con lo staff.",

        color=discord.Color.blue()

    )


    embed.set_footer(
        text="Sistema assistenza"
    )


    await ctx.send(

        embed=embed,

        view=SupportView()

    )





# =========================
# START
# =========================

bot.run(TOKEN)