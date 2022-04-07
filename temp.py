



CALLBACK_BUTTON_LEFT = 'btn_left'
CALLBACK_BUTTON_RIGHT = 'btn_right'


def generate_keyboard(text_1, text_2):
    keyboard = types.InlineKeyboardMarkup()

    keyboard.row(
        types.InlineKeyboardButton(text_1, callback_data=CALLBACK_BUTTON_LEFT),
        types.InlineKeyboardButton(text_2, callback_data=CALLBACK_BUTTON_RIGHT)
    )
    return keyboard


@bot.message_handler(commands=['switch'])
def switch(message):
    chat_id = message.chat.id
    msg = 'Ваш ID = {}\n\n{}'.format(chat_id, message.text)
    markup = generate_keyboard('❤️ 0', '😡 0')
    bot.send_message(
        chat_id,
        msg,
        reply_markup=markup
    )


def check_ext(file_name):
    exts = ['.txt', '.dic']
    for ext in exts:
        if file_name.endswith(ext):
            return True
        else:
            return False
    return 0


@bot.callback_query_handler(func=lambda call: True)
def foo(call):
    msg = call.message
    data = call.data

    chat_id = msg.chat.id
    msg_id = msg.message_id
    print(f'CallBack Received (Chat: {chat_id}| Msg: {msg_id}): CallBackID: {data}')

    button_rows = msg.json['reply_markup']['inline_keyboard']

    butns = []

    for row in button_rows:
        for e in row:
            if e['callback_data'] == data:
                temp = e['text'].split(' ')
                temp[len(temp)-1] = str(int(temp[len(temp)-1])+1)
                new_txt = ''
                for e in temp:
                    new_txt = '{0}{1}'.format(new_txt, f' {e}')
                butns.append({
                    'text': new_txt,
                    'callback_data': data
                })
            else:
                butns.append(e)
    new_markup = generate_keyboard(butns[0]['text'], butns[1]['text'])
    try:
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=msg_id,
            text=msg.text,
            reply_markup=new_markup
        )
    except Exception as e:
        bot.answer_callback_query(call.id, text=f"Не спамь!!")
        logger.info(f'CallBack Error: Spam')