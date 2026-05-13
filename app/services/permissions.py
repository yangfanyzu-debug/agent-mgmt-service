class OwnershipError(Exception):
    pass


def add_can_edit(rows, current_user_id):
    enriched = []
    for row in rows:
        item = dict(row)
        item["can_edit"] = int(item.get("created_by_user_id") or 0) == int(current_user_id)
        enriched.append(item)
    return enriched


def ensure_can_edit(row, current_user_id):
    if int(row.get("created_by_user_id") or 0) != int(current_user_id):
        raise OwnershipError("Only the creator can modify this resource")
    return None
