import psycopg2



DATABASE_URL = "postgresql://postgres:mSMZUURhfEPYoDGfpPaMybXcrcJysmOq@tramway.proxy.rlwy.net:41466/railway"

print("正在连接 Railway 数据库...")
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

print("正在读取并过滤 agentdb.sql...")
with open("agentdb.sql", "r", encoding="utf-8") as f:
    lines = f.readlines()

# 过滤掉以 \ 开头的 psql 专有命令和空行
clean_lines = []
for line in lines:
    stripped = line.strip()
    if stripped.startswith("\\") or not stripped:
        continue
    clean_lines.append(line)

sql_content = "".join(clean_lines)

print("正在导入数据到云端...")
cursor.execute(sql_content)
conn.commit()

cursor.close()
conn.close()
print("数据库导入成功！🎉")