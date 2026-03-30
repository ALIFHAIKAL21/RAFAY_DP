from db.persistence import load_all_order_rows, prepare_chat_for_parsing, reset_all_data, save_parsed_rows


def save_raw_chat_if_new(chat_text: str):
    should_parse, raw_chat_id = prepare_chat_for_parsing(chat_text)
    return raw_chat_id if should_parse else None


def save_orders_from_rows(raw_chat_id, rows):
    return save_parsed_rows(raw_chat_id=raw_chat_id, parsed_rows=rows)


def get_all_saved_orders():
    return load_all_order_rows()


def reset_saved_data():
    return reset_all_data()
