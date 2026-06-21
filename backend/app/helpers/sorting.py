def merge_sort(records:list,key:str,reverse:bool=False) -> list:
    if len(records) <=1:
        return list(records)
    mid = len(records) // 2
    left = merge_sort(records[:mid],key,reverse)
    right = merge_sort(records[mid:],key,reverse)
    return _merge(left,right,key,reverse)

def _merge(left, right, key, reverse):
    result, i, j = [], 0, 0
    while i < len(left) and j < len(right):
        lv = left[i].get(key)  if left[i].get(key) is not None else ""
        rv = right[j].get(key) if right[i].get(key) is not None else ""
        # (lv <= rv) != reverse  ->  ascending when reverse=False, descending when True
        if (lv <= rv) != reverse:
            result.append(left[i]);  i += 1
        else:
            result.append(right[j]); j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result
        