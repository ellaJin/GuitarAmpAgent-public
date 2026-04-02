import uvicorn
import sys
import os

# 将 src 目录加入搜索路径
sys.path.append(os.path.join(os.getcwd(), "src"))

if __name__ == "__main__":
    # 注意这里直接写 app.main:app，因为 PYTHONPATH 已经包含了 src
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)