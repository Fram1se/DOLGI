def check_pin(raw):
    try:
        pin = str(raw)
        if len(pin) == 4 and pin.isdigit():
            return "ok"
        return "bad"
    except Exception:
        return "bad"
    finally:
        print("пин проверен")