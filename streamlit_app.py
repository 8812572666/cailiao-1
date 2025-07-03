import streamlit as st
import pandas as pd
import os
from PIL import Image
import io
import mysql.connector
from mysql.connector import Error
import base64
import oss2  # 添加oss2导入

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

# 数据库连接配置
DB_CONFIG = {
    'host': 'rm-bp1174e22118zcprheo.mysql.rds.aliyuncs.com',
    'user': 'cxf8812572666',
    'password': 'Cxf88023706',
    'port': 3306,
    'charset': 'utf8mb4',
    'connect_timeout': 10,
    'use_pure': True,  # 使用纯Python实现
    'auth_plugin': 'mysql_native_password',  # 指定认证插件
    'raise_on_warnings': True,
    'buffered': True
}

# 数据库连接函数
def create_db_connection():
    connection = None
    try:
        # 首先尝试连接
        connection = mysql.connector.connect(**DB_CONFIG)
        
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
def get_databases():
    try:
        connection = create_db_connection()
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
def get_tables(database):
    connection = create_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute(f"USE {database}")
            cursor.execute("SHOW TABLES")
            tables = [table[0] for table in cursor.fetchall()]
            cursor.close()
            connection.close()
            return tables
        except Error as e:
            st.error(f"获取表格列表错误: {e}")
            return []
        finally:
            if connection.is_connected():
                connection.close()
    return []

# 获取表数据
def get_table_data(database, table):
    connection = create_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute(f"USE {database}")
            cursor.execute(f"SELECT * FROM {table}")
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
                
            return df
        except Error as e:
            st.error(f"获取表格数据错误: {e}")
            return None
        finally:
            if connection.is_connected():
                connection.close()
    return None

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

# 自定义CSS样式
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
    </style>
""", unsafe_allow_html=True)

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
    # 加载本地数据
    material_df = load_local_material_names()
    rows = len(material_df)
    image_files, text_files = get_available_files()

    # 创建本地数据字典
    data_dict = {'序号': range(1, rows + 1)}  # 添加从1开始的序号列
    data_dict['材料名称'] = material_df['材料名称'].tolist()
    for i in range(1, 11):
        data_dict[f'性能{i}'] = ['待添加'] * rows
    data_dict['图片'] = [image_files[i] if i < len(image_files) else '' for i in range(rows)]
    data_dict['文本说明'] = [text_files[i] if i < len(text_files) else '' for i in range(rows)]
    
    df_display = pd.DataFrame(data_dict)
    df_display.set_index('序号', inplace=True)  # 设置序号列为索引
    
    st.markdown(f"""
        <div style="display: flex; align-items: center; margin-bottom: 1rem;">
            <h2 style="margin: 0; margin-right: 1rem;">📋 本地数据总览</h2>
            <div class="info-tag">
                <span>📑 共 {len(df_display)} 条记录</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.dataframe(df_display, use_container_width=True, height=400)

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
        connection = create_db_connection()
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
            databases = get_databases()
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
            selected_db = st.selectbox(
                "选择数据库",
                options=st.session_state['databases'],
                key="database_selector",
                help="选择要连接的数据库",
                index=st.session_state['databases'].index(st.session_state['selected_db']) if st.session_state['selected_db'] in st.session_state['databases'] else 0
            )
            
            if selected_db != st.session_state['selected_db']:
                st.session_state['selected_db'] = selected_db
                st.session_state['show_tables'] = True
                tables = get_tables(selected_db)
                if tables:
                    st.session_state['tables'] = tables
                    st.success(f"已选择数据库: {selected_db}")
                else:
                    st.warning(f"在数据库 {selected_db} 中未找到可用的数据表")

        with col_table:
            if 'show_tables' in st.session_state and st.session_state['show_tables'] and 'tables' in st.session_state:
                selected_table = st.selectbox(
                    "选择数据表",
                    options=st.session_state['tables'],
                    key="table_selector",
                    help="选择要显示的数据表",
                    index=st.session_state['tables'].index(st.session_state['selected_table']) if st.session_state['selected_table'] in st.session_state['tables'] else 0
                )
                
                if selected_table != st.session_state['selected_table']:
                    st.session_state['selected_table'] = selected_table
                    st.session_state['show_data'] = True
                    # 加载新的表格数据
                    with st.spinner('正在加载数据...'):
                        df = get_table_data(st.session_state['selected_db'], selected_table)
                        if df is not None:
                            # 添加序号列
                            df.insert(0, '序号', range(1, len(df) + 1))
                            
                            # 添加图片和文本说明列
                            # 检查多种可能的图片扩展名
                            df['图片'] = [next((f"{i}{ext}" for ext in ['.jpg', '.jpeg', '.png', '.jfif'] 
                                              if f"{i}{ext}" in st.session_state['image_objects']), "") 
                                        for i in range(1, len(df) + 1)]
                            df['文本说明'] = [f"{i}.txt" if f"{i}.txt" in st.session_state['text_objects'] else "" 
                                        for i in range(1, len(df) + 1)]
                            
                            # 设置序号为索引
                            df.set_index('序号', inplace=True)
                            st.session_state['df_display'] = df
                            st.success(f"已选择数据表: {selected_table}")
                        else:
                            st.error("无法加载表格数据")

        # 显示选中的数据表内容
        if 'show_data' in st.session_state and st.session_state['show_data'] and st.session_state['df_display'] is not None:
            st.markdown(f"""
                <div class="info-tag">
                    <span>📑 共 {len(st.session_state['df_display'])} 条记录</span>
                </div>
            """, unsafe_allow_html=True)
            st.dataframe(st.session_state['df_display'], use_container_width=True, height=400)

# 如果有数据显示，则显示详细信息部分
if ('df_display' in locals() and df_display is not None) or ('df_display' in st.session_state and st.session_state['df_display'] is not None):
    df_to_display = df_display if 'df_display' in locals() else st.session_state['df_display']
    
    st.markdown("""
        <div class="gradient-line"></div>
        <h2 style="color: #2c5282; display: flex; align-items: center;">
            <span style="margin-right: 0.5rem;">🔎</span> 详细信息
        </h2>
    """, unsafe_allow_html=True)

    # 选择器和详细信息显示
    valid_rows = range(1, len(df_to_display) + 1)
    selected_row = st.selectbox(
        "",
        valid_rows,
        format_func=lambda x: f"第 {x} 行"
    )

    if selected_row:
        row_idx = selected_row - 1
        
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
            
            if data_source == "本地数据":
                image_filename = df_to_display.iloc[row_idx]['图片']
                if image_filename and image_filename in image_files:
                    image_path = os.path.join("data", "图片对象存储", image_filename)
                    image = load_image(image_path)
                    if image:
                        st.image(image, caption="图片预览", use_container_width=True)
                        image_data = get_binary_file_downloader_html(image_path)
                        if image_data is not None:
                            st.download_button(
                                label="⬇️ 下载图片",
                                data=image_data,
                                file_name=image_filename,
                                mime="image/jpeg"
                            )
            else:
                image_filename = df_to_display.iloc[row_idx]['图片']
                if image_filename:
                    image = get_image_from_oss(st.session_state['image_bucket'], image_filename)
                    if image:
                        st.image(image, caption="图片预览", use_container_width=True)
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
            
            if data_source == "本地数据":
                text_filename = df_to_display.iloc[row_idx]['文本说明']
                if text_filename and text_filename in text_files:
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
                text_filename = df_to_display.iloc[row_idx]['文本说明']
                if text_filename:
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

# 添加页脚
st.markdown("""
    <div style="margin-top: 4rem; text-align: center;">
        <div class="gradient-line"></div>
    </div>
""", unsafe_allow_html=True)
