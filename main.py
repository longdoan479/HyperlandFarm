import asyncio
import random


from Include.FileProcessing import FileProcessing
import CONSTANT as Cons
from IncludeAsync.AsyncTaskQueue import AsyncTaskQueue
from IncludeAsync.Database.AsyncPostgresClient import AsyncPostgresClient
from ThreadTask.AsyncDoTask import AsyncDoTask



# Hàm khởi chạy tất cả các tác vụ không đồng bộ
async def main():
    DB_URL = "postgresql+asyncpg://postgres:long123@localhost/HyperlandFarm"
    l_db = AsyncPostgresClient(DB_URL)

    l_FileKey = FileProcessing("key/key.xlsx")
    # l_FileKey2 = FileProcessing("key/2.xlsx")


    l_lstAccount = []
    l_lstAccount.extend(l_FileKey.ReadData())
    # l_lstAccount.extend(l_FileKey2.ReadData())


    l_MaxGroup = max(l_lstAccount, key=lambda obj: obj.mGroup).mGroup

    l_lstAccountRandom = []
    groups_Account = {}

    for i in range(1, l_MaxGroup + 1):
        group = i

        l_lstAccountFilter = list(filter(lambda acc: acc.mGroup == group, l_lstAccount))

        # Nhóm dữ liệu theo giá trị group
        if group not in groups_Account:
            groups_Account[group] = []

        random.shuffle(l_lstAccountFilter)
        groups_Account[group].extend(l_lstAccountFilter)

    l_randomThreadNumber = random.randint(3, 4)

    # Chia các nhóm thành 5 mảng
    l_Results = [[] for _ in range(l_randomThreadNumber)]
    group_list = list(groups_Account.values())

    for i, group in enumerate(group_list):
        l_Results[i % l_randomThreadNumber].extend(group)

    tasks = []

    # Tạo một hàng đợi xử lý với giới hạn tối đa 5 tác vụ đồng thời
    task_queue = AsyncTaskQueue(max_concurrent_tasks=l_randomThreadNumber)

    # Thêm 20 tác vụ vào hàng đợi
    for i in range(0, l_randomThreadNumber):
        task_obj = AsyncDoTask(f"Task {i}", l_Results[i], l_db)  # Khởi tạo đối tượng AsyncDoTask
        task_queue.add_task(task_obj)  # Thêm tác vụ vào hàng đợi
        await asyncio.sleep(0.1)  # Giả lập việc thêm tác vụ theo thời gian thực

    # Chờ cho đến khi tất cả các tác vụ hoàn thành
    await task_queue.run()


# Chạy chương trình asyncio
asyncio.run(main())
