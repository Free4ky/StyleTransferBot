import telebot
import os
from model import *

isRunning = False

TOKEN = ...
bot = telebot.TeleBot(TOKEN)

queue = {}
img_counter = {}


@bot.message_handler(commands=['start', 'go'])
def start_handler(message):
    global isRunning
    if not isRunning:
        bot.send_message(message.chat.id, 'Hello! Send style and content photos!')
        isRunning = True

    img_counter[message.chat.id] = 0


@bot.message_handler(content_types=['photo'])
def handle_docs_photo(message):
    global queue, img_counter
    if isRunning:
        file_info = bot.get_file(message.photo[len(message.photo) - 1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        file_name = file_info.file_path[file_info.file_path.find('/') + 1:]
        if img_counter[message.chat.id] % 2 == 0:
            src = os.path.join('..', 'data', 'style', file_name)
            queue[message.chat.id] = {'style': [src], 'content': []}
        else:
            src = os.path.join('..', 'data', 'content', file_name)
            queue[message.chat.id]['content'].append(src)
        with open(src, 'wb') as new_file:
            new_file.write(downloaded_file)

        img_counter[message.chat.id] += 1

        if img_counter[message.chat.id] % 2 == 0 and img_counter[message.chat.id] > 0:
            style_src, content_src = queue[message.chat.id]['style'].pop(0), queue[message.chat.id]['content'].pop(0)
            style_img, _ = image_loader(style_src)
            content_img, content_size = image_loader(content_src)
            input_img = content_img.clone()
            bot.send_message(message.chat.id, 'Starting style transfer...')
            output = run_style_transfer(
                cnn,
                content_img,
                style_img,
                input_img
            ).detach().cpu().squeeze(0)
            final_transforms = transforms.Compose([
                transforms.Resize(content_size[::-1]),
                transforms.ToPILImage()
            ])
            img = final_transforms(output)
            out_src = os.path.join('..', 'data', 'output', f'{img_counter[message.chat.id]}.png')
            img.save(out_src)
            try:
                bot.send_photo(message.chat.id, photo=open(out_src, 'rb'))
            except Exception as e:
                bot.reply_to(message, f'{e}')


bot.polling(none_stop=True)
