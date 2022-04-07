# -*- coding: utf-8 -*-
import telebot
from telebot import *
import mysql.connector
from mysql.connector import errorcode

import json
import os
import hashlib
import random
import re
import logging


# Service
def log_error(f):
    def inner(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(e)
            raise 0
    return inner


class Const:

    # SQL
    SEARCH_TYPE = 'search_type'
    TOKENS_TABLE = 'tokens'

    SUCCESS_EMOJI = '✅'
    ERROR_EMOJI = '❌'
    WARN_EMOJI = '⚠️'
    CRY_EMOJI = '😢'
    UNAMUSED_EMOJI = '😒'

    SUCCESS = f'{SUCCESS_EMOJI} *Успешная обработка!*\n'
    FAIL = f'{ERROR_EMOJI} *Ошибка выполнения!*\n'
    WARN = f'{WARN_EMOJI} *Предупреждение!*\n'

    STICKERS = [

    ]

    DEHASH_CMDS = {
        'dehash': 1,
        'hash': 2,
    }
    DEHASH_HELP = {
        'dehash': '`/dehash <AuthMe/MD5 hash>` – de-hash password',
        'hash': '`/hash <AuthMe/MD5> <password>` – hash password'
    }

    WLIST_CMDS = {
        'wl': 2  # 23 - 2 или 3 аргумента!!
    }
    WLIST_HELP = {
        'wl': '`/wl <check/get/add/rm> [username]` – whitelist'
    }

    OTHER_CMDS = {
        'code': 1,
        'start': 0,
        'help': 0,
        'ping': 0,
    }
    OTHER_HELP = {
        'code': f'`/code <access_token>` – get access using bought token',
        'start': f'`/start` – idk, just _start_ command',
        'help': '`/help` – receive this message',
        'ping': '`/ping` – check if bot is alive'
    }

    ADMIN_CMDS = {
        **WLIST_CMDS,
        'sql': 1,
    }

    ADMIN_HELP = {
        **WLIST_HELP,
        'sql': '`/sql <username>` – check if username exists in leaked databases'
    }

    USER_CMDS = {**DEHASH_CMDS, **OTHER_CMDS}
    USER_HELP = {**DEHASH_HELP, **OTHER_HELP}

    FULL_CMDS = {**ADMIN_CMDS, **USER_CMDS}
    FULL_HELP = {**ADMIN_HELP, **USER_HELP}


class DeHash:
    DICTS_FOLDER = 'Dicts'  # Папка со словарями
    EXTS = ['.txt', '.dic']  # Расширения файлов словарей

    AUTHME_LEN = 86
    SALT_LENGTH = 16

    MD5_LEN = 32

    ALLOWED = True  # Прошел ли хеш проверку
    RESULT = dict()  # Результат

    def __init__(self, hashed: str):
        if not Helper.check_dir(self.DICTS_FOLDER):
            logger.info(f'{self.DICTS_FOLDER} directory not found..')
            logger.info('-  Creating new one')

            os.mkdir(self.DICTS_FOLDER)

            logger.info(' - Done!')

        self.__type = self.check_hash(hashed)
        self.__DICT_LIST = list(filter(
            lambda x: Helper.check_file(x, self.DICTS_FOLDER, self.EXTS),
            os.listdir(self.DICTS_FOLDER))
        )
        if self.__type == 'authme':
            self.__hash = hashed
            self.__salt = hashed.split('$')[2]
        elif self.__type == 'md5':
            self.__hash = hashed
            self.__salt = 'NO NEED'
        else:
            self.ALLOWED = False

    def password(self):
        for dictionary in self.__DICT_LIST:
            dict_file = open(f'{self.DICTS_FOLDER}/{dictionary}', mode='r', encoding='utf-8',  errors='ignore')

            logger.info(dictionary)

            i = 0
            for pwd in dict_file:
                pwd = pwd.rstrip()
                if self.__decrypt(pwd):
                    self.RESULT['type'] = self.__type.upper()
                    self.RESULT['dict'] = dictionary
                    self.RESULT['iter'] = i+1
                    self.RESULT['pwd'] = pwd
                    return True
                i = i + 1
        self.RESULT.clear()
        return False

    @staticmethod
    def encrypt(etype: str, password: str, salt: str):
        if etype == 'authme':
            hashed = hashlib.sha256(hashlib.sha256(password.encode('utf-8')).hexdigest().join(salt).encode('utf-8')).hexdigest()
            out = f'$SHA${salt}${hashed}'
            return out
        elif etype == 'md5':
            return hashlib.md5(password.encode('utf-8')).hexdigest()

    @staticmethod
    def generate_salt():
        salt_len = 16
        chars = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f']
        max_char_index = len(chars)-1
        salt = ''
        for i in range(salt_len):
            e = chars[random.randint(0, max_char_index)]
            salt = '{0}{1}'.format(salt, e)
        return salt

    @staticmethod
    def check_hash(hashed: str):
        if re.search(r'^\$SHA\$[0-9a-f]{16}\$[0-9a-f]{64}$', hashed):
            return 'authme'
        elif re.search(r'^[0-9a-z]{32}$', hashed):
            return 'md5'
        else:
            return 'undefined'

    def __decrypt(self, password: str):
        encrypted = self.encrypt(self.__type, password, self.__salt)
        if self.__hash == encrypted:
            return True
        return False


class Helper:

    # Telegram
    @staticmethod
    def get_args(message: types.Message):
        splitted = Helper.clear(message.text.split(' '))
        splitted.pop(0)
        args = []
        for i in splitted:
            args.append(i)
        return args

    @staticmethod
    def get_cmd(message: types.Message):
        splitted = message.text.split(' ')
        if splitted[0][0] == '/':
            splitted[0] = splitted[0][1:]
        return splitted[0]

    @staticmethod
    def check_args(args: list, size: int):
        if len(args) >= size:
            return True
        return False

    @staticmethod
    def check_full_cmd(command: str, args: list):
        for c in Const.FULL_CMDS:
            if c == command:
                for e in str(Const.FULL_CMDS[c]):
                    if len(args) == int(e):
                        return True
        return False

    @staticmethod
    def edit(message: types.Message, msg: str):
        return bot.edit_message_text(
            text=msg,
            chat_id=message.chat.id,
            message_id=message.message_id,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )

    @staticmethod
    def send(message: types.Message, msg: str):
        return bot.send_message(
            text=msg,
            chat_id=message.chat.id,
            parse_mode="Markdown",
            disable_web_page_preview=False
        )

    @staticmethod
    def error(message: types.Message, msg: str):
        return Helper.send(message, f'{Const.FAIL}Причина: {msg}')

    @staticmethod
    def warn(message: types.Message, msg: str):
        return Helper.send(message, f'{Const.WARN}{msg}')

    @staticmethod
    def success(message: types.Message, msg: str):
        return Helper.send(message, f'{Const.SUCCESS}{msg}')

    @staticmethod
    def reply(message: types.Message, msg: str):
        return bot.reply_to(
            text=msg,
            message=message,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )

    @staticmethod
    def message_debug(message: types.Message):
        print(f'\nCommand: {Helper.get_cmd(message)}')
        print(f'Args: {Helper.get_args(message)}')
        output = f'--------\nNew message!\n Time: {message.date}\n From: {message.from_user.first_name}' \
            f'{message.from_user.last_name} ({message.from_user.username})\n' \
            f' ID: {message.from_user.id}\n Text: {message.text}\n--------'
        logger.info(output)

    # Service
    @staticmethod
    def is_email(e: str):
        return re.search(r'@\w+.\w+$', e)

    @staticmethod
    def clean_at(data: str):
        return data.replace('@', '')

    @staticmethod
    def join(one: str, two: str):
        return '{0}{1}'.format(one, two)

    @staticmethod
    def clear(to_clear: list):
        clean = []
        for val in to_clear:
            if (val is not None) and (not isinstance(val, int)) and (len(val) > 1):
                clean.append(val)
        return clean

    # Files
    @staticmethod
    def check_dir(dirname: str):
        if os.path.isdir(dirname):
            return True
        return False

    @staticmethod
    def check_file(filename: str, directory: str = False, extensions: list = False):
        path = ''
        if directory:
            if extensions:
                for ext in extensions:
                    if filename.endswith(ext):
                        path = f'{directory}/{filename}'
                        pass
            else:
                path = f'{directory}/{filename}'
        else:
            path = filename
        if os.path.exists(path):
            return 1
        return 0

    @staticmethod
    def file_empty(file_path: str):
        if os.stat(file_path).st_size == 0:
            return True
        return False


class WLister:
    WLISTING = True

    __WLIST_FILE = 'wlist.json'
    __WLIST_DIR = 'Assets'
    __PATH = '{0}/{1}'.format(__WLIST_DIR, __WLIST_FILE)

    WLIST = dict()

    __ADMINS = ['igordux']  # Дабудих

    def __init__(self):
        self.WLIST = self.get_file()

    def check(self, username: str):
        if self.WLISTING:
            for i in self.WLIST:
                if self.WLIST[i] == username:
                    return True
            return False
        return True

    def in_admins(self, username: str):
        for i in self.get_admins():
            if i == username:
                return True
        return False

    def get_admins(self):
        return self.__ADMINS

    def add(self, username: str):
        if self.check(username):
            return False
        else:
            self.WLIST[str(len(self.WLIST))] = username
            self.set_file(self.WLIST)
            return True

    def remove(self, username: str):
        if self.check(username):
            for k in self.WLIST:
                if self.WLIST[k] == username:
                    self.WLIST.pop(k)
                    self.set_file(self.WLIST)
                    return True
        else:
            return False

    def get_file(self):
        if not Helper.check_dir(self.__WLIST_DIR):
            logger.info(f'{self.__WLIST_DIR} directory not found..')
            logger.info('-  Creating new one')

            os.mkdir(self.__WLIST_DIR)

            logger.info(' - Done!')

        if Helper.check_file(self.__PATH):
            if Helper.file_empty(self.__PATH):
                self.adm_file()
            with open(self.__PATH, 'r') as file:
                return json.load(file)
        else:
            logger.info(f'{self.__WLIST_FILE} not found..')

            logger.info(' - Creating new one...')
            self.set_file()
            while not Helper.check_file(self.__PATH):
                print('..Still not created')
                time.sleep(1)
            logger.info(' - Done!')

            return self.get_file()

    def set_file(self, data: dict = False):
        if data:
            logger.info(data)
            with open(self.__PATH, 'w') as file:
                return json.dump(data, file)
        else:
            open(self.__PATH, 'w+').close()

    def adm_file(self):
        admins_dict = dict()
        for i in range(0, len(self.__ADMINS)):
            admins_dict[i] = self.__ADMINS[i]

        logger.info('- Filling WList file with Admins..')
        self.set_file(admins_dict)
        logger.info('- Done!')


class SQL:
    tables = list()
    columns = dict()

    def __init__(self, username: str, password: str, db_name: str):
        self.username = username
        self.password = password
        self.db_name = db_name
        try:
            self.cnx = mysql.connector.connect(user=self.username, password=self.password, database=self.db_name)
            self.cursor = self.cnx.cursor()

            self.query("SELECT * FROM INFORMATION_SCHEMA.TABLES", [])
            self.tables = [c[2] for c in self.cursor if c[1] == self.db_name]

            for e in self.tables:
                self.query(f'SHOW COLUMNS FROM {e}', [])
                columns = self.cursor.fetchall()
                i = 0
                self.columns[e] = {}
                for c in columns:
                    self.columns[e].update({i: list(c)[0]})
                    i += 1

        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                logger.error("Database access denied!")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                logger.error("Database does not exist!")
            else:
                logger.error(err)

    def query(self, query: str, args: list):
        return self.cursor.execute(query, tuple(args))

    def get_all(self):
        result = self.cursor.fetchall()
        return list() if not result else list(result)

    def get_first(self):
        result = self.get_all()
        return list() if not result else list(result[0])

    def search(self, type: str, to_check: str):
        callback = {}
        for table in self.columns:
            callback[table] = {}
            try:
                for e in self.columns[table]:
                    row = self.columns[table][e]

                    query = f'SELECT {row} FROM `{table}` WHERE {type} = %s'
                    self.query(query, [to_check])
                    result = self.get_first()

                    cleaned = Helper.clear(result)
                    if cleaned:
                        callback[table][row] = result[0]
                if not callback[table]:
                    callback.pop(table)
            except Exception as e:
                print(f'{table} error: {e}')
                callback.pop(table)
                pass
        return callback

    def check(self, to_check: str):

        type = 'login'
        if Helper.is_email(to_check):
            type = 'email'

        callback = self.search(type, to_check)

        if callback:
            callback.update({Const.SEARCH_TYPE: type})
        return callback

    def __del__(self):
        try:
            self.cursor.close()
            self.cnx.close()
        except Exception as e:
            print(e)


bot = telebot.TeleBot('API TOKEN REMOVED')
wlist = WLister()

logger = telebot.logger
logger.setLevel(logging.INFO)


@bot.message_handler(commands=['help'])
def help(message):
    logger.info(f'{message.from_user.username} issued {message.text}')

    user = message.from_user
    out = '*All of the bot\'s commands*\n`1.` *Main commands:*\n'
    for h in Const.DEHASH_HELP:
        out = Helper.join(out, f'{Const.DEHASH_HELP[h]}\n')

    out = Helper.join(out, '\n`2.` *Other commands:*\n')
    for h in Const.OTHER_HELP:
        out = Helper.join(out, f'{Const.OTHER_HELP[h]}\n')

    if wlist.in_admins(user.username):
        out = Helper.join(out, '\n`3.` *ADMIN commands:*\n')
        for h in Const.ADMIN_HELP:
            out = Helper.join(out, f'{Const.ADMIN_HELP[h]}\n')
        out = Helper.join(out, f'\n`Nah, u\'re Administrator, here is ur `[account](t.me/{user.username})` link`')

    elif wlist.check(user.username):
        out = Helper.join(out, '\n`You CAN use *Main commands* you need to`')

    else:
        out = Helper.join(out, '\n`To use *Main commands* you need to` [purchase](t.me/igordux) `an access!`')
    Helper.send(message, out)


@bot.message_handler(commands=['start'])
def start(message):
    logger.info(f'{message.from_user.username} issued {message.text}')
    Helper.send(message, f'`Привет`, *{message.from_user.first_name} {message.from_user.last_name}*!!!😍😍')


@bot.message_handler(commands=["ping"])
def ping(message):
    logger.info(f'{message.from_user.username} issued {message.text}')
    Helper.send(message, '*S*_t_`i`*l*_l_ `a`_l_`i`*v*_e_`!`')


@bot.message_handler(content_types=['audio'])
def audio(message):

    global temp_audio
    temp_audio = message.audio

    Helper.send(message, 'Any caption?')
    bot.register_next_step_handler(message, audio_2)


def audio_2(message):

    audio = globals()['temp_audio']
    del globals()['temp_audio']

    caption = message.text if message.text.lower() != 'no' else ''
    bot.send_audio(
        chat_id=message.chat.id,
        audio=audio.file_id,
        caption=caption.encode('utf-8'),
        parse_mode='Markdown'
    )
    bot.clear_reply_handlers_by_message_id(message.message_id)


# КОМАНДЫ ХЕШЕРА
@bot.message_handler(commands=Const.DEHASH_CMDS)
def hasher(message):
    logger.info(f'{message.from_user.username} issued {message.text}')
    user = message.from_user

    if wlist.check(user.username) or wlist.in_admins(user.username):
        command = Helper.get_cmd(message)
        args = Helper.get_args(message)

        if not Helper.check_full_cmd(command, args):
            Helper.warn(message, Const.DEHASH_HELP[command])
            return -1

        if command == 'dehash':
            msg_callback = Helper.warn(message, f' Проверка пароля `{args[0]}`...')
            dehash = DeHash(args[0])

            if dehash.ALLOWED:
                res = dehash.password()

                if res:
                    logger.info(f'[{res}] Password: {dehash.RESULT["pwd"]}')
                    out = f'{Const.SUCCESS} Файл: `{dehash.RESULT["dict"]}`\n' \
                        f' Строка: `{dehash.RESULT["iter"]}`\n' \
                        f' Метод: `{dehash.RESULT["type"]}`\n' \
                        f' Пароль: `{dehash.RESULT["pwd"]}`'
                    Helper.edit(msg_callback, out)
                else:
                    logger.info(f'[{res}] Password not found.')
                    Helper.edit(msg_callback, f'{Const.FAIL}Причина: `Увы, расшифровать не получилось!`')
            else:
                Helper.edit(msg_callback, f'{Const.FAIL}Причина: `Некорректный хеш`\nПроверьте введенные данные!')
        elif command == 'hash':
            Helper.success(
                message,
                f'Результат:\n`{DeHash.encrypt(args[0], args[1], DeHash.generate_salt())}`'
            )


@bot.message_handler(commands=["code"])
def code(message):
    logger.info(f'{message.from_user.username} issued {message.text}')

    user = message.from_user

    if wlist.in_admins(user.username):
        command = Helper.get_cmd(message)
        args = Helper.get_args(message)
        if not Helper.check_args(args, 1):
            Helper.warn(message, Const.FULL_HELP[command])
            return -1

        sql = SQL('root', '', 'checker_settings')

        with open('Tokens/7Days.txt', 'r') as file:
            lines = [line.rstrip() for line in file]
            print(lines)
            for line in lines:
                query = f"INSERT INTO `{Const.TOKENS_TABLE}` (`code`) VALUES ('{line.rstrip()}');"
                print(query)


@bot.message_handler(commands=Const.WLIST_CMDS)
def whitelisting(message):
    logger.info(f'{message.from_user.username} issued {message.text}')

    user = message.from_user

    if wlist.in_admins(user.username):
        command = Helper.get_cmd(message)
        args = Helper.get_args(message)
        if not Helper.check_full_cmd(command, args):
            Helper.warn(message, Const.WLIST_HELP[command])
            return -1
        if args[0] == 'check':
            if args[1] == 'me':
                Helper.success(message, str(wlist.check(user.username)))
            else:
                Helper.success(message, str(wlist.check(Helper.clean_at(args[1]))))

        elif args[0] == 'get':
            wl = wlist.WLIST
            out = '---WhiteListed Users---\n'
            for e in wl:
                out = Helper.join(out, f'- {wl[e]}\n')
            Helper.success(message, out)

        elif args[0] == 'adm':
            wl = wlist.get_admins()
            out = '---Admin Users---\n'
            for e in wl:
                out = Helper.join(out, f'- {e}\n')
            Helper.success(message, out)

        elif args[0] == 'add':
            if wlist.add(Helper.clean_at(args[1])):
                Helper.success(message, '')
            else:
                Helper.error(message, f'`Ник уже в вайтлисте!`')

        elif args[0] == 'rm':
            if wlist.remove(Helper.clean_at(args[1])):
                Helper.send(message, Const.SUCCESS)
            else:
                Helper.error(message, f'`Ник не в вайтлисте!`')
        else:
            Helper.warn(message, Const.WLIST_HELP[command])


@bot.message_handler(commands=['sql'])
def sql_check(message):
    logger.info(f'{message.from_user.username} issued {message.text}')

    user = message.from_user

    if wlist.in_admins(user.username):
        command = Helper.get_cmd(message)
        args = Helper.get_args(message)
        if not Helper.check_args(args, 1):
            Helper.warn(message, Const.FULL_HELP[command])
            return -1

        sql = SQL('root', '', 'checker_dicts')
        result = sql.check(args[0])

        if result:
            type = result.pop(Const.SEARCH_TYPE)
            out = f' *Тип поиска*: `{type}`\n'
            for table in result:
                other = {}
                out = Helper.join(out, f'*- - - - - - -*\n *Таблица:* `{table}`\n')
                for k, v in result[table].items():
                    if k == 'login':
                        out = Helper.join(out, f' Логин: `{v}`\n')
                    elif k == 'email':
                        out = Helper.join(out, f' Почта: `{v}`\n')
                    elif k == 'password':
                        out = Helper.join(out, f' Пароль: `{v}`\n')
                    else:
                        other[k] = v
                # Дополнительная информация отключена!
                # if other:
                #     out = Helper.join(out, f'\n *Другая информация*:\n')
                #     for k, v in other.items():
                #         out = Helper.join(out, f' `{k}: {v}`\n')
            logger.info(Helper.join('\n[True]\n', out))
            Helper.success(message, out)
        else:
            Helper.error(message, f'`Не найдено в базах данных!`')


@bot.message_handler(content_types=['text'])
def text(message):
    Helper.send(message, f'Wat do *YOU* want now? {Const.UNAMUSED_EMOJI}\nType */help* for help')


bot.polling()
