import time

import parameters
import telebot
import datetime
import json
import os
from threading import Thread

# generate_service = {}
BOT_TOKEN = parameters.bot_token
bot = telebot.TeleBot(BOT_TOKEN)


# keyboard_phone = telebot.types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
# button_phone = telebot.types.KeyboardButton(text="Send phone", request_contact=True)
# keyboard_phone.add(button_phone)  # Add this button
#
# keyboard_finish = telebot.types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
# button_finish = telebot.types.KeyboardButton(text="Finish")
# keyboard_finish.add(button_finish)
#
# keyboard_service = telebot.types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
# button_service = telebot.types.InlineKeyboardButton(text="Create service request")
# keyboard_service.add(button_service)


@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
	bot.reply_to(message,
	             f"Вітаю, {message.from_user.first_name}. Я бот сервісної підтримки Sasha Assaul Design. "
	             f"Опишіть будь ласка ваш запит чи проблему і з вами зв'яжуться наші фахівці.")
	work_time = True


#
# @bot.message_handler(content_types=['contact'])
# def contact(message):
# 	if message.contact is not None:
# 		print(message.contact)
# 		with open(f"{message.from_user.username}_{datetime.datetime.fromtimestamp(message.date).date()}.txt", "w+") as file:
# 			file.write(f'Request from {message.from_user.first_name} {message.from_user.last_name} - Phone {message.contact.phone_number}\n')
# 		bot.reply_to(message, f"{message.from_user.first_name}, please descript your problem", reply_markup=keyboard_finish)
# 		generate_service.update({message.from_user.username: True})
# 	print(generate_service)


# @bot.message_handler(func=lambda message: message.text == "Create service request")
# def activate_service_request(message):
# 	bot.send_message(message.chat.id, f"{message.from_user.first_name}, please give your number", reply_markup=keyboard_phone)


# @bot.message_handler(content_types=["text"])
# def save_message(message):
# 	try:
# 		if generate_service[message.from_user.username]:
# 			if message.text == "Finish":
# 				generate_service.pop(message.from_user.username)
# 				bot.reply_to(message, f"Thank you, {message.from_user.first_name}")
# 			else:
# 				with open(f"{message.from_user.username}_{datetime.datetime.fromtimestamp(message.date).date()}.txt", "a+") as file:
# 					file.write(f'{datetime.datetime.fromtimestamp(message.date)} - {message.text}\n')
# 		print(generate_service)
# 	except KeyError:
# 		bot.reply_to(message, f"{message.from_user.first_name}, if you have some problem. Please, click on 'Create service request'", reply_markup=keyboard_service)
#

@bot.message_handler(
	content_types=["text", "audio", "document", "photo", "sticker", "video", "video_note", "voice", "location",
	               "contact", "new_chat_members", "left_chat_member", "new_chat_title", "new_chat_photo",
	               "delete_chat_photo", "group_chat_created", "supergroup_chat_created", "channel_chat_created",
	               "migrate_to_chat_id", "migrate_from_chat_id", "pinned_message", "web_app_data"])
def forward_message(message):
	# Надсилання повідомлення клієнту
	if message.chat.id == parameters.group_id_main:
		# print(message.reply_to_message)
		if message.reply_to_message.forward_sender_name:
			print(f'Send to {message.reply_to_message.forward_sender_name}')
			bot.send_message(users[message.reply_to_message.forward_sender_name]["chat_id"], message.text)
		else:
			print(f'Send to {message.reply_to_message.forward_from.first_name}')
			bot.send_message(message.reply_to_message.forward_from.id, message.text)
	# Перенаправлення повідомлення до групи підтримки
	else:
		bot.forward_message(parameters.group_id_main, message.chat.id, message.message_id)
		print(f"From {message.chat.id}")
		# print(message)
		users.update(
			{
				f"{message.from_user.first_name}":
					{
						"chat_id": message.chat.id,
						"time_last_message": str(datetime.datetime.fromtimestamp(message.date)),
						"time_answer_message": str(
							datetime.datetime.fromtimestamp(message.date) + datetime.timedelta(minutes=2)),
						"send_answer": False
					}
			}
		)
		with open('data/users.json', "w") as file:
			json.dump(users, file)


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
					                 f"Дякуємо, {user}."
					                 f"Запит прийнято, але ми вже не працюємо. Завтра наші фахівці займуться вашим питанням.")
				# Робочий час
				else:
					bot.send_message(users[user]["chat_id"],
					                 f"Дякуємо, {user}. Запит прийнято. Вже поспішаємо щоб його вирішити.")
				users[user].update({"send_answer": True})
				with open('data/users.json', "w") as file:
					json.dump(users, file)
		time.sleep(5)


if __name__ == '__main__':
	
	if os.path.exists('data/users.json'):
		with open('data/users.json', 'r') as file:
			users = json.load(file)
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
