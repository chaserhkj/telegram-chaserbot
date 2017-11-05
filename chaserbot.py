#!/usr/bin/env python3

config_path = "config.yaml"
config = {}
steam_status_array = ["Offline", "Online", "Busy", "Away", "Snooze", "Looking for trade", "Looking for play"]
import yaml, os
with open(config_path, "r") as f:
    config = yaml.load(f)
tg_key = config["APIKEY"]
steam_key = config["steam"]["APIKEY"]
import dataset
from valve.steam.api.interface import API as steamapi
steam = steamapi(steam_key)

db = dataset.connect("sqlite:///data.db")

def start(bot, update):
    update.message.reply_text("Hi, this is chaserbot, how are you doing today?\n\n"
            "reply /help for a list of commands")

def helpmsg(bot, update):
    update.message.reply_text("List of commands:\n\n"
            "/authsharing : Authorize sharing of your status in this chat\n"
            "/revokesharing : Revoke sharing of your status in this chat\n"
            "/status : Show status of everybody who is sharing\n\n"
            "/registersteam : Register your steamid with this bot\n"
            "/addsteam : Add external steam account to this chat\n"
            "/delsteam : Delete an external steam account")

def registersteam(bot, update, args):
    if len(args) == 0:
        update.message.reply_text("Usage: /registersteam <64-bit steam id>\n\n"
                "Use this tool ( https://steamdb.info/calculator/ ) to find your"
                "64-bit steam id (and Get Disappointed In Your Life(TM)), it should"
                " be the numerical id in the \"steamid\" entry part in the "
                "profile page of your account in the calculator.")
        return
    else:
        steamid = args[0]
        tb = db["ids"]
        userid = update.message.from_user.id
        username = update.message.from_user.first_name + " " + update.message.from_user.last_name
        tb.upsert({"user":userid, "name":username, "steamid":steamid}, ["user"])
        update.message.reply_text("Updated steamid successfully")
        return

def authsharing(bot, update):
    chatid = update.message.chat.id
    userid = update.message.from_user.id
    tb = db["auth_" + str(chatid)]
    if tb.find_one(user = userid):
        update.message.reply_text("You've already authorized sharing in this chat!")
        return
    tb.insert({"user":userid})
    update.message.reply_text("Successfully authorized status sharing in this chat")

def revokesharing(bot, update):
    chatid = update.message.chat.id
    userid = update.message.from_user.id
    tb = db["auth_" + str(chatid)]
    if not tb.find(user = userid):
        update.message.reply_text("You haven't authorized sharing in this chat!")
        return
    tb.delete(user = userid)
    update.message.reply_text("Successfully revoked status sharing in this chat")

def status(bot, update):
    chatid = update.message.chat.id
    authtb = db["auth_" + str(chatid)]
    idtb = db["ids"]
    steamtb = db["steam_" + str(chatid)]
    users = [idtb.find_one(user = i["user"]) for i in authtb.all()]
    steamids = [u["steamid"] for u in users]
    namecache = dict((u["steamid"], u["name"]) for u in users)
    steamstatus = "Steam Accounts Status\n"
    steamplayers = steam["ISteamUser"].GetPlayerSummaries(steamids)["response"]["players"]
    for player in steamplayers:
        steamid = player["steamid"]
        status = player["personastate"]
        name = namecache[steamid]
        steamstatus += name + " is " + steam_status_array[status]
        if "gameextrainfo" in player:
            gamename = player["gameextrainfo"]
            steamstatus += " and playing " + gamename
        steamstatus += "\n"
    steamids = [e["steamid"] for e in steamtb.all()]
    steamplayers = steam["ISteamUser"].GetPlayerSummaries(steamids)["response"]["players"]
    for player in steamplayers:
        steamid = player["steamid"]
        status = player["personastate"]
        name = player["personaname"]
        steamstatus += name + " is " + steam_status_array[status]
        if "gameextrainfo" in player:
            gamename = player["gameextrainfo"]
            steamstatus += " and playing " + gamename
        steamstatus += "\n"
    update.message.reply_text(steamstatus)

def addsteam(bot, update, args):
    if len(args) == 0 :
        update.message.reply_text("Usage: /addsteam <64-bit steam id>")
        return
    chatid = update.message.chat.id
    steamtb = db["steam_" + str(chatid)]
    steamtb.upsert({"steamid": args[0]}, ["steamid"])
    update.message.reply_text("Updated successfully")

def delsteam(bot, update, args):
    if len(args) == 0 :
        update.message.reply_text("Usage: /delsteam <64-bit steam id>")
        return
    chatid = update.message.chat.id
    tb = db["steam_" + str(chatid)]
    if not tb.find(steamid = args[0]):
        update.message.reply_text("Account not found")
        return
    tb.delete(steamid = args[0])
    update.message.reply_text("Successfully deleted this account")

from telegram.ext import Updater, CommandHandler
updater = Updater(tg_key)

updater.dispatcher.add_handler(CommandHandler("start", start))
updater.dispatcher.add_handler(CommandHandler("help", helpmsg))
updater.dispatcher.add_handler(CommandHandler("authsharing", authsharing))
updater.dispatcher.add_handler(CommandHandler("revokesharing", revokesharing))
updater.dispatcher.add_handler(CommandHandler("status", status))
updater.dispatcher.add_handler(CommandHandler("registersteam", registersteam, pass_args=True))
updater.dispatcher.add_handler(CommandHandler("addsteam", addsteam, pass_args=True))
updater.dispatcher.add_handler(CommandHandler("delsteam", delsteam, pass_args=True))

updater.start_polling()
updater.idle()

