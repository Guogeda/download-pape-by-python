from queue import Queue
from concurrent.futures import ThreadPoolExecutor


from scihub import SciHub

    
def get_pdf(title):
    sci = SciHub(title=title)
    sci.search(get_first=True)
    print("{} strart downloading ".format(sci.title))
    sci.download()
    return  sci.flag
     
if __name__ == "__main__":
    
    # 无多线程测试程序，将文章title 放在newtitle.txt 文件中
    titil_queue = Queue(maxsize=1000)
    with open( './newtitle.txt', 'r', encoding='UTF-8' ) as f:
        for title in f.readlines():
            titil_queue.put(title)
    
    # while not titil_queue.empty():
    #     title = titil_queue.get()
    #     demo = get_pdf(title)
    #     if not demo:
    #         titil_queue.put(title)

    # 测试多线程程序 
    # titil_queue = Queue(maxsize=1000)

    # with ThreadPoolExecutor(3) as excuter:
    #     while not titil_queue.empty():
    #         title = titil_queue.get()
    #         task = excuter.submit(get_pdf,(title))
    #         if not task.result():
    #             titil_queue.put(title)
