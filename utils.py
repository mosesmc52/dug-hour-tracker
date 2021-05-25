
def phone_format(n):
    return format(int(n[:-1]), ",").replace(",", "-") + n[-1]
