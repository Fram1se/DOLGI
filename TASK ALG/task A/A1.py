def make_phone(raw):
    try:
        text = str(raw)
        if not text.isdigit():
            return None
        
        if len(text) > 11:
            return None
            
        number = "+" + text
        return number
        
    except Exception:
        return None
    finally:
        print("проверка номера завершена")