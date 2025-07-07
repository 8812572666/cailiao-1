import streamlit as st
import pandas as pd
import os
from PIL import Image
import io
import mysql.connector
from mysql.connector import Error
import base64
import oss2  # 添加oss2导入
import math  # 添加用于分页计算

# 添加辅助函数到文件顶部
def get_safe_index(value, options, default=0):
    """安全获取选项索引，避免类型错误"""
    try:
        if value and isinstance(value, (int, str)) and value in options:
            return options.index(value)
        return default
    except (ValueError, TypeError):
        return default

# 添加自定义CSS样式
st.markdown("""
<style>
    /* 莫兰迪冷色系渐变背景 */
    .main {
        background: linear-gradient(135deg, 
            #E8EFF1 0%,
            #D5E1E8 50%,
            #C9D6E0 100%
        );
    }
    
    /* 全局字体设置 */
    * {
        font-family: "SF Pro Display", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* 标题样式 */
    h1 {
        color: #2C3E50;
        font-weight: 700;
        font-size: 2.8rem;
        line-height: 1.4;
        letter-spacing: -0.02em;
        margin-bottom: 1.5rem;
        text-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    h2 {
        color: #34495E;
        font-weight: 600;
        font-size: 1.8rem;
        line-height: 1.3;
        margin: 1.2rem 0;
    }
    
    /* 正文文本样式 */
    p {
        color: #4A5568;
        line-height: 1.6;
        font-size: 1.1rem;
        letter-spacing: 0.01em;
    }
    
    /* 卡片样式 */
    .card {
        background-color: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(10px);
        padding: 1.8rem;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        height: 100%;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid rgba(255, 255, 255, 0.5);
    }
    
    .card:hover {
        transform: translateY(-4px) scale(1.01);
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
    }
    
    /* 按钮样式 */
    .stButton button {
        background: linear-gradient(135deg, #6B8CAE 0%, #4A6F8C 100%);
        color: white;
        border-radius: 12px;
        padding: 0.6rem 1.2rem;
        font-weight: 500;
        border: none;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .stButton button:hover {
        background: linear-gradient(135deg, #5A7B9D 0%, #395E7B 100%);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        transform: translateY(-2px);
    }
    
    /* 数据框样式 */
    .dataframe {
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 12px;
        border: 1px solid rgba(211, 220, 230, 0.5);
        padding: 1.2rem;
        box-shadow: 0 2px 12px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }
    
    .dataframe:hover {
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
    }
    
    /* 选择框样式 */
    .row-widget.stSelectbox div[data-baseweb="select"] {
        background-color: rgba(255, 255, 255, 0.9);
        border-radius: 10px;
        border: 1px solid rgba(211, 220, 230, 0.5);
        transition: all 0.3s ease;
    }
    
    .row-widget.stSelectbox div[data-baseweb="select"]:hover {
        border-color: #6B8CAE;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    
    /* 信息标签样式 */
    .info-tag {
        display: inline-block;
        padding: 0.4rem 1rem;
        background: rgba(107, 140, 174, 0.1);
        color: #4A6F8C;
        border-radius: 20px;
        font-size: 0.95rem;
        margin: 0.3rem;
        backdrop-filter: blur(4px);
        border: 1px solid rgba(107, 140, 174, 0.2);
        transition: all 0.3s ease;
    }
    
    .info-tag:hover {
        background: rgba(107, 140, 174, 0.15);
        transform: translateY(-1px);
    }
    
    /* 分割线样式 */
    .gradient-line {
        height: 2px;
        background: linear-gradient(90deg, 
            rgba(107, 140, 174, 0) 0%, 
            rgba(107, 140, 174, 0.3) 50%, 
            rgba(107, 140, 174, 0) 100%
        );
        margin: 2.5rem 0;
    }
    
    /* 页眉样式 */
    div[data-testid="stHeader"] {
        background-color: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(12px);
        border-bottom: 1px solid rgba(211, 220, 230, 0.3);
    }
    
    /* 图片容器样式 */
    div.stImage {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    
    div.stImage:hover {
        transform: scale(1.02);
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
    }

    .connection-status {
        padding: 8px 15px;
        border-radius: 8px;
        margin: 10px 0;
        font-size: 0.9rem;
    }
    .connection-status.success {
        background-color: rgba(0, 200, 81, 0.1);
        color: #00c851;
        border: 1px solid rgba(0, 200, 81, 0.2);
    }
    .connection-status.error {
        background-color: rgba(255, 68, 68, 0.1);
        color: #ff4444;
        border: 1px solid rgba(255, 68, 68, 0.2);
    }
    
    /* 分页按钮样式 */
    .pagination-button {
        background-color: #f0f2f6;
        border: 1px solid #ddd;
        color: #333;
        padding: 8px 16px;
        border-radius: 4px;
        cursor: pointer;
        transition: background-color 0.3s;
        width: 100%;
    }
    
    .pagination-button:hover {
        background-color: #e0e2e6;
    }
    
    .pagination-button:disabled {
        background-color: #f8f9fa;
        color: #aaa;
        cursor: not-allowed;
        border: 1px solid #eee;
    }
    
    .pagination-info {
        text-align: center;
        padding: 10px;
        color: #666;
    }
    
    .rows-per-page {
        text-align: center;
        padding: 10px;
    }
</style>
""", unsafe_allow_html=True)

# 设置页面标题和图标
st.set_page_config(
    page_title="材料数据",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="auto"
)

# OSS配置
access_key_id = 'LTAI5tAzmjQ8GBZDocozoBSy'
access_key_secret = '42cL9W2JOvMuYgTVGAES6Hi2593BjP'
endpoint = 'oss-cn-wuhan-lr.aliyuncs.com'
text_bucket_name = 'testcxf'
image_bucket_name = 'tupian-cxf'

# 本地数据库配置
LOCAL_DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '1234',
    'port': 3306,
    'charset': 'utf8mb4',
    'connect_timeout': 10,
    'use_pure': True,
    'auth_plugin': 'mysql_native_password',
    'raise_on_warnings': True,
    'buffered': True
}

# 云端数据库配置
CLOUD_DB_CONFIG = {
    'host': 'rm-cn-w5g4c7g10000azfo.rwlb.rds.aliyuncs.com',
    'user': 'cxf8812572666',
    'password': 'Cxf88023706',
    'port': 3306,
    'charset': 'utf8mb4',
    'connect_timeout': 10,
    'use_pure': True,
    'auth_plugin': 'mysql_native_password',
    'raise_on_warnings': True,
    'buffered': True
}

# 首先定义所有辅助函数
def get_available_files():
    image_files = []
    text_files = []
    
    image_dir = os.path.join("data", "图片对象存储")
    if os.path.exists(image_dir):
        image_files = [f for f in os.listdir(image_dir) if f.endswith('.jfif')]
        image_files.sort(key=lambda x: int(x.split('.')[0]))
    
    text_dir = os.path.join("data", "文本对象存储")
    if os.path.exists(text_dir):
        text_files = [f for f in os.listdir(text_dir) if f.endswith('.txt')]
        text_files.sort(key=lambda x: int(x.split('.')[0]))
    
    return image_files, text_files

@st.cache_data
def load_image(image_path):
    try:
        return Image.open(image_path)
    except Exception as e:
        st.error(f"无法加载图片: {str(e)}")
        return None

@st.cache_data
def load_text(text_path):
    try:
        with open(text_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        st.error(f"无法加载文本: {str(e)}")
        return ""

def get_binary_file_downloader_html(file_path):
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
        return data
    except Exception as e:
        st.error(f"无法读取文件: {str(e)}")
        return None

# 创建数据库连接函数（支持本地和云端）
def create_db_connection(is_cloud=False):
    connection = None
    config = CLOUD_DB_CONFIG if is_cloud else LOCAL_DB_CONFIG
    try:
        # 首先尝试连接
        connection = mysql.connector.connect(**config)
        
        if connection.is_connected():
            db_info = connection.get_server_info()
            st.session_state['db_info'] = f"MySQL 服务器版本: {db_info}"
            return connection
        else:
            st.error("数据库连接失败: 无法建立连接")
            return None
            
    except mysql.connector.Error as err:
        error_msg = ""
        if err.errno == mysql.connector.errorcode.ER_ACCESS_DENIED_ERROR:
            error_msg = "数据库连接失败: 用户名或密码错误"
        elif err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
            error_msg = "数据库连接失败: 数据库不存在"
        else:
            error_msg = f"数据库连接失败: {err}"
        st.error(error_msg)
        return None
        
    except Exception as e:
        st.error(f"发生未知错误: {str(e)}")
        return None

# 获取所有数据库
def get_databases(is_cloud=False):
    try:
        connection = create_db_connection(is_cloud)
        if connection and connection.is_connected():
            try:
                cursor = connection.cursor()
                cursor.execute("SHOW DATABASES")
                databases = [db[0] for db in cursor.fetchall()]
                return databases
            except mysql.connector.Error as err:
                st.error(f"获取数据库列表错误: {err}")
                return []
            finally:
                if cursor:
                    cursor.close()
                if connection:
                    connection.close()
        else:
            st.error("无法获取数据库列表：数据库连接失败")
            return []
    except Exception as e:
        st.error(f"获取数据库列表时发生错误: {str(e)}")
        return []



# 获取数据库中的所有表
def get_tables(database, is_cloud=False):
    connection = create_db_connection(is_cloud)
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute(f"USE `{database}`")  # 使用反引号包裹数据库名
            cursor.execute("SHOW TABLES")
            tables = [table[0] for table in cursor.fetchall()]
            cursor.close()
            connection.close()
            return tables
        except Error as e:
            st.error(f"获取数据表错误: {e}")
            return []
        finally:
            if connection.is_connected():
                connection.close()
    return []

# 加载本地材料名称数据
@st.cache_data
def load_local_material_names():
    try:
        df = pd.read_excel("data/材料名称.xlsx")
        if '材料名称' not in df.columns:
            if len(df) == 0:
                df['材料名称'] = [f'材料{i+1}' for i in range(10)]
            else:
                df['材料名称'] = [f'材料{i+1}' for i in range(len(df))]
            return df
    except Exception as e:
        st.error(f"无法加载材料名称数据: {str(e)}")
        return pd.DataFrame({'材料名称': [f'材料{i+1}' for i in range(10)]})

# 初始化OSS客户端
def init_oss_client():
    auth = oss2.Auth(access_key_id, access_key_secret)
    text_bucket = oss2.Bucket(auth, endpoint, text_bucket_name)
    image_bucket = oss2.Bucket(auth, endpoint, image_bucket_name)
    return text_bucket, image_bucket

# 从OSS获取文本内容
def get_text_from_oss(text_bucket, object_name):
    try:
        object_stream = text_bucket.get_object(object_name)
        return object_stream.read().decode('utf-8')
    except oss2.exceptions.NoSuchKey:
        return None
    except Exception as e:
        st.error(f"获取文本时出错: {str(e)}")
        return None

# 从OSS获取图片
def get_image_from_oss(image_bucket, object_name):
    try:
        object_stream = image_bucket.get_object(object_name)
        image_data = object_stream.read()
        return Image.open(io.BytesIO(image_data))
    except oss2.exceptions.NoSuchKey:
        return None
    except Exception as e:
        st.error(f"获取图片时出错: {str(e)}")
        return None

# 列出OSS存储桶中的所有对象
def list_oss_objects(bucket):
    objects = []
    for obj in oss2.ObjectIterator(bucket):
        objects.append(obj.key)
    return objects

# 获取表的总行数
def get_table_count(database, table, is_cloud=False):
    connection = create_db_connection(is_cloud)
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute(f"USE `{database}`")
            cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
            count = cursor.fetchone()[0]
            cursor.close()
            connection.close()
            return count
        except Error as e:
            st.error(f"获取表格行数错误: {e}")
            return 0
        finally:
            if connection.is_connected():
                connection.close()
    return 0

# 优化的表数据获取函数
@st.cache_data(ttl=600)  # 缓存10分钟
def get_table_data(database, table, is_cloud=False, page=1, rows_per_page=50):
    connection = create_db_connection(is_cloud)
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute(f"USE `{database}`")
            
            # 计算偏移量
            offset = (page - 1) * rows_per_page
            
            # 使用 LIMIT 和 OFFSET 进行分页查询
            query = f"""
                SELECT * FROM `{table}`
                LIMIT {rows_per_page} OFFSET {offset}
            """
            cursor.execute(query)
            
            columns = [desc[0] for desc in cursor.description]
            data = cursor.fetchall()
            cursor.close()
            connection.close()
            
            # 创建DataFrame
            df = pd.DataFrame(data, columns=columns)
            
            # 确保有图片和文本说明列
            if '图片' not in df.columns:
                df['图片'] = [''] * len(df)
            if '文本说明' not in df.columns:
                df['文本说明'] = [''] * len(df)
            
            # 添加序号列（从offset+1开始）
            df['序号'] = pd.Series(range(offset + 1, offset + len(df) + 1))
            
            # 根据序号生成图片和文本文件名
            if is_cloud:
                # 云端模式：根据序号生成图片和文本文件名
                df['图片'] = df['序号'].apply(lambda x: next((f"{x}{ext}" for ext in ['.jpg', '.jpeg', '.png', '.jfif'] 
                                                          if f"{x}{ext}" in st.session_state['image_objects']), ""))
                df['文本说明'] = df['序号'].apply(lambda x: f"{x}.txt" if f"{x}.txt" in st.session_state['text_objects'] else "")
            else:
                # 本地模式：根据序号生成图片和文本文件名
                image_files, text_files = get_available_files()
                df['图片'] = df['序号'].apply(lambda x: f"{x}.jfif" if f"{x}.jfif" in image_files else "")
                df['文本说明'] = df['序号'].apply(lambda x: f"{x}.txt" if f"{x}.txt" in text_files else "")
            
            # 设置序号为索引
            df.set_index('序号', inplace=True)
            return df
        except Error as e:
            st.error(f"获取表格数据错误: {e}")
            return None
        finally:
            if connection.is_connected():
                connection.close()
    return None

# 修改分页相关的会话状态初始化
if 'page_number' not in st.session_state:
    st.session_state['page_number'] = 1

# 固定每页显示100行
st.session_state['rows_per_page'] = 100

if 'total_rows' not in st.session_state:
    st.session_state['total_rows'] = 0

def display_pagination_controls(total_rows):
    """显示分页控件"""
    # 先显示数据表
    if 'df_display' in st.session_state and st.session_state['df_display'] is not None:
        st.dataframe(st.session_state['df_display'], use_container_width=True, height=400)
    
    # 显示总记录数和分页信息
    total_pages = math.ceil(total_rows / st.session_state['rows_per_page'])
    st.markdown(f"""
        <div class="pagination-info">
            📑 共 {total_rows} 条记录 | 第 {st.session_state['page_number']} 页 / 共 {total_pages} 页
        </div>
    """, unsafe_allow_html=True)
    
    # 分页按钮
    col1, col2, col3 = st.columns([2, 2, 2])
    
    with col1:
        prev_disabled = st.session_state['page_number'] <= 1
        if st.button(
            "⬅️ 上一页",
            key="prev_page",
            disabled=prev_disabled,
            type="secondary",
            use_container_width=True
        ):
            st.session_state['page_number'] -= 1
            # 重新加载数据
            df = get_table_data(
                st.session_state['selected_db'],
                st.session_state['selected_table'],
                is_cloud=(data_source == "云端数据"),
                page=st.session_state['page_number'],
                rows_per_page=st.session_state['rows_per_page']
            )
            if df is not None:
                st.session_state['df_display'] = df
            st.rerun()
    
    with col3:
        next_disabled = st.session_state['page_number'] >= total_pages
        if st.button(
            "下一页 ➡️",
            key="next_page",
            disabled=next_disabled,
            type="secondary",
            use_container_width=True
        ):
            st.session_state['page_number'] += 1
            # 重新加载数据
            df = get_table_data(
                st.session_state['selected_db'],
                st.session_state['selected_table'],
                is_cloud=(data_source == "云端数据"),
                page=st.session_state['page_number'],
                rows_per_page=st.session_state['rows_per_page']
            )
            if df is not None:
                st.session_state['df_display'] = df
            st.rerun()

# 页面标题区域
st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <h1 style="margin-bottom: 0.5rem;">🔬 材料数据分析平台</h1>
        <div class="info-tag">专业 · 高效 · 直观</div>
    </div>
""", unsafe_allow_html=True)

# 简介卡片
st.markdown("""
    <div class="card" style="margin-bottom: 2.5rem;">
        <p style="color: #2c5282; margin: 0; font-size: 1.15rem; display: flex; align-items: center; gap: 0.8rem;">
            <span style="font-size: 1.4rem;">💡</span>
            这个应用展示了不同材料的性能指标、图片和文本说明数据。通过直观的界面，您可以轻松查看和分析各种材料的特性。
        </p>
    </div>
""", unsafe_allow_html=True)

# 在数据来源选择之前添加初始化会话状态的代码
if 'cloud_data_initialized' not in st.session_state:
    st.session_state['cloud_data_initialized'] = False

if 'local_data_initialized' not in st.session_state:
    st.session_state['local_data_initialized'] = False

if 'selected_db' not in st.session_state:
    st.session_state['selected_db'] = None

if 'selected_table' not in st.session_state:
    st.session_state['selected_table'] = None

if 'show_tables' not in st.session_state:
    st.session_state['show_tables'] = False

if 'show_data' not in st.session_state:
    st.session_state['show_data'] = False

if 'df_display' not in st.session_state:
    st.session_state['df_display'] = None

if 'oss_initialized' not in st.session_state:
    st.session_state['oss_initialized'] = False
    text_bucket, image_bucket = init_oss_client()
    st.session_state['text_bucket'] = text_bucket
    st.session_state['image_bucket'] = image_bucket
    st.session_state['text_objects'] = list_oss_objects(text_bucket)
    st.session_state['image_objects'] = list_oss_objects(image_bucket)
    st.session_state['oss_initialized'] = True

# 数据来源选择
data_source = st.radio(
    "选择数据来源",
    ["本地数据", "云端数据"],
    horizontal=True
)

if data_source == "本地数据":
    # 只在第一次切换到本地数据时初始化连接
    if not st.session_state['local_data_initialized']:
        st.info("正在连接本地数据库...")
        connection = create_db_connection(is_cloud=False)
        if connection and connection.is_connected():
            st.markdown("""
                <div class="connection-status success">
                    ✅ 本地数据库连接成功
                </div>
            """, unsafe_allow_html=True)
            
            if 'db_info' in st.session_state:
                st.info(st.session_state['db_info'])
                
            connection.close()
            
            # 获取数据库列表
            databases = get_databases(is_cloud=False)
            if databases:
                st.session_state['local_databases'] = databases
                st.session_state['local_data_initialized'] = True
            else:
                st.error("未能获取本地数据库列表，请检查数据库权限")
        else:
            st.markdown("""
                <div class="connection-status error">
                    ❌ 本地数据库连接失败，请检查数据库服务是否启动
        </div>
    """, unsafe_allow_html=True)
    
    # 如果已经初始化过，直接使用保存的状态
    if st.session_state['local_data_initialized']:
        col_db, col_table = st.columns(2)
        
        with col_db:
            # 获取当前选中的数据库
            current_db = st.session_state.get('selected_db', '')
            db_index = get_safe_index(current_db, st.session_state['local_databases'])
            
            selected_db = st.selectbox(
                "选择数据库",
                options=st.session_state['local_databases'],
                key="local_database_selector",
                help="选择要连接的本地数据库",
                index=db_index
            )
            
            if selected_db != st.session_state['selected_db']:
                st.session_state['selected_db'] = selected_db
                st.session_state['show_tables'] = True
                st.session_state['page_number'] = 1  # 重置页码
                tables = get_tables(selected_db, is_cloud=False)
                if tables:
                    st.session_state['tables'] = tables
                    st.success(f"已选择数据库: {selected_db}")
                else:
                    st.warning(f"在数据库 {selected_db} 中未找到可用的数据表")

        with col_table:
            if 'show_tables' in st.session_state and st.session_state['show_tables'] and 'tables' in st.session_state:
                # 获取当前选中的表
                current_table = st.session_state.get('selected_table', '')
                table_index = get_safe_index(current_table, st.session_state['tables'])
                
                selected_table = st.selectbox(
                    "选择数据表",
                    options=st.session_state['tables'],
                    key="local_table_selector",
                    help="选择要显示的数据表",
                    index=table_index
                )
                
                if selected_table != st.session_state['selected_table']:
                    st.session_state['selected_table'] = selected_table
                    st.session_state['show_data'] = True
                    st.session_state['page_number'] = 1  # 重置页码
                    
                    # 获取总行数
                    with st.spinner('正在计算总行数...'):
                        total_rows = get_table_count(st.session_state['selected_db'], selected_table, is_cloud=False)
                        st.session_state['total_rows'] = total_rows
                    
                    # 加载第一页数据
                    with st.spinner('正在加载数据...'):
                        df = get_table_data(
                            st.session_state['selected_db'],
                            selected_table,
                            is_cloud=False,
                            page=st.session_state['page_number'],
                            rows_per_page=st.session_state['rows_per_page']
                        )
                        if df is not None:
                            st.session_state['df_display'] = df
                            st.success(f"已选择数据表: {selected_table}")
                        else:
                            st.error("无法加载表格数据")

        # 显示分页控件和数据
        if 'show_data' in st.session_state and st.session_state['show_data'] and st.session_state['df_display'] is not None:
            display_pagination_controls(st.session_state['total_rows'])

else:
    # 云端数据库和表格选择
    st.markdown("""
        <div style="display: flex; align-items: center; margin-bottom: 1rem;">
            <h2 style="margin: 0; margin-right: 1rem;">📋 云端数据总览</h2>
        </div>
    """, unsafe_allow_html=True)

    # 只在第一次切换到云端数据时初始化连接
    if not st.session_state['cloud_data_initialized']:
        st.info("正在连接数据库...")
        connection = create_db_connection(is_cloud=True)
        if connection and connection.is_connected():
            st.markdown("""
                <div class="connection-status success">
                    ✅ 数据库连接成功
                </div>
            """, unsafe_allow_html=True)
            
            if 'db_info' in st.session_state:
                st.info(st.session_state['db_info'])
                
            connection.close()
            
            # 获取数据库列表
            databases = get_databases(is_cloud=True)
            if databases:
                st.session_state['databases'] = databases
                st.session_state['cloud_data_initialized'] = True
            else:
                st.error("未能获取数据库列表，请检查数据库权限")
        else:
            st.markdown("""
                <div class="connection-status error">
                    ❌ 数据库连接失败，请检查网络连接或联系管理员
                </div>
            """, unsafe_allow_html=True)

    # 如果已经初始化过，直接使用保存的状态
    if st.session_state['cloud_data_initialized']:
        col_db, col_table = st.columns(2)
        
        with col_db:
            # 获取当前选中的数据库
            current_db = st.session_state.get('selected_db', '')
            db_index = get_safe_index(current_db, st.session_state['databases'])
            
            selected_db = st.selectbox(
                "选择数据库",
                options=st.session_state['databases'],
                key="database_selector",
                help="选择要连接的数据库",
                index=db_index
            )
            
            if selected_db != st.session_state['selected_db']:
                st.session_state['selected_db'] = selected_db
                st.session_state['show_tables'] = True
                st.session_state['page_number'] = 1  # 重置页码
                tables = get_tables(selected_db, is_cloud=True)
                if tables:
                    st.session_state['tables'] = tables
                    st.success(f"已选择数据库: {selected_db}")
                else:
                    st.warning(f"在数据库 {selected_db} 中未找到可用的数据表")

        with col_table:
            if 'show_tables' in st.session_state and st.session_state['show_tables'] and 'tables' in st.session_state:
                # 获取当前选中的表
                current_table = st.session_state.get('selected_table', '')
                table_index = get_safe_index(current_table, st.session_state['tables'])
                
                selected_table = st.selectbox(
                    "选择数据表",
                    options=st.session_state['tables'],
                    key="table_selector",
                    help="选择要显示的数据表",
                    index=table_index
                )
                
                if selected_table != st.session_state['selected_table']:
                    st.session_state['selected_table'] = selected_table
                    st.session_state['show_data'] = True
                    st.session_state['page_number'] = 1  # 重置页码
                    
                    # 获取总行数
                    with st.spinner('正在计算总行数...'):
                        total_rows = get_table_count(st.session_state['selected_db'], selected_table, is_cloud=True)
                        st.session_state['total_rows'] = total_rows
                    
                    # 加载第一页数据
                    with st.spinner('正在加载数据...'):
                        df = get_table_data(
                            st.session_state['selected_db'],
                            selected_table,
                            is_cloud=True,
                            page=st.session_state['page_number'],
                            rows_per_page=st.session_state['rows_per_page']
                        )
                        if df is not None:
                            st.session_state['df_display'] = df
                            st.success(f"已选择数据表: {selected_table}")
                        else:
                            st.error("无法加载表格数据")

        # 显示分页控件和数据
        if 'show_data' in st.session_state and st.session_state['show_data'] and st.session_state['df_display'] is not None:
            display_pagination_controls(st.session_state['total_rows'])

# 修改详细信息显示部分
def display_detail_info(df_to_display, row_idx, data_source):
    """显示详细信息"""
    # 创建三列布局
    col1, col2, col3 = st.columns([1.8, 1.2, 1])
    
    # 性能数据显示
    with col1:
        st.markdown(f"""
            <div class="card" style="padding: 0.8rem 1rem;">
                <h3 style="color: #2c5282; margin: 0; font-size: 1rem; display: flex; align-items: center;">
                    <span style="margin-right: 0.5rem;">📊</span>
                    性能数据
                </h3>
            </div>
        """, unsafe_allow_html=True)
        display_data = df_to_display.iloc[row_idx].drop(['图片', '文本说明'])
        st.write(display_data.to_dict())
    
    # 图片显示
    with col2:
        st.markdown("""
            <div class="card" style="padding: 0.8rem 1rem;">
                <h3 style="color: #2c5282; margin: 0; font-size: 1rem; display: flex; align-items: center;">
                    <span style="margin-right: 0.5rem;">🖼️</span>
                    图片预览
                </h3>
            </div>
        """, unsafe_allow_html=True)
        
        image_filename = df_to_display.iloc[row_idx]['图片']
        if image_filename:
            if data_source == "本地数据":
                image_files, _ = get_available_files()
                if image_filename in image_files:
                    image_path = os.path.join("data", "图片对象存储", image_filename)
                    image = load_image(image_path)
                    if image:
                        st.image(image, caption=f"图片 {image_filename}", use_container_width=True)
                        image_data = get_binary_file_downloader_html(image_path)
                        if image_data is not None:
                            st.download_button(
                                label="⬇️ 下载图片",
                                data=image_data,
                                file_name=image_filename,
                                mime="image/jpeg"
                            )
                else:
                    st.warning(f"图片文件不存在: {image_filename}")
            else:
                image = get_image_from_oss(st.session_state['image_bucket'], image_filename)
                if image:
                    st.image(image, caption=f"图片 {image_filename}", use_container_width=True)
                    # 获取图片数据用于下载
                    image_stream = io.BytesIO()
                    image.save(image_stream, format='JPEG')
                    image_data = image_stream.getvalue()
                    st.download_button(
                        label="⬇️ 下载图片",
                        data=image_data,
                        file_name=image_filename,
                        mime="image/jpeg"
                    )
        else:
            st.warning("图片文件名为空，无法显示。")
    
    # 文本说明显示
    with col3:
        st.markdown("""
            <div class="card" style="padding: 0.8rem 1rem;">
                <h3 style="color: #2c5282; margin: 0; font-size: 1rem; display: flex; align-items: center;">
                    <span style="margin-right: 0.5rem;">📝</span>
                    文本说明
                </h3>
            </div>
        """, unsafe_allow_html=True)
        
        text_filename = df_to_display.iloc[row_idx]['文本说明']
        if text_filename:
            if data_source == "本地数据":
                _, text_files = get_available_files()
                if text_filename in text_files:
                    text_path = os.path.join("data", "文本对象存储", text_filename)
                    text_content = load_text(text_path)
                    if text_content:
                        st.markdown(f"""
                            <div style="background-color: #f8fafc; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
                                {text_content}
                            </div>
                        """, unsafe_allow_html=True)
                        if os.path.exists(text_path):
                            with open(text_path, 'r', encoding='utf-8') as f:
                                text_data = f.read()
                            st.download_button(
                                label="📄 下载文本说明",
                                data=text_data,
                                file_name=text_filename,
                                mime="text/plain"
                            )
                else:
                    st.warning(f"文本文件不存在: {text_filename}")
            else:
                text_content = get_text_from_oss(st.session_state['text_bucket'], text_filename)
                if text_content:
                    st.markdown(f"""
                        <div style="background-color: #f8fafc; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
                            {text_content}
                        </div>
                    """, unsafe_allow_html=True)
                    st.download_button(
                        label="📄 下载文本说明",
                        data=text_content,
                        file_name=text_filename,
                        mime="text/plain"
                    )
        else:
            st.warning("文本说明文件名为空，无法显示。")

# 在主代码中调用详细信息显示函数
if ('df_display' in st.session_state and st.session_state['df_display'] is not None):
    df_to_display = st.session_state['df_display']
    
    st.markdown("""
        <div class="gradient-line"></div>
        <h2 style="color: #2c5282; display: flex; align-items: center;">
            <span style="margin-right: 0.5rem;">🔎</span> 详细信息
        </h2>
    """, unsafe_allow_html=True)

    # 选择器和详细信息显示
    current_page = st.session_state.get('page_number', 1)
    rows_per_page = st.session_state.get('rows_per_page', 50)
    start_row = (current_page - 1) * rows_per_page + 1
    end_row = start_row + len(df_to_display) - 1
    
    valid_rows = range(start_row, end_row + 1)
    selected_row = st.selectbox(
        "",
        valid_rows,
        format_func=lambda x: f"第 {x} 行"
    )

    if selected_row:
        row_idx = selected_row - start_row
        display_detail_info(df_to_display, row_idx, data_source)

# 添加页脚
st.markdown("""
    <div style="margin-top: 4rem; text-align: center;">
        <div class="gradient-line"></div>
    </div>
""", unsafe_allow_html=True)
