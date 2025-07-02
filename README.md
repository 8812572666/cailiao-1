# 材料数据管理系统

这是一个基于Streamlit开发的材料数据管理系统，支持本地数据和云端数据的展示与管理。

## 功能特点

- 支持本地数据和云端MySQL数据的切换展示
- 材料数据的性能指标展示
- 图片预览和下载功能
- 文本说明查看和下载功能
- 专业的UI设计和用户体验
- 响应式布局设计

## 安装要求

```bash
pip install -r requirements.txt
```

## 使用方法

1. 克隆项目到本地：
```bash
git clone [repository-url]
cd [repository-name]
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 启动应用：
```bash
streamlit run streamlit_app.py
```

4. 在浏览器中访问：
```
http://localhost:8501
```

## 数据结构

### 本地数据
- `/data/材料名称.xlsx`：材料基本信息
- `/data/图片对象存储/`：材料相关图片
- `/data/文本对象存储/`：材料说明文档

### 云端数据
- 支持连接到MySQL数据库
- 可选择不同数据库和数据表

## 配置说明

云端数据库连接配置：
- 主机：rm-bp1174e22118zcprheo.mysql.rds.aliyuncs.com
- 用户名：cxf8812572666
- 数据库：根据实际选择

## 许可证

本项目基于 MIT 许可证开源。
