d = {"a": "b", "c": "d", "e": "f", "g": "h", "i": "j", "k": "l", "m": "n"}

b = {}

b.update(d)
b.update({v: k for k, v in d.items()})
print(b)


def select_half_pairs_general2(d):
    selected_pairs = {}
    seen = set()

    # 遍历字典
    for key, value in d.items():
        if key not in seen:
            # 添加当前键值对到结果中
            selected_pairs[key] = value
            seen.add(key)
            seen.add(value)

    return selected_pairs


import time

start = time.time()

for _ in range(1000000):
    select_half_pairs_general2(b)

print(time.time() - start)
