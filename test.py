import time

# Lấy thời gian hiện tại (giây ở dạng float)
timestamp_seconds = time.time()
print(f"Timestamp (second): {timestamp_seconds}")

# Chuyển đổi sang milliseconds
timestamp_milliseconds = int(timestamp_seconds * 1000)

print(f"Timestamp (milliseconds): {timestamp_milliseconds}")