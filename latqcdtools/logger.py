
log_levels = {
    'ALL': 0,
    'DEBUG': 1,
    'DETAILS': 2,
    'PROGRESS': 3,
    'INFO': 4,
    'WARN': 5,
    'NONE': 6
}

current_level = 4


def isLevel(level):
    return log_levels[level] >= current_level


def set_log_level(level):
    global current_level
    current_level = log_levels[level]


def log(level, *args, **kwargs):
    if log_levels[level] >= current_level:
        print(*args, **kwargs)


def debug(*args, **kwargs):
    if current_level <= 1:
        print(*args, **kwargs)


def details(*args, **kwargs):
    if current_level <= 2:
        print(*args, **kwargs)


def progress(*args, **kwargs):
    if current_level <= 3:
        print(*args, **kwargs)


def info(*args, **kwargs):
    if current_level <= 4:
        print(*args, **kwargs)


def warn(*args, **kwargs):
    if current_level <= 5:
        print(*args, **kwargs)
