import requests
import telegram
from settings import bearer, JTOBot_token
from telegram.ext import Updater, CommandHandler, InlineQueryHandler, MessageHandler, Filters
from telegram import InlineQueryResultArticle, InputTextMessageContent
import logging
import json
from operator import itemgetter
##yelp requests
s = requests.Session()
headers = {
    "Authorization": bearer
}


#Bot code

bot = telegram.Bot(token=JTOBot_token)
updater = Updater(token=JTOBot_token)
dispatcher = updater.dispatcher


# logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#                      level=logging.DEBUG)



def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Hi! I'm JTObot, are you up for a pint?")


start_handler = CommandHandler('start', start)
updater.start_polling()


def hello(bot, update):
    update.message.reply_text(
        'Hello {}, are you up for a pint?'.format(update.message.from_user.first_name))

updater.dispatcher.add_handler(CommandHandler('hello', hello))


location = "Dublin"
payload = {'location': location, 'term': 'pub', 'sort_by': 'rating', 'limit':20}
r = s.get('https://api.yelp.com/v3/businesses/search', headers=headers, params=payload)
json_data = json.loads(r.text)
pubs = json_data["businesses"]
blacklist = []



def setstreet(bot, update, args):
    global location, payload, r, json_data, pubs, pub_index
    pub_index = 0
    location = ' '.join(args)+" Dublin"
    payload = {'location': location, 'term': 'pub', 'radius': 1000, 'sort_by': 'rating', 'limit':20}
    r = s.get('https://api.yelp.com/v3/businesses/search', headers=headers, params=payload)
    json_data = json.loads(r.text)
    pubs = json_data["businesses"]
    bot.send_message(chat_id=update.message.chat_id, text="Ok I've updated your location to "+location)

updater.dispatcher.add_handler(CommandHandler('setstreet', setstreet, pass_args=True))


def pubsplease(bot, update):
    for pub in pubs:
        if pub["name"] not in blacklist:
            update.message.reply_text(pub["name"])

updater.dispatcher.add_handler(CommandHandler('pubsplease', pubsplease))


pub_index = 0
def gimmeapub(bot, update):
    global pub_index
    if pubs[pub_index]["name"] in blacklist:
        pub_index += 1
        gimmeapub(bot, update)
    else:
        update.message.reply_text("How about "+pubs[pub_index]["name"]+"?")
    pub_index += 1

updater.dispatcher.add_handler(CommandHandler('gimmeapub', gimmeapub))


def startover(bot, update):
    global pub_index
    pub_index = 0
    update.message.reply_text("Ok, I'll start again. Ask me for a pub")

updater.dispatcher.add_handler(CommandHandler('startover', startover))


def exclude(bot, update, args):
    blacklisted_pub = ' '.join(args)
    blacklist.append(blacklisted_pub)
    bot.send_message(chat_id=update.message.chat_id, text="Ok I won't suggest " +blacklisted_pub+" to you again.")

updater.dispatcher.add_handler(CommandHandler('exclude', exclude, pass_args=True))


def emptyblacklist(bot, update):
    global blacklist
    blacklist = []
    update.message.reply_text("Ok, all pubs are included again. Ask me for a pub")

updater.dispatcher.add_handler(CommandHandler('emptyblacklist', emptyblacklist))


def location(bot, update):
    global payload, r, json_data, pubs, pub_index, meet_in_the_middle, first_pinter, second_pinter
    pub_index = 0
    user_location = update.message.location
    latitude = user_location.latitude
    longitude = user_location.longitude
    if meet_in_the_middle == False:
        payload = {'latitude': latitude, 'longitude': longitude, 'term': 'pub', 'radius': 1000, 'sort_by': 'rating', 'limit': 20}
        r = s.get('https://api.yelp.com/v3/businesses/search', headers=headers, params=payload)
        json_data = json.loads(r.text)
        pubs = json_data["businesses"]
        bot.send_message(chat_id=update.message.chat_id, text="Thanks! I'll update your location now so.")
    else:
        user = update.message.from_user
        if len(first_pinter) == 0:
            first_pinter.append((latitude, longitude))
            bot.send_message(chat_id=update.message.chat_id, text="Cool, and where's pinter number 2? Send me your pin now please!")
        else:
            second_pinter.append((latitude,longitude))
            meet_in_the_middle = False
            mid_lat = (float(first_pinter[0][0]) + float(second_pinter[0][0]))/2
            mid_long = (float(first_pinter[0][1]) + float(second_pinter[0][1]))/2
            payload = {'latitude': mid_lat, 'longitude': mid_long, 'term': 'pub', 'radius': 1000, 'sort_by': 'rating',
                       'limit': 20}
            r = s.get('https://api.yelp.com/v3/businesses/search', headers=headers, params=payload)
            json_data = json.loads(r.text)
            pubs = json_data["businesses"]
            bot.send_message(chat_id=update.message.chat_id,
                             text="Grand, I have two pinters. Ask me for a pub, and I'll give you one in the middle.")

updater.dispatcher.add_handler(MessageHandler(Filters.location, location))

first_pinter = []
second_pinter = []
meet_in_the_middle = False
def meetmeinthemiddle(bot, update):
    global meet_in_the_middle, first_pinter, second_pinter
    meet_in_the_middle = True
    first_pinter = []
    second_pinter = []
    bot.send_message(chat_id=update.message.chat_id, text="Ok where is pinter number 1? Send me your pin now!")

updater.dispatcher.add_handler(CommandHandler('meetmeinthemiddle', meetmeinthemiddle))



def help(bot, update):
    update.message.reply_text("Please see below for all the things you can ask me:\n"+
                            "/hello - ...fairly self explanatory, wouldn't you think?\n"+
                              "/setlocation - let me tell you where I am (street names are good) defaults to Dublin\n"+
                              "/pubsplease - list the top 20 pubs for my location\n"+
                              "/gimmeapub - suggest me the (next) highest rated pub in the list\n"+
                              "/startover - go back to the start of the list again\n"+
                              "/exclude - I hate this pub, don't show it to me anymore! (Type the name exactly as I do, or I won't remember)\n"+
                              "/emptyblacklist - I changed my mind, include all those pubs I vetoed before")

updater.dispatcher.add_handler(CommandHandler('help', help))


def unknown(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Sorry, I didn't understand that command. If you need help, send me '/help'.")

unknown_handler = MessageHandler(Filters.command, unknown)
updater.dispatcher.add_handler(unknown_handler)

updater.idle()