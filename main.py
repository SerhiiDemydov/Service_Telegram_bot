import time
import logging
import parameters
import telebot
import datetime
import json
import os
from threading import Thread

BOT_TOKEN = parameters.bot_token
bot = telebot.TeleBot(BOT_TOKEN)

logging.basicConfig(level='INFO')
logger = logging.getLogger()

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler = logging.FileHandler('data/logfile.log')
handler.setLevel(level=logging.DEBUG)
handler.setFormatter(formatter)

logger.addHandler(handler)


@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
	bot.reply_to(message,
	             f"Вітаю, {message.from_user.first_name}. Я бот сервісної підтримки Sasha Assaul Design. "
	             f"Опишіть будь ласка ваш запит чи проблему і з вами зв'яжуться наші фахівці.")
	logger.info('Send hello message')

@bot.message_handler(
	content_types=["text", "audio", "document", "photo", "sticker", "video", "video_note", "voice", "location",
	               "contact", "new_chat_members", "left_chat_member", "new_chat_title", "new_chat_photo",
	               "delete_chat_photo", "group_chat_created", "supergroup_chat_created", "channel_chat_created",
	               "migrate_to_chat_id", "migrate_from_chat_id", "pinned_message", "web_app_data"])
def forward_message(message):
	# Надсилання повідомлення клієнту
	if message.chat.id == parameters.group_id_main:
		# try:
			if message.reply_to_message.forward_sender_name:
				name = message.reply_to_message.forward_sender_name
				bot.send_message(users[name.split(" ")[0]]["chat_id"], message.text)
				users[name.split(" ")[0]].update({"send_answer": True})
				bot.reply_to(message,
				             f"Повідомлення надіслано користувачу {name.split(' ')[0]} (@{users[name.split(' ')[0]]['username']})")
				logger.info(f"Send answer to {name.split(' ')[0]} (@{users[name.split(' ')[0]]['username']})")
			else:
				print(f'Send to {message.reply_to_message.forward_from.first_name}')
				bot.send_message(message.reply_to_message.forward_from.id, message.text)
				users[message.reply_to_message.forward_from.first_name].update({"send_answer": True})
				bot.reply_to(message,
				             f"Повідомлення надіслано користувачу {message.reply_to_message.forward_from.first_name} "
				             f"(@{users[message.reply_to_message.forward_from.first_name]['username']})")
				logger.info(f"Send answer to {message.reply_to_message.forward_from.first_name} "
				             f"(@{users[message.reply_to_message.forward_from.first_name]['username']})")
		# except AttributeError:
		# 	bot.reply_to(message,
		# 	             f"Повідомлення не відправлене")
		# 	logger.info(f"Don't sent answer")
		# raise AttributeError
	# Перенаправлення повідомлення до групи підтримки
	else:
		bot.forward_message(parameters.group_id_main, message.chat.id, message.message_id)
		print(f"From {message.from_user.first_name} - {message.chat.id}")
		logger.info(f"Received message from {message.from_user.first_name} - {message.chat.id}")
		users.update(
			{
				f"{message.from_user.first_name}":
					{
						"chat_id": message.chat.id,
						"username": message.from_user.username,
						"time_last_message": str(datetime.datetime.fromtimestamp(message.date)),
						"time_answer_message": str(
							datetime.datetime.fromtimestamp(message.date) + datetime.timedelta(minutes=2)),
						"send_answer": False
					}
			}
		)
		logger.info(f"Create dict in json about user {message.from_user.first_name}")
	with open('data/users.json', "w") as file:
		json.dump(users, file)
		logger.info("Updated json file")


def send_answer_to_user():
	while True:
		for user in users:
			if datetime.datetime.now() > datetime.datetime.strptime(users[user]["time_answer_message"],
			                                                        "%Y-%m-%d %H:%M:%S") \
					and users[user]['send_answer'] is False:
				# Фіксація вихідних
				if datetime.datetime.weekday(
						datetime.datetime.strptime(users[user]["time_last_message"],
						                           "%Y-%m-%d %H:%M:%S")) > 4:
					bot.send_message(users[user]["chat_id"],
					                 f"Дякуємо, {user}. "
					                 f"Запит прийнято, але сьогодні у нас вихідний. "
					                 f"У понеділок наші фахівці займуться вашим питанням.")
				# П'ятниця, вечір
				elif datetime.datetime.weekday(
						datetime.datetime.strptime(users[user]["time_last_message"], "%Y-%m-%d %H:%M:%S")) == 4 and \
						int(str(datetime.datetime.strptime(users[user]["time_last_message"], "%Y-%m-%d %H:%M:%S").
								strftime("%H"))) >= 16:
					bot.send_message(users[user]["chat_id"],
					                 f"Дякуємо, {user}. "
					                 f"Запит прийнято, але ми вже не працюємо. "
					                 f"У понеділок наші фахівці займуться вашим питанням.")
				# Фіксація неробочого часу
				elif 7 < int(str(datetime.datetime.strptime(users[user]["time_last_message"],
				                                            "%Y-%m-%d %H:%M:%S").strftime("%H"))) >= 16:
					bot.send_message(users[user]["chat_id"],
					                 f"Дякуємо, {user}. "
					                 f"Запит прийнято, але ми вже не працюємо. Завтра наші фахівці займуться вашим питанням.")
				# Робочий час
				else:
					bot.send_message(users[user]["chat_id"],
					                 f"Дякуємо, {user}. Запит прийнято. Вже поспішаємо щоб його вирішити.")
				users[user].update({"send_answer": True})
				logger.info(f"Send automatic answer to user {user} (@{users[user]['username']})")
				with open('data/users.json', "w") as file:
					json.dump(users, file)
					logger.info("Update json file")
		time.sleep(5)


if __name__ == '__main__':
	
	if os.path.exists('data/users.json'):
		with open('data/users.json', 'r') as file:
			users = json.load(file)
			logger.info("Open json file")
	else:
		users = {}
	
	t1 = Thread(target=send_answer_to_user)
	t2 = Thread(target=bot.infinity_polling)
	
	# start the threads
	t2.start()
	t1.start()
	
	# wait for the threads to complete
	t2.join()
	t2.join()
