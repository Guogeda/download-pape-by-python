##  使用scihub接口批量下载文献

### 工具

* python

### 参考资料

* [scihub2pdf](https://github.com/bibcure/scihub2pdf)
* [scihub](https://github.com/zaytoun/scihub.py)

### 使用方法

* ```python
  pip install -r requirements.txt
  ```

### 使用例子

* ```python
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
  
  ```



### 说明

* 代码是在参考资料的基础上修改的，适用于用title和doi批量下载文献

