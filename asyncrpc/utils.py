def get_lst(item):
    if item is None:
        return item
    return [item] if not isinstance(item, list) else item
