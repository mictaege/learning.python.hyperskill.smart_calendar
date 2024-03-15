from datetime import date
from datetime import datetime
from datetime import timedelta
from enum import Enum
import re
import sys
import json
import os

sys.setrecursionlimit(2000)

cmd_add = "add"
cmd_view = "view"
cmd_delete = "delete"
cmd_exit = "exit"

type_note = "note"
type_birthday = "birthday"


class Filter(Enum):
    ALL = "all"
    DATE = "date"
    TEXT = "text"
    BIRTHDAYS = "birthdays"
    NOTES = "notes"
    SORTED = "sorted"


def parse_date_time(datetime_str):
    return datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")


def format_date_time(date_obj):
    return date_obj.strftime("%Y-%m-%d %H:%M")


def parse_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def format_date(date_obj):
    return date_obj.strftime("%Y-%m-%d")


print("Current date and time:")
print(datetime.now().strftime("%Y-%m-%d %H:%M"))


class Note:

    @staticmethod
    def enter_note(idx):
        entered_datetime = enter_datetime(f'{idx}. Enter datetime in "YYYY-MM-DD HH:MM" format:')
        entered_text = input("Enter text")
        return Note(entered_datetime, entered_text)

    @staticmethod
    def to_json(note):
        return {
            "type": type_note,
            "date_time": format_date_time(note.date_time),
            "text": note.text,
        }

    @staticmethod
    def from_json(data):
        return Note(parse_date_time(data["date_time"]), data["text"])

    def __init__(self, date_time, text):
        self.date_time = date_time
        self.date = date_time.date()
        self.text = text

    def __repr__(self):
        left = self.time_left(datetime.now())

        days = left.days
        hours, remainder = divmod(left.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if seconds > 0:
            minutes += 1
        if minutes == 60:
            hours += 1
            minutes = 0
        return f'Note: "{self.text}". Remains: {days} day(s), {hours} hour(s), {minutes} minute(s)'

    def time_left(self, now) -> timedelta:
        return self.date_time - now

    def next_schedule(self):
        return self.date_time

    def is_scheduled(self, schedule_date):
        return (schedule_date.year == self.date.year and schedule_date.month == self.date.month
                and schedule_date.day == self.date.day)


class Birthday:

    @staticmethod
    def enter_birthday(idx):
        entered_date = enter_date(f'{idx}. Enter date of birth in "YYYY-MM-DD" format')
        entered_text = input("Enter name")
        return Birthday(entered_date, entered_text)

    @staticmethod
    def to_json(note):
        return {
            "type": type_birthday,
            "date": format_date(note.date),
            "text": note.text,
        }

    @staticmethod
    def from_json(data):
        return Birthday(parse_date(data["date"]), data["text"])

    def __init__(self, birthday, text):
        self.date = birthday
        self.text = text

    def __repr__(self):
        now = datetime.now()
        left = self.time_left(now)
        days = left.days

        return f'Birthday: "{self.text} (turns {self.age(now)})" Remains: {days} day(s)'

    def next_birthday(self, now):
        today = now.date()
        if (self.date.month, self.date.day) <= (today.month, today.day):
            return date(today.year + 1, self.date.month, self.date.day)
        else:
            return date(today.year, self.date.month, self.date.day)

    def next_schedule(self, now):
        today = now.date()
        birthday = self.next_birthday(today)
        return datetime(birthday.year, birthday.month, birthday.day)

    def time_left(self, now) -> timedelta:
        today = now.date()
        return self.next_birthday(now) - today

    def is_scheduled(self, schedule_date):
        return schedule_date.month == self.date.month and schedule_date.day == self.date.day

    def age(self, now):
        today = now.date()
        age = today.year - self.date.year
        if (today.month, today.day) < (self.date.month, self.date.day):
            age -= 1
        return age + 1


notes = []


def add():
    new_notes = []
    node_type = enter_type("Specify type (note, birthday):")
    if node_type == type_note:
        number = enter_number("How many notes would you like to add:")
        for i in range(number):
            new_notes.append(Note.enter_note(i + 1))
    elif node_type == type_birthday:
        number = enter_number("How many dates of birth would you like to add:")
        for i in range(number):
            new_notes.append(Birthday.enter_birthday(i + 1))
    for note in new_notes:
        print(note)
    notes.extend(new_notes)
    save_notes()
    print()
    execute(True)


def view():
    filter_cmd = enter_filter("Specify filter (all, date, text, birthdays, notes, sorted):")
    match filter_cmd:
        case Filter.ALL:
            filter_all()
        case Filter.DATE:
            filter_date()
        case Filter.TEXT:
            filter_text()
        case Filter.BIRTHDAYS:
            filter_birthdays()
        case Filter.NOTES:
            filter_notes()
        case Filter.SORTED:
            sorted_notes()
    print()
    execute(True)


def filter_all():
    for note in notes:
        print(note)


def filter_date():
    date_input = enter_date('Enter date in "YYYY-MM-DD" format:')
    for note in notes:
        if note.is_scheduled(date_input):
            print(note)


def filter_text():
    text_input = input("Enter text:")
    for note in notes:
        if text_input.lower() in note.text.lower():
            print(note)


def filter_birthdays():
    for note in notes:
        if isinstance(note, Birthday):
            print(note)


def filter_notes():
    for note in notes:
        if isinstance(note, Note):
            print(note)


def sorted_notes():
    now = datetime.now()
    reverse = enter_sorting("Specify way (ascending, descending):") == "descending"
    notes_sorted = sorted(notes, key=lambda n: n.text, reverse=reverse)
    notes_sorted = sorted(notes_sorted, key=lambda n: n.time_left(now), reverse=reverse)
    for note in notes_sorted:
        print(note)


def delete():
    idx = 1
    for note in notes:
        print(f"{idx}. {note}")
        idx += 1
    ids_str = input("Enter ids:")
    ids = map(lambda index: int(index), filter(lambda s: s.isdigit(), ids_str.split(",")))
    for i in sorted(ids, reverse=True):
        del notes[i - 1]
    save_notes()
    print()
    execute(True)


def enter_type(msg):
    node_type = input(msg)
    if node_type == type_note or node_type == type_birthday:
        return node_type
    else:
        print("Incorrect type")
        return enter_type("")


def enter_number(msg):
    num_str = input(msg)
    num = 0
    try:
        num = int(num_str)
    except ValueError:
        pass
    if num <= 0:
        print("Incorrect number")
        return enter_number("")
    return num


def enter_datetime(msg):
    datetime_input = input(msg)
    match = re.fullmatch(r"^\d{2,4}-\d{1,2}-\d{1,2} \d{1,2}:\d{1,2}$", datetime_input)
    if match is None:
        print("Incorrect format")
        return enter_datetime("")
    else:
        try:
            entered_datetime = parse_date_time(datetime_input)
            return entered_datetime
        except ValueError:
            print("Incorrect date or time values")
            return enter_datetime("")


def enter_date(msg):
    date_input = input(msg)
    match = re.fullmatch(r"^\d{2,4}-\d{1,2}-\d{1,2}$", date_input)
    if match is None:
        print("Incorrect format")
        return enter_date("")
    else:
        try:
            entered_date = parse_date(date_input)
            return entered_date
        except ValueError:
            print("Incorrect date or time values")
            return enter_date("")


def enter_filter(msg):
    filter_input = input(msg)
    try:
        return Filter(filter_input)
    except ValueError:
        print("Incorrect filter")
        return enter_filter("")


def enter_sorting(msg):
    sort_input = input(msg)
    if sort_input in ("ascending", "descending"):
        return sort_input
    else:
        print("Incorrect way")
        return enter_sorting("")


def execute(prt_msg):
    if prt_msg:
        print('Enter the command (add, view, delete, exit):')
    cmd = input()
    if cmd == cmd_exit:
        print("Goodbye")
    elif cmd == cmd_add:
        add()
    elif cmd == cmd_view:
        view()
    elif cmd == cmd_delete:
        delete()
    else:
        print("Incorrect command")
        execute(False)


def save_notes():
    data = []
    for note in notes:
        if isinstance(note, Note):
            data.append(Note.to_json(note))
        elif isinstance(note, Birthday):
            data.append(Birthday.to_json(note))
    with open('data.txt', 'w') as f:
        json.dump(data, f)


def load_notes():
    notes.clear()
    if os.path.isfile("data.txt"):
        with open('data.txt', 'r') as f:
            data = json.load(f)
            for item in data:
                if item["type"] == type_note:
                    notes.append(Note.from_json(item))
                elif item["type"] == type_birthday:
                    notes.append(Birthday.from_json(item))


load_notes()
execute(True)
