import pandas as pd
import random
import re
import json
from flask import Flask, request, jsonify, render_template, send_from_directory
from sqlalchemy import create_engine, text
from datetime import datetime
import numpy as np
import os
import matplotlib
matplotlib.use('Agg')  # 使用非GUI后端
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import hashlib
import uuid

# 尝试导入orjson以提升JSON性能
try:
    import orjson
    def fast_json_dumps(obj):
        """使用orjson快速序列化，返回字符串"""
        return orjson.dumps(obj, option=orjson.OPT_INDENT_2).decode('utf-8')
    
    def fast_json_loads(s):
        """使用orjson快速反序列化"""
        return orjson.loads(s)
except ImportError:
    # 如果orjson未安装，回退到标准json
    def fast_json_dumps(obj):
        return json.dumps(obj, ensure_ascii=False, indent=2)
    
    def fast_json_loads(s):
        return json.loads(s)

# 全局配置matplotlib字体，避免重复设置
# 根据环境变量决定是否使用中文字体
enable_zh_cn = os.environ.get('enable_zh_CN', 'TRUE').upper() == 'TRUE'

if enable_zh_cn:
    # 只使用系统中确实存在的中文字体
    plt.rcParams['font.sans-serif'] = ['WenQuanYi Zen Hei', 'DejaVu Sans', 'sans-serif']
else:
    # 使用英文字体，不依赖中文字体
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'sans-serif']

plt.rcParams['axes.unicode_minus'] = False
# 禁用字体警告
import warnings
warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')


app = Flask(__name__)

# Use SQLite database with connection pool configuration
db_path = os.path.join(os.path.dirname(__file__), 'group_tool.db')
engine = create_engine(
    f"sqlite:///{db_path}",
    pool_size=2,           # 最大2个并发连接
    max_overflow=0,        # 不允许溢出连接
    pool_recycle=3600,     # 1小时后回收连接
    pool_pre_ping=True     # 连接前检查有效性
)

# 内存缓存
experiment_cache = {}
file_exists_cache = {}

# 数据库表定义SQL
create_charts_sql = """
    CREATE TABLE IF NOT EXISTS experiment_charts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        experiment_name VARCHAR(100) NOT NULL,
        parameter_name VARCHAR(50) NOT NULL,
        file_path TEXT NOT NULL,
        data_hash VARCHAR(64) NOT NULL,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        display_format VARCHAR(20) DEFAULT '原始数值',
        day_zero_date DATE,
        UNIQUE(experiment_name, parameter_name, display_format)
    );
    """

create_data_lock_sql = """
    CREATE TABLE IF NOT EXISTS experiment_data_locks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        experiment_name VARCHAR(100) NOT NULL,
        date DATE NOT NULL,
        is_locked BOOLEAN NOT NULL DEFAULT 0,
        locked_at DATETIME,
        locked_by VARCHAR(100),
        UNIQUE(experiment_name, date)
    );
    """

create_day_zero_sql = """
    CREATE TABLE IF NOT EXISTS experiment_day_zero (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        experiment_name VARCHAR(100) NOT NULL,
        day_zero_date DATE NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(experiment_name)
    );
    """

def clear_experiment_cache(experiment_name=None):
    """清除实验信息缓存"""
    if experiment_name:
        experiment_cache.pop(experiment_name, None)
    else:
        experiment_cache.clear()


def init_db():
    """Initialize the database and create the table if it doesn't exist"""
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS group_results (
        id VARCHAR(10) PRIMARY KEY,
        data TEXT NOT NULL,
        group_count INTEGER NOT NULL,
        layers TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """

    create_experiments_sql = """
    CREATE TABLE IF NOT EXISTS experiments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(100) UNIQUE NOT NULL,
        parameters TEXT NOT NULL,
        group_count INTEGER NOT NULL,
        group_type VARCHAR(20) NOT NULL,
        group_info TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """

    

with engine.connect() as conn:
        # 创建表
        conn.execute(text(create_charts_sql))
        conn.execute(text(create_data_lock_sql))
        conn.execute(text(create_day_zero_sql))
        
        # 检查并添加新字段（数据库迁移）
        try:
            # 检查display_format字段是否存在
            check_display_format = """
            PRAGMA table_info(experiment_charts)
            """
            columns = conn.execute(text(check_display_format)).fetchall()
            column_names = [col[1] for col in columns]
            
            if 'display_format' not in column_names:
                conn.execute(text("ALTER TABLE experiment_charts ADD COLUMN display_format VARCHAR(20) DEFAULT '原始数值'"))
            
            if 'day_zero_date' not in column_names:
                conn.execute(text("ALTER TABLE experiment_charts ADD COLUMN day_zero_date DATE"))
            
            # 由于UNIQUE约束改变，需要重新创建表（SQLite限制）
            # 这里我们采用简单的方式：删除旧约束，SQLite会自动处理
            conn.execute(text("DROP INDEX IF EXISTS idx_experiment_charts_unique"))
            
        except Exception as e:
            print(f"数据库迁移警告: {e}")
        
        conn.commit()


def layered_random_grouping(data, group_count, layers, group_sizes=None):
    """
    Perform layered random grouping based on specified columns with specified group sizes.
    This maintains balanced representation of each layer (parameter-binned group) across all groups
    while respecting the exact group sizes specified.

    Args:
        data (str): CSV string data with header
        group_count (int): Number of groups to divide into
        layers (list): List of column names to use for layering
        group_sizes (list or None): List of integers specifying the size of each group.
                                   If None, use equal distribution

    Returns:
        dict: The grouped data with groups as keys
    """
    # Read CSV data into a pandas DataFrame (优化内存使用)
    df = pd.read_csv(
        pd.io.common.StringIO(data),
        engine='c',           # 使用C引擎，更快
        low_memory=False      # 避免混合类型推断
    )

    # Check if the required layers exist in the DataFrame
    if not layers:
        raise ValueError("Layers must be specified")

    missing_columns = [col for col in layers if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Invalid layer columns: {missing_columns}")

    # Filter out non-numeric columns except the specified layers
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    valid_layers = [col for col in layers if col in numeric_cols]

    if not valid_layers:
        raise ValueError("No valid numeric columns found for layering")

    # For each layer column, create bins using pandas.cut
    for col in valid_layers:
        # Use pandas.cut to create 5 equal-width bins
        df[col + '_bin'] = pd.cut(df[col], bins=5, labels=False, duplicates='drop')

    # Create a combined layer key by concatenating all bin values
    layer_cols = [col + '_bin' for col in valid_layers]
    df['layer_key'] = df[layer_cols].apply(lambda x: tuple(x) if not x.isna().any() else None, axis=1)

    # If no group sizes specified, use equal distribution (with remainder handling)
    if group_sizes is None:
        total_animals = len(df)
        base_size = total_animals // group_count
        remainder = total_animals % group_count

        # Create group sizes: first 'remainder' groups get one extra animal
        group_sizes = [base_size + (1 if i < remainder else 0) for i in range(group_count)]
    else:
        # Validate that group_sizes has the correct length
        if len(group_sizes) != group_count:
            raise ValueError(f"group_sizes must have {group_count} elements, but has {len(group_count)}")

        # Validate that total size matches data size
        total_specified = sum(group_sizes)
        total_available = len(df)
        if total_specified != total_available:
            raise ValueError(f"Sum of group_sizes ({total_specified}) does not match data size ({total_available})")

    # Create a list that represents the final group assignment for each position
    # This ensures exact group sizes
    group_assignment = []
    for i, size in enumerate(group_sizes):
        group_assignment.extend([i] * size)

    # Shuffle the assignment list to randomize which positions get assigned to which groups
    import random
    random.shuffle(group_assignment)

    # Prepare all animals with their layer information
    all_animals = []
    for layer_key, layer_group in df.groupby('layer_key'):
        if layer_key is None:
            continue  # Skip rows with NaN values after binning

        # Add layer information to each animal and shuffle within layer
        layer_animals = layer_group.sample(frac=1, random_state=None).reset_index(drop=True)
        for idx, row in layer_animals.iterrows():
            animal_data = row.to_dict()
            animal_data['_layer_key'] = layer_key  # Preserve layer information
            all_animals.append(animal_data)

    # Shuffle all animals to ensure overall randomness
    random.shuffle(all_animals)

    # Assign animals to groups according to the randomized assignment
    result_groups = [[] for _ in range(group_count)]

    for i, animal in enumerate(all_animals):
        if i < len(group_assignment):
            group_idx = group_assignment[i]
            # Remove the temporary layer key before adding to result
            animal_clean = {k: v for k, v in animal.items() if k != '_layer_key'}
            result_groups[group_idx].append(animal_clean)

    # Convert to the expected return format
    grouped_data = {f"group_{i+1}": group_list for i, group_list in enumerate(result_groups)}

    return grouped_data


def evaluate_group_quality(groups, layers):
    """
    Evaluate the quality of a grouping result.
    Returns a score where lower is better.
    Considers:
    1. Variance between group means (lower is better)
    2. Sum of within-group variances (lower is better)
    """
    if not groups or not layers:
        return float('inf')
    
    # Calculate statistics for each group
    stats = calculate_group_statistics(groups, layers)
    
    # Calculate variance between group means
    all_means = []
    total_variance = 0
    
    for group_name, group_stats in stats.items():
        for layer in layers:
            if layer in group_stats:
                all_means.append(group_stats[layer]['mean'])
                total_variance += group_stats[layer]['variance']
    
    if not all_means:
        return float('inf')
    
    # Calculate variance between group means
    mean_variance = np.var(all_means)
    
    # Combined score: between-group variance + within-group variance
    # We can adjust weights if needed
    combined_score = mean_variance + total_variance
    
    return combined_score


def optimal_grouping(data, group_count, layers, group_sizes=None, num_attempts=10):
    """
    Perform multiple random grouping attempts and return the best result.
    
    Args:
        data: CSV string data with header
        group_count: Number of groups to divide into
        layers: List of column names to use for layering
        group_sizes: List of integers specifying the size of each group
        num_attempts: Number of random grouping attempts
    
    Returns:
        The best grouping result
    """
    best_result = None
    best_score = float('inf')
    
    for attempt in range(num_attempts):
        try:
            # Perform random grouping with different seed
            result = layered_random_grouping(data, group_count, layers, group_sizes)
            
            # Evaluate the quality of this grouping
            score = evaluate_group_quality(result, layers)
            
            # Keep the best result
            if score < best_score:
                best_score = score
                best_result = result
                
        except Exception as e:
            print(f"Error in grouping attempt {attempt + 1}: {e}")
            continue
    
    return best_result


@app.route('/api/group', methods=['POST'])
def group_data():
    """
    API endpoint to perform optimized layered random grouping.

    Expects JSON data with:
    - data: CSV string data with header
    - group_count: Number of groups to divide into
    - layers: List of column names to use for layering
    - group_sizes: List of integers specifying the size of each group

    Returns:
        JSON response with grouped data and ID
    """
    try:
        req_data = request.get_json()

        data = req_data.get('data', '')
        group_count = req_data.get('group_count', 3)
        layers = req_data.get('layers', [])
        group_sizes = req_data.get('group_sizes', None)  # Optional: specific sizes for each group

        # Validate input parameters
        if not data:
            return jsonify({'error': 'CSV data is required'}), 400

        # Support both list and string input for layers
        if isinstance(layers, str):
            # Split by both Chinese and English commas
            layers = [l.strip() for l in re.split(r'[，,]', layers) if l.strip()]
        
        if not isinstance(layers, list) or len(layers) == 0:
            return jsonify({'error': 'Layers must be specified'}), 400

        if not isinstance(group_count, int) or group_count <= 0:
            return jsonify({'error': 'group_count must be a positive integer'}), 400

        # Perform optimized grouping with 10 attempts
        grouped_result = optimal_grouping(data, group_count, layers, group_sizes, num_attempts=10)

        # Generate a random ID for this grouping result
        result_id = ''.join(random.choices('0123456789ABCDEF', k=6))

        # Store the result in the database
        try:
            # Convert layers to string for storage
            layers_str = ','.join(layers) if isinstance(layers, list) else layers
            store_result_in_db(result_id, grouped_result, group_count, layers_str)
        except Exception as e:
            print(f"Error storing result: {e}")
            # Continue without storing

        # Return the grouped result with the ID
        response = {
            'id': result_id,
            'result': grouped_result
        }

        return jsonify(response)

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


def store_result_in_db(result_id, grouped_result, group_count, layers):
    """Store the grouping result in the database"""
    print(f"DEBUG: store_result_in_db called with types: result_id={type(result_id)}, group_count={type(group_count)}, layers={type(layers)}")
    
    data_json = fast_json_dumps(grouped_result)
    
    # Ensure layers is a string, not a list
    if isinstance(layers, list):
        print(f"DEBUG: Converting layers from list to string: {layers}")
        layers = ','.join(layers)
        print(f"DEBUG: Converted layers to string: {layers}")
    
    # Ensure group_count is an integer
    if not isinstance(group_count, int):
        print(f"DEBUG: Converting group_count to int: {group_count}")
        group_count = int(group_count)
        print(f"DEBUG: Converted group_count to int: {group_count}")
    
    # Ensure result_id is a string
    if not isinstance(result_id, str):
        print(f"DEBUG: Converting result_id to string: {result_id}")
        result_id = str(result_id)
        print(f"DEBUG: Converted result_id to string: {result_id}")
    
    print(f"DEBUG: Final types before DB insert: result_id={type(result_id)}({result_id}), group_count={type(group_count)}({group_count}), layers={type(layers)}({layers})")
    
    insert_sql = """
    INSERT INTO group_results (id, data, group_count, layers, timestamp)
    VALUES (:id, :data, :group_count, :layers, :timestamp)
    """

    with engine.connect() as conn:
        conn.execute(text(insert_sql), {
            'id': result_id,
            'data': data_json,
            'group_count': group_count,
            'layers': layers,
            'timestamp': datetime.now()
        })
        conn.commit()


@app.route('/api/save-results', methods=['POST'])
def save_results():
    """
    API endpoint to save grouping results to the Docker specified directory.
    
    Expects JSON data with:
    - csv_content: CSV string content to save
    - result_id: Unique identifier for the grouping result
    
    Returns:
        JSON response with status and filename
    """
    try:
        req_data = request.get_json()
        csv_content = req_data.get('csv_content', '')
        result_id = req_data.get('result_id', '')
        
        if not csv_content:
            return jsonify({'error': 'CSV content is required'}), 400
        
        if not result_id:
            return jsonify({'error': 'Result ID is required'}), 400
        
        # 确定目录 - 统一使用data/results目录
        group_dir = '/data/results'
        os.makedirs(group_dir, exist_ok=True)
        
        # Generate filename with date-time and unique ID
        now = datetime.now()
        date_time_str = now.strftime('%Y%m%d-%H%M%S')
        filename = f"grouping_result_{date_time_str}_{result_id}.csv"
        filepath = os.path.join(group_dir, filename)
        
        # Write the CSV content to file (with BOM for proper UTF-8 handling)
        with open(filepath, 'w', encoding='utf-8-sig') as f:
            f.write(csv_content)
        
        return jsonify({
            'status': 'success',
            'filename': filename,
            'filepath': filepath
        })
        
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


def get_result_from_db(result_id):
    """Retrieve grouping result from database by ID"""
    try:
        with engine.connect() as conn:
            query = text("SELECT data, group_count, layers FROM group_results WHERE id = :id")
            result = conn.execute(query, {'id': result_id}).fetchone()
            
            if not result:
                return None
                
            return {
                'data': fast_json_loads(result[0]),
                'group_count': int(result[1]),
                'layers': result[2]  # Keep as string
            }
    except Exception as e:
        print(f"Error retrieving result from database: {e}")
        return None


def calculate_group_statistics(groups, layers):
    """Calculate mean and variance for each group and layer"""
    stats = {}
    
    for group_name, group_data in groups.items():
        stats[group_name] = {}
        
        for layer in layers:
            # Extract values for this layer
            values = []
            for item in group_data:
                if layer in item and item[layer] is not None:
                    try:
                        values.append(float(item[layer]))
                    except (ValueError, TypeError):
                        continue
            
            if values:
                mean = np.mean(values)
                variance = np.var(values)
                stats[group_name][layer] = {
                    'mean': mean,
                    'variance': variance
                }
    
    return stats


def calculate_overall_variance(stats, layers):
    """Calculate overall variance across all groups and layers"""
    all_means = []
    
    for group_name, group_stats in stats.items():
        for layer in layers:
            if layer in group_stats:
                all_means.append(group_stats[layer]['mean'])
    
    if all_means:
        return np.var(all_means)
    return float('inf')


def extract_and_redistribute(groups, extract_count, group_count, random_seed=None):
    """Extract animals from each group and redistribute them"""
    if random_seed is not None:
        random.seed(random_seed)
    
    # Extract animals from each group
    extracted_animals = []
    remaining_groups = {f"group_{i+1}": [] for i in range(group_count)}
    
    for group_name, group_data in groups.items():
        group_animals = list(group_data)  # Make a copy
        
        # Randomly extract animals
        random.shuffle(group_animals)
        
        # Extract the specified number of animals
        extracted = group_animals[:extract_count]
        remaining = group_animals[extract_count:]
        
        extracted_animals.extend(extracted)
        remaining_groups[group_name] = remaining
    
    # Shuffle extracted animals
    random.shuffle(extracted_animals)
    
    # Redistribute extracted animals back to groups
    result_groups = {f"group_{i+1}": [] for i in range(group_count)}
    
    # First, add remaining animals back to their original groups
    for group_name in remaining_groups:
        result_groups[group_name] = remaining_groups[group_name].copy()
    
    # Then, redistribute extracted animals evenly
    for i, animal in enumerate(extracted_animals):
        target_group = f"group_{(i % group_count) + 1}"
        result_groups[target_group].append(animal)
    
    return result_groups


def fine_tune_grouping(result_id, simulations_count, min_extract_count, max_extract_count):
    """Perform fine-tuning of grouping with multiple extraction counts"""
    # Get original grouping result
    original_data = get_result_from_db(result_id)
    if not original_data:
        raise ValueError(f"Result with ID {result_id} not found")
    
    original_groups = original_data['data']
    group_count = original_data['group_count']
    original_layers = original_data['layers']  # Keep original for storage
    print(f"DEBUG: original_layers type: {type(original_layers)}, value: {original_layers}")
    layers = re.split(r'[，,]', original_layers) if isinstance(original_layers, str) else original_layers
    layers = [l.strip() for l in layers if l.strip()]  # Remove empty strings and whitespace
    print(f"DEBUG: layers type: {type(layers)}, value: {layers}")
    
    # Calculate original statistics
    original_stats = calculate_group_statistics(original_groups, layers)
    original_variance = calculate_overall_variance(original_stats, layers)
    
    # Store results for each extraction count
    trend_data = []
    best_result = None
    best_variance = original_variance
    
    # Test different extraction counts
    for extract_count in range(min_extract_count, max_extract_count + 1):
        best_sim_result = None
        best_sim_variance = float('inf')
        
        # Run simulations for this extraction count
        for sim in range(simulations_count):
            # Extract and redistribute
            sim_groups = extract_and_redistribute(
                original_groups, extract_count, group_count, random_seed=sim
            )
            
            # Calculate statistics
            sim_stats = calculate_group_statistics(sim_groups, layers)
            sim_variance = calculate_overall_variance(sim_stats, layers)
            
            # Keep the best result for this extraction count
            if sim_variance < best_sim_variance:
                best_sim_variance = sim_variance
                best_sim_result = sim_groups
        
        # Store trend data
        trend_data.append({
            'extract_count': extract_count,
            'mean_variance': best_sim_variance,
            'improvement': original_variance - best_sim_variance
        })
        
        # Keep the best overall result
        if best_sim_variance < best_variance:
            best_variance = best_sim_variance
            best_result = best_sim_result
    
    return {
        'result': best_result,
        'trend_data': trend_data,
        'original_variance': original_variance,
        'final_variance': best_variance,
        'improvement': original_variance - best_variance
    }


@app.route('/api/fine-tune', methods=['POST'])
def fine_tune():
    """
    API endpoint to perform fine-tuning of existing grouping results.
    
    Expects JSON data with:
    - result_id: ID of the original grouping result
    - simulations_count: Number of simulations to run for each extraction count
    - min_extract_count: Minimum number of animals to extract from each group
    - max_extract_count: Maximum number of animals to extract from each group
    
    Returns:
        JSON response with fine-tuned grouping result and trend data
    """
    try:
        req_data = request.get_json()
        
        result_id = req_data.get('result_id', '')
        simulations_count = req_data.get('simulations_count', 100)
        min_extract_count = req_data.get('min_extract_count', 1)
        max_extract_count = req_data.get('max_extract_count', 5)
        
        # Validate input parameters
        if not result_id:
            return jsonify({'error': 'Result ID is required'}), 400
        
        if not isinstance(simulations_count, int) or simulations_count < 10:
            return jsonify({'error': 'simulations_count must be an integer >= 10'}), 400
        
        if not isinstance(min_extract_count, int) or min_extract_count < 1:
            return jsonify({'error': 'min_extract_count must be an integer >= 1'}), 400
        
        if not isinstance(max_extract_count, int) or max_extract_count < min_extract_count:
            return jsonify({'error': 'max_extract_count must be >= min_extract_count'}), 400
        
        # Perform fine-tuning
        fine_tune_result = fine_tune_grouping(
            result_id, simulations_count, min_extract_count, max_extract_count
        )
        
        # Generate a random ID for this fine-tune result
        tune_result_id = ''.join(random.choices('0123456789ABCDEF', k=6))
        
        # Store the result in the database
        original_data = get_result_from_db(result_id)
        if original_data:
            try:
                # Use the original layers string from database
                print(f"DEBUG: About to store fine-tune result with layers type: {type(original_data['layers'])}, value: {original_data['layers']}")
                store_result_in_db(
                    tune_result_id, 
                    fine_tune_result['result'], 
                    original_data['group_count'], 
                    original_data['layers']
                )
                print(f"DEBUG: Successfully stored fine-tune result")
            except Exception as e:
                print(f"Error storing fine-tune result: {e}")
                # Continue without storing
        
        # Return the fine-tuned result with the ID
        response = {
            'id': tune_result_id,
            'result': fine_tune_result['result'],
            'trend_data': fine_tune_result['trend_data'],
            'statistics': {
                'original_variance': fine_tune_result['original_variance'],
                'final_variance': fine_tune_result['final_variance'],
                'improvement': fine_tune_result['improvement']
            }
        }
        
        return jsonify(response)
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


@app.route('/api/test-db', methods=['GET'])
def test_db():
    """Test database storage functionality"""
    try:
        test_id = 'TEST123'
        test_data = {'test': 'data'}
        test_group_count = 2
        test_layers = '体重'
        
        print(f"DEBUG: About to call store_result_in_db with layers type: {type(test_layers)}, value: {test_layers}")
        store_result_in_db(test_id, test_data, test_group_count, test_layers)
        print(f"DEBUG: Successfully called store_result_in_db")
        
        return jsonify({'status': 'success', 'message': 'Database storage test successful'})
    except Exception as e:
        print(f"DEBUG: Error in test_db: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


def advanced_fine_tuning_algorithm(data, layers, simulation_count, sample_size, iteration_count):
    """
    高级分组微调算法
    
    Args:
        data: CSV字符串数据
        layers: 分层参数列表
        simulation_count: 每次迭代的随机模拟次数 (N)
        sample_size: 初始抽样数量 (M)
        iteration_count: 迭代次数 (a)
    
    Returns:
        包含所有迭代结果和最佳结果的字典
    """
    # 读取数据
    df = pd.read_csv(pd.io.common.StringIO(data))
    
    # 首先进行初始分组
    group_count = 3  # 默认分为3组
    initial_grouping = layered_random_grouping(data, group_count, layers)
    
    # 存储所有迭代的结果
    all_results = []
    best_overall_result = None
    best_overall_variance = float('inf')
    best_sample_size = sample_size
    
    # 从M到M+a进行迭代
    for i in range(iteration_count + 1):
        current_sample_size = sample_size + i
        best_iteration_result = None
        best_iteration_variance = float('inf')
        
        # 进行N次随机模拟
        for j in range(simulation_count):
            # 从每组抽出current_sample_size只动物
            extracted_animals = []
            remaining_groups = {f"group_{k+1}": [] for k in range(group_count)}
            
            # 从每组抽取动物
            for group_name, group_data in initial_grouping.items():
                group_animals = list(group_data)
                random.shuffle(group_animals)
                
                # 抽取指定数量的动物
                extract_count = min(current_sample_size, len(group_animals))
                extracted = group_animals[:extract_count]
                remaining = group_animals[extract_count:]
                
                extracted_animals.extend(extracted)
                remaining_groups[group_name] = remaining
            
            # 随机重分配抽出的动物
            random.shuffle(extracted_animals)
            
            # 创建新的分组
            new_groups = {f"group_{k+1}": [] for k in range(group_count)}
            
            # 首先将剩余动物放回原组
            for group_name in remaining_groups:
                new_groups[group_name] = remaining_groups[group_name].copy()
            
            # 然后将抽出的动物均匀分配到各组
            for k, animal in enumerate(extracted_animals):
                target_group = f"group_{(k % group_count) + 1}"
                new_groups[target_group].append(animal)
            
            # 计算当前分组的统计信息
            stats = calculate_group_statistics(new_groups, layers)
            variance_of_means = calculate_overall_variance(stats, layers)
            
            # 保留本次迭代中的最佳结果
            if variance_of_means < best_iteration_variance:
                best_iteration_variance = variance_of_means
                best_iteration_result = {
                    'groups': new_groups,
                    'stats': stats,
                    'variance_of_means': variance_of_means
                }
        
        # 保存当前迭代的结果
        if best_iteration_result:
            group_means = []
            group_variances = []
            
            for layer in layers:
                layer_means = []
                layer_variances = []
                
                for group_name, group_stats in best_iteration_result['stats'].items():
                    if layer in group_stats:
                        layer_means.append(group_stats[layer]['mean'])
                        layer_variances.append(group_stats[layer]['variance'])
                
                group_means.append(layer_means)
                group_variances.append(layer_variances)
            
            # 计算所有层的平均均值和方差
            avg_means = [np.mean(means) for means in zip(*group_means)] if group_means else []
            avg_variances = [np.mean(variances) for variances in zip(*group_variances)] if group_variances else []
            
            iteration_result = {
                'sample_size': current_sample_size,
                'group_means': avg_means,
                'group_variances': avg_variances,
                'variance_of_means': best_iteration_variance,
                'groups': best_iteration_result['groups']
            }
            
            all_results.append(iteration_result)
            
            # 更新全局最佳结果
            if best_iteration_variance < best_overall_variance:
                best_overall_variance = best_iteration_variance
                best_overall_result = iteration_result
                best_sample_size = current_sample_size
    
    # 计算改进幅度
    initial_variance = all_results[0]['variance_of_means'] if all_results else float('inf')
    improvement = initial_variance - best_overall_variance
    
    return {
        'trend_data': all_results,
        'best_result': best_overall_result,
        'statistics': {
            'best_sample_size': best_sample_size,
            'min_variance': best_overall_variance,
            'improvement': improvement
        }
    }


@app.route('/api/advanced-fine-tuning', methods=['POST'])
def api_advanced_fine_tuning():
    """
    高级分组微调API端点
    
    请求体:
    {
        "data": "CSV格式的字符串数据",
        "layers": ["体重", "摄食量"],
        "simulation_count": 100,
        "sample_size": 1,
        "iteration_count": 5
    }
    """
    try:
        req_data = request.get_json()
        
        csv_data = req_data.get('data', '')
        layers = req_data.get('layers', [])
        simulation_count = req_data.get('simulation_count', 100)
        sample_size = req_data.get('sample_size', 1)
        iteration_count = req_data.get('iteration_count', 5)
        
        # 验证输入参数
        if not csv_data:
            return jsonify({'error': 'CSV数据是必需的'}), 400
        
        # Support both list and string input for layers
        if isinstance(layers, str):
            # Split by both Chinese and English commas
            layers = [l.strip() for l in re.split(r'[，,]', layers) if l.strip()]
        
        if not isinstance(layers, list) or len(layers) == 0:
            return jsonify({'error': '必须指定至少一个分层参数'}), 400
        
        if not isinstance(simulation_count, int) or simulation_count < 10:
            return jsonify({'error': '随机模拟次数必须是大于等于10的整数'}), 400
        
        if not isinstance(sample_size, int) or sample_size < 1:
            return jsonify({'error': '每组抽样数量必须是大于等于1的整数'}), 400
        
        if not isinstance(iteration_count, int) or iteration_count < 1:
            return jsonify({'error': '迭代次数必须是大于等于1的整数'}), 400
        
        # 执行高级分组微调算法
        result = advanced_fine_tuning_algorithm(
            csv_data, layers, simulation_count, sample_size, iteration_count
        )
        
        # 生成结果ID并存储到数据库
        result_id = ''.join(random.choices('0123456789ABCDEF', k=6))
        
        try:
            # 存储最佳分组结果
            if result['best_result'] and result['best_result']['groups']:
                layers_str = ','.join(layers) if isinstance(layers, list) else layers
                store_result_in_db(
                    result_id, 
                    result['best_result']['groups'], 
                    len(result['best_result']['groups']), 
                    layers_str
                )
        except Exception as e:
            print(f"存储高级微调结果时出错: {e}")
            # 继续执行，不因存储错误而中断
        
        # 返回结果
        response = {
            'id': result_id,
            'trend_data': result['trend_data'],
            'statistics': result['statistics']
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': f'执行高级微调时出错: {str(e)}'}), 500


@app.route('/')
def index():
    """Serve the main page of the web application"""
    return render_template('index.html')


@app.route('/scientific-grouping')
def scientific_grouping():
    """Serve the scientific grouping page"""
    return render_template('scientific_grouping.html')


@app.route('/fine-tuning')
def fine_tuning():
    """Serve the fine tuning page"""
    return render_template('fine_tuning.html')


def get_safe_table_name(experiment_name):
    """生成安全的表名，保留中文字符"""
    import re
    # 只替换可能导致SQL问题的特殊字符，保留中文字符、字母、数字和下划线
    safe_name = re.sub(r'[^\w\u4e00-\u9fff]', '_', experiment_name)
    return f"experiment_data_{safe_name}"


def create_experiment_data_table(experiment_name):
    """为特定实验创建数据记录表"""
    table_name = get_safe_table_name(experiment_name)
    
    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE NOT NULL,
        group_name VARCHAR(50) NOT NULL,
        animal_id VARCHAR(50) NOT NULL,
        parameter_name VARCHAR(50) NOT NULL,
        parameter_value TEXT NOT NULL,
        recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # 创建索引以优化查询性能
    create_date_index_sql = f"""
    CREATE INDEX IF NOT EXISTS idx_{table_name}_date ON {table_name}(date);
    """
    
    create_group_index_sql = f"""
    CREATE INDEX IF NOT EXISTS idx_{table_name}_group ON {table_name}(group_name);
    """
    
    create_param_index_sql = f"""
    CREATE INDEX IF NOT EXISTS idx_{table_name}_param ON {table_name}(parameter_name);
    """
    
    create_composite_index_sql = f"""
    CREATE INDEX IF NOT EXISTS idx_{table_name}_date_group_param 
    ON {table_name}(date, group_name, parameter_name);
    """
    
    with engine.connect() as conn:
        conn.execute(text(create_table_sql))
        conn.execute(text(create_date_index_sql))
        conn.execute(text(create_group_index_sql))
        conn.execute(text(create_param_index_sql))
        conn.execute(text(create_composite_index_sql))
        conn.commit()
    
    return table_name


@app.route('/api/experiments', methods=['GET'])
def get_experiments():
    """获取所有实验名称"""
    try:
        with engine.connect() as conn:
            query = text("SELECT name FROM experiments ORDER BY created_at DESC")
            results = conn.execute(query).fetchall()
            experiments = [row[0] for row in results]
            return jsonify({'experiments': experiments})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/experiments', methods=['POST'])
def create_experiment():
    """创建新实验或更新已有实验"""
    try:
        req_data = request.get_json()
        experiment_name = req_data.get('experiment_name', '')
        parameters = req_data.get('parameters', '')
        group_count = req_data.get('group_count', 0)
        group_type = req_data.get('group_type', 'average')
        group_info = req_data.get('group_info', [])
        
        if not experiment_name:
            return jsonify({'error': '实验名称不能为空'}), 400
        
        if not parameters:
            return jsonify({'error': '参数名称不能为空'}), 400
        
        if group_count <= 0:
            return jsonify({'error': '组数必须大于0'}), 400
        
        # 验证组信息
        if len(group_info) != group_count:
            return jsonify({'error': '组信息数量与组数不匹配'}), 400
        
        # 检查实验是否已存在
        with engine.connect() as conn:
            check_sql = "SELECT COUNT(*) FROM experiments WHERE name = :name"
            result = conn.execute(text(check_sql), {'name': experiment_name}).fetchone()
            exists = result[0] > 0
            
            if exists:
                # 更新已有实验
                update_sql = """
                UPDATE experiments 
                SET parameters = :parameters, 
                    group_count = :group_count, 
                    group_type = :group_type, 
                    group_info = :group_info
                WHERE name = :name
                """
                conn.execute(text(update_sql), {
                    'name': experiment_name,
                    'parameters': parameters,
                    'group_count': group_count,
                    'group_type': group_type,
                    'group_info': fast_json_dumps(group_info)
                })
                message = '实验更新成功'
            else:
                # 创建新实验
                insert_sql = """
                INSERT INTO experiments (name, parameters, group_count, group_type, group_info)
                VALUES (:name, :parameters, :group_count, :group_type, :group_info)
                """
                conn.execute(text(insert_sql), {
                    'name': experiment_name,
                    'parameters': parameters,
                    'group_count': group_count,
                    'group_type': group_type,
                    'group_info': fast_json_dumps(group_info)
                })
                message = '实验创建成功'
            
            conn.commit()
        
        # 清除缓存
        clear_experiment_cache(experiment_name)
        
        # 创建实验数据表（如果不存在）
        create_experiment_data_table(experiment_name)
        
        return jsonify({'status': 'success', 'message': message})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/experiments/<experiment_name>', methods=['GET'])
def get_experiment_info(experiment_name):
    """获取特定实验的信息（带缓存）"""
    try:
        # 检查缓存
        if experiment_name in experiment_cache:
            return jsonify(experiment_cache[experiment_name])
        
        # 缓存未命中，查询数据库
        with engine.connect() as conn:
            query = text("""
            SELECT parameters, group_count, group_type, group_info 
            FROM experiments WHERE name = :name
            """)
            result = conn.execute(query, {'name': experiment_name}).fetchone()
            
            if not result:
                return jsonify({'error': '实验不存在'}), 404
            
            # 构建结果并缓存
            exp_info = {
                'parameters': result[0],
                'group_count': result[1],
                'group_type': result[2],
                'group_info': fast_json_loads(result[3])
            }
            experiment_cache[experiment_name] = exp_info
            
            return jsonify(exp_info)
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/experiment-data', methods=['POST'])
def save_experiment_data():
    """保存实验数据（支持覆盖）"""
    try:
        req_data = request.get_json()
        experiment_name = req_data.get('experiment_name', '')
        date = req_data.get('date', '')
        data = req_data.get('data', [])
        
        if not experiment_name or not date or not data:
            return jsonify({'error': '实验名称、日期和数据不能为空'}), 400
        
        # 获取实验信息
        experiment_info = get_experiment_info(experiment_name)
        if experiment_info.status_code != 200:
            return experiment_info
        
        exp_data = experiment_info.get_json()
        parameters = exp_data['parameters'].split(',')
        
        # 创建数据表
        table_name = create_experiment_data_table(experiment_name)
        
        # 保存数据（使用UPSERT方式）
        with engine.connect() as conn:
            for item in data:
                animal_id = item.get('animal_id', '')
                group_name = item.get('group_name', '')
                
                for param in parameters:
                    param_name = param.strip()
                    param_value = item.get(param_name, 0)
                    
                    # 使用REPLACE语句实现UPSERT
                    upsert_sql = f"""
                    INSERT OR REPLACE INTO {table_name} 
                    (date, group_name, animal_id, parameter_name, parameter_value)
                    VALUES (:date, :group_name, :animal_id, :parameter_name, :parameter_value)
                    """
                    conn.execute(text(upsert_sql), {
                        'date': date,
                        'group_name': group_name,
                        'animal_id': animal_id,
                        'parameter_name': param_name,
                        'parameter_value': param_value
                    })
            
            conn.commit()
        
        # 生成CSV备份文件
        csv_data = generate_experiment_csv(experiment_name, date, data, parameters)
        save_csv_backup(experiment_name, date, csv_data)
        
        # 自动生成图表（新数据，强制生成）
        try:
            generate_experiment_charts(experiment_name)
        except Exception as chart_error:
            print(f"图表生成失败: {chart_error}")
        
        return jsonify({'status': 'success', 'message': '数据保存成功'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/experiment-data/overwrite', methods=['POST'])
def overwrite_experiment_data():
    """强制覆写实验数据"""
    try:
        req_data = request.get_json()
        experiment_name = req_data.get('experiment_name', '')
        date = req_data.get('date', '')
        data = req_data.get('data', [])
        
        if not experiment_name or not date or not data:
            return jsonify({'error': '实验名称、日期和数据不能为空'}), 400
        
        # 获取实验信息
        experiment_info = get_experiment_info(experiment_name)
        if experiment_info.status_code != 200:
            return experiment_info
        
        exp_data = experiment_info.get_json()
        parameters = exp_data['parameters'].split(',')
        
        # 创建数据表
        table_name = create_experiment_data_table(experiment_name)
        
        # 删除该日期的旧数据
        with engine.connect() as conn:
            delete_sql = f"""
            DELETE FROM {table_name} WHERE date = :date
            """
            conn.execute(text(delete_sql), {'date': date})
            conn.commit()
        
        # 保存新数据
        with engine.connect() as conn:
            for item in data:
                animal_id = item.get('animal_id', '')
                group_name = item.get('group_name', '')
                
                for param in parameters:
                    param_name = param.strip()
                    param_value = item.get(param_name, 0)
                    
                    insert_sql = f"""
                    INSERT INTO {table_name} (date, group_name, animal_id, parameter_name, parameter_value)
                    VALUES (:date, :group_name, :animal_id, :parameter_name, :parameter_value)
                    """
                    conn.execute(text(insert_sql), {
                        'date': date,
                        'group_name': group_name,
                        'animal_id': animal_id,
                        'parameter_name': param_name,
                        'parameter_value': param_value
                    })
            
            conn.commit()
        
        # 生成CSV备份文件(覆写)
        csv_data = generate_experiment_csv(experiment_name, date, data, parameters)
        save_csv_backup(experiment_name, date, csv_data)
        
        # 自动生成图表（数据已修改，强制重新生成）
        try:
            generate_experiment_charts(experiment_name)
        except Exception as chart_error:
            print(f"图表生成失败: {chart_error}")
        
        return jsonify({'status': 'success', 'message': '数据覆写成功'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def generate_experiment_csv(experiment_name, date, data, parameters):
    """生成实验数据的CSV格式"""
    import io
    import csv
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 写入表头
    header = ['日期', '组别名称', '动物编号'] + parameters
    writer.writerow(header)
    
    # 写入数据
    for item in data:
        row = [
            date,
            item.get('group_name', ''),
            item.get('animal_id', '')
        ]
        
        for param in parameters:
            row.append(item.get(param.strip(), ''))
        
        writer.writerow(row)
    
    return output.getvalue()


def save_csv_backup(experiment_name, date, csv_data):
    """保存CSV备份文件"""
    try:
        # 确定目录 - 统一使用data/results目录
        backup_dir = '/data/results'
        
        os.makedirs(backup_dir, exist_ok=True)
        
        # 生成文件名
        filename = f"{experiment_name}_{date}.csv"
        filepath = os.path.join(backup_dir, filename)
        
        # 保存文件
        with open(filepath, 'w', encoding='utf-8-sig') as f:
            f.write(csv_data)
            
        return filepath
        
    except Exception as e:
        print(f"保存CSV备份文件时出错: {e}")
        return None


@app.route('/api/experiment-data/<experiment_name>', methods=['GET'])
def get_experiment_data(experiment_name):
    """获取实验数据用于可视化"""
    try:
        # 获取实验信息
        experiment_info = get_experiment_info(experiment_name)
        if experiment_info.status_code != 200:
            return experiment_info
        
        exp_data = experiment_info.get_json()
        parameters = exp_data['parameters'].split(',')
        
        # 构建表名
        table_name = get_safe_table_name(experiment_name)
        
        # 查询数据，只选择数值类型的参数
        with engine.connect() as conn:
            query = text(f"""
            SELECT date, group_name, parameter_name, parameter_value
            FROM {table_name}
            ORDER BY date, group_name, parameter_name
            """)
            results = conn.execute(query).fetchall()
        
        # 组织数据，只处理数值类型的参数
        data = {}
        numeric_params = set()
        
        for row in results:
            date_str = row[0]
            group_name = row[1]
            param_name = row[2]
            param_value = row[3]
            
            # 尝试将值转换为数字
            try:
                numeric_value = float(param_value)
                numeric_params.add(param_name)
                
                if param_name not in data:
                    data[param_name] = {}
                
                if group_name not in data[param_name]:
                    data[param_name][group_name] = {}
                
                if date_str not in data[param_name][group_name]:
                    data[param_name][group_name][date_str] = []
                
                data[param_name][group_name][date_str].append(numeric_value)
            except (ValueError, TypeError):
                # 非数值类型，跳过
                continue
        
        # 计算每个日期的平均值
        chart_data = {}
        for param_name in data:
            chart_data[param_name] = {}
            for group_name in data[param_name]:
                dates = sorted(data[param_name][group_name].keys())
                values = [np.mean(data[param_name][group_name][date]) for date in dates]
                
                chart_data[param_name][group_name] = {
                    'dates': dates,
                    'values': values
                }
        
        return jsonify({'data': chart_data, 'parameters': [p.strip() for p in parameters if p.strip() in numeric_params]})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/experiment-data/realtime', methods=['POST'])
def save_experiment_data_realtime():
    """实时保存单个数据项"""
    try:
        req_data = request.get_json()
        experiment_name = req_data.get('experiment_name', '')
        date = req_data.get('date', '')
        animal_id = req_data.get('animal_id', '')
        group_name = req_data.get('group_name', '')
        parameter_name = req_data.get('parameter_name', '')
        parameter_value = req_data.get('parameter_value', '')
        
        if not experiment_name or not date or not animal_id or not group_name or not parameter_name:
            return jsonify({'error': '实验名称、日期、动物编号、组别名称和参数名称不能为空'}), 400
        
        # 检查数据是否已锁定
        with engine.connect() as conn:
            check_lock_sql = """
            SELECT is_locked FROM experiment_data_locks 
            WHERE experiment_name = :experiment_name AND date = :date
            """
            result = conn.execute(text(check_lock_sql), {
                'experiment_name': experiment_name,
                'date': date
            }).fetchone()
            
            if result and result[0]:
                return jsonify({'error': '数据已锁定，无法修改'}), 403
        
        # 获取实验信息
        experiment_info = get_experiment_info(experiment_name)
        if experiment_info.status_code != 200:
            return experiment_info
        
        # 创建数据表
        table_name = create_experiment_data_table(experiment_name)
        
        # 使用UPSERT操作（先删除再插入）
        with engine.connect() as conn:
            # 删除已存在的记录
            delete_sql = f"""
            DELETE FROM {table_name} 
            WHERE date = :date AND animal_id = :animal_id AND parameter_name = :parameter_name
            """
            conn.execute(text(delete_sql), {
                'date': date,
                'animal_id': animal_id,
                'parameter_name': parameter_name
            })
            
            # 插入新记录
            insert_sql = f"""
            INSERT INTO {table_name} (date, group_name, animal_id, parameter_name, parameter_value)
            VALUES (:date, :group_name, :animal_id, :parameter_name, :parameter_value)
            """
            conn.execute(text(insert_sql), {
                'date': date,
                'group_name': group_name,
                'animal_id': animal_id,
                'parameter_name': parameter_name,
                'parameter_value': parameter_value
            })
            
            conn.commit()
        
        return jsonify({'status': 'success', 'message': '数据保存成功'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/experiment-data/lock', methods=['POST'])
def lock_experiment_data():
    """锁定实验数据"""
    try:
        req_data = request.get_json()
        experiment_name = req_data.get('experiment_name', '')
        date = req_data.get('date', '')
        locked_by = req_data.get('locked_by', 'user')
        
        if not experiment_name or not date:
            return jsonify({'error': '实验名称和日期不能为空'}), 400
        
        with engine.connect() as conn:
            # 检查是否有数据
            table_name = get_safe_table_name(experiment_name)
            check_data_sql = f"""
            SELECT COUNT(*) FROM {table_name} WHERE date = :date
            """
            result = conn.execute(text(check_data_sql), {'date': date}).fetchone()
            
            if result[0] == 0:
                return jsonify({'error': '没有数据可以锁定'}), 400
            
            # 锁定数据
            upsert_lock_sql = """
            INSERT OR REPLACE INTO experiment_data_locks 
            (experiment_name, date, is_locked, locked_at, locked_by)
            VALUES (:experiment_name, :date, 1, :locked_at, :locked_by)
            """
            conn.execute(text(upsert_lock_sql), {
                'experiment_name': experiment_name,
                'date': date,
                'locked_at': datetime.now(),
                'locked_by': locked_by
            })
            
            conn.commit()
        
        # 生成CSV备份文件
        try:
            # 获取实验信息和数据
            experiment_info = get_experiment_info(experiment_name)
            if experiment_info.status_code == 200:
                exp_data = experiment_info.get_json()
                parameters = exp_data['parameters'].split(',')
                
                # 获取该日期的所有数据
                with engine.connect() as conn:
                    query = text(f"""
                    SELECT group_name, animal_id, parameter_name, parameter_value
                    FROM {table_name}
                    WHERE date = :date
                    ORDER BY group_name, animal_id, parameter_name
                    """)
                    results = conn.execute(query, {'date': date}).fetchall()
                
                # 组织数据
                data_dict = {}
                for row in results:
                    animal_id = row[1]
                    param_name = row[2]
                    param_value = row[3]
                    
                    if animal_id not in data_dict:
                        data_dict[animal_id] = {
                            'group_name': row[0],
                            'animal_id': animal_id
                        }
                    
                    data_dict[animal_id][param_name] = param_value
                
                data_list = list(data_dict.values())
                
                # 生成CSV并保存
                csv_data = generate_experiment_csv(experiment_name, date, data_list, parameters)
                save_csv_backup(experiment_name, date, csv_data)
                
                # 自动生成图表
                generate_experiment_charts(experiment_name)
        except Exception as e:
            print(f"生成CSV备份或图表时出错: {e}")
        
        return jsonify({'status': 'success', 'message': '数据已锁定并导出'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/experiment-data/unlock', methods=['POST'])
def unlock_experiment_data():
    """解锁实验数据"""
    try:
        req_data = request.get_json()
        experiment_name = req_data.get('experiment_name', '')
        date = req_data.get('date', '')
        
        if not experiment_name or not date:
            return jsonify({'error': '实验名称和日期不能为空'}), 400
        
        with engine.connect() as conn:
            unlock_sql = """
            UPDATE experiment_data_locks 
            SET is_locked = 0, locked_at = NULL, locked_by = NULL
            WHERE experiment_name = :experiment_name AND date = :date
            """
            conn.execute(text(unlock_sql), {
                'experiment_name': experiment_name,
                'date': date
            })
            
            conn.commit()
        
        return jsonify({'status': 'success', 'message': '数据已解锁'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/experiment-data/lock-status', methods=['GET'])
def get_experiment_data_lock_status():
    """获取实验数据锁定状态"""
    try:
        experiment_name = request.args.get('experiment_name', '')
        date = request.args.get('date', '')
        
        if not experiment_name or not date:
            return jsonify({'error': '实验名称和日期不能为空'}), 400
        
        with engine.connect() as conn:
            query = text("""
            SELECT is_locked, locked_at, locked_by 
            FROM experiment_data_locks 
            WHERE experiment_name = :experiment_name AND date = :date
            """)
            result = conn.execute(query, {
                'experiment_name': experiment_name,
                'date': date
            }).fetchone()
            
            if result:
                return jsonify({
                    'is_locked': bool(result[0]),
                    'locked_at': result[1],
                    'locked_by': result[2]
                })
            else:
                return jsonify({'is_locked': False})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/experiment-data/<experiment_name>/<date>', methods=['GET'])
def get_experiment_data_by_date(experiment_name, date):
    """获取特定日期的实验数据"""
    try:
        # 获取实验信息
        experiment_info = get_experiment_info(experiment_name)
        if experiment_info.status_code != 200:
            return experiment_info
        
        exp_data = experiment_info.get_json()
        parameters = exp_data['parameters'].split(',')
        
        # 构建表名
        table_name = get_safe_table_name(experiment_name)
        
        # 查询特定日期的数据
        with engine.connect() as conn:
            query = text(f"""
            SELECT group_name, animal_id, parameter_name, parameter_value
            FROM {table_name}
            WHERE date = :date
            ORDER BY group_name, animal_id, parameter_name
            """)
            results = conn.execute(query, {'date': date}).fetchall()
        
        # 组织数据
        data_dict = {}
        for row in results:
            group_name = row[0]
            animal_id = row[1]
            param_name = row[2]
            param_value = row[3]
            
            key = f"{group_name}_{animal_id}"
            if key not in data_dict:
                data_dict[key] = {
                    'group_name': group_name,
                    'animal_id': animal_id
                }
            
            data_dict[key][param_name] = param_value
        
        # 转换为列表
        data_list = list(data_dict.values())
        
        return jsonify({
            'has_data': len(data_list) > 0,
            'data': data_list
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def calculate_data_hash(data):
    """计算数据的哈希值，用于判断数据是否变化"""
    # orjson默认会排序键，确保哈希一致性
    data_str = fast_json_dumps(data)
    return hashlib.sha256(data_str.encode()).hexdigest()


def generate_chart_svg(experiment_name, param_name, param_data, force_regenerate=False, display_format='原始数值', day_zero_date=None):
    """为单个参数生成SVG图表文件，返回文件路径
    
    Args:
        experiment_name: 实验名称
        param_name: 参数名称
        param_data: 参数数据字典
        force_regenerate: 是否强制重新生成
        display_format: 数据展示格式 ('原始数值', '比值', '百分比', '对数值')
        day_zero_date: Day 0日期（用于比值和百分比计算）
    """
    try:
        # 计算数据哈希值（包含展示格式和Day 0日期）
        hash_data = {
            'param_data': param_data,
            'display_format': display_format,
            'day_zero_date': day_zero_date
        }
        data_hash = calculate_data_hash(hash_data)
        
        # 确保data/images目录存在
        if os.environ.get('DOCKER_ENV') == 'true':
            # Docker环境：使用/data目录（挂载点）
            data_dir = '/data/images'
        else:
            # 本地环境：使用./data/images目录
            data_dir = os.path.join(os.path.dirname(__file__), 'data', 'images')
        os.makedirs(data_dir, exist_ok=True)
        
        # 生成规范化的文件名：实验名称-参数名称-实验日期.svg
        # 使用最新的数据日期作为文件名中的实验日期
        all_dates = set()
        for group_data in param_data.values():
            all_dates.update(group_data.keys())
        
        if all_dates:
            latest_date = max(all_dates)
            earliest_date = min(all_dates)
            date_range = f"{earliest_date}_to_{latest_date}"
        else:
            date_range = "no_data"
        
        # 根据展示格式调整文件名
        format_suffix = {
            '原始数值': 'raw',
            '比值': 'ratio',
            '百分比': 'percentage',
            '对数值': 'log10'
        }.get(display_format, 'raw')
        
        filename = f"{experiment_name}-{param_name}-{date_range}-{format_suffix}.svg"
        file_path = os.path.join(data_dir, filename)
        # 用于返回的相对路径
        relative_path = f"data/images/{filename}"
        
        # 调试日志
        print(f"DEBUG: generate_chart_svg - experiment_name={experiment_name}, param_name={param_name}, display_format={display_format}, format_suffix={format_suffix}, filename={filename}")
        try:
            with open('/data/debug.log', 'a', encoding='utf-8') as f:
                f.write(f"DEBUG: generate_chart_svg - experiment_name={experiment_name}, param_name={param_name}, display_format={display_format}, format_suffix={format_suffix}, filename={filename}\n")
        except:
            pass
        
        # 检查是否需要重新生成
        if not force_regenerate:
            with engine.connect() as conn:
                query = text("""
                SELECT file_path, data_hash FROM experiment_charts
                WHERE experiment_name = :exp_name AND parameter_name = :param_name AND display_format = :display_format
                """)
                result = conn.execute(query, {
                    'exp_name': experiment_name,
                    'param_name': param_name,
                    'display_format': display_format
                }).fetchone()
                
                if result and result[1] == data_hash:
                    # 数据未变化，检查文件是否存在（使用缓存）
                    file_path_cached = result[0]
                    if file_path_cached in file_exists_cache:
                        if file_exists_cache[file_path_cached]:
                            return file_path_cached
                    else:
                        exists = os.path.exists(file_path_cached)
                        file_exists_cache[file_path_cached] = exists
                        if exists:
                            return file_path_cached
        
        # 根据展示格式转换数据
        transformed_data = transform_data_for_display(param_data, display_format, day_zero_date)
        
        # 创建图表
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # 确保中文字体设置正确
        enable_zh_cn = os.environ.get('enable_zh_CN', 'TRUE').upper() == 'TRUE'
        if enable_zh_cn:
            # 重新设置中文字体，确保每个图表都使用正确的字体
            plt.rcParams['font.sans-serif'] = ['WenQuanYi Zen Hei', 'DejaVu Sans', 'sans-serif']
            plt.rcParams['axes.unicode_minus'] = False
        else:
            # 确保英文字体设置
            plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'sans-serif']
        
        # 收集所有转换后的数据用于计算Y轴范围
        all_values = []
        all_values_with_sd = []
        
        # 为每个组绘制折线和误差线
        for group_name in sorted(transformed_data.keys()):
            # 检查数据结构
            if 'dates' in transformed_data[group_name] and 'values' in transformed_data[group_name]:
                # 新的数据结构：{'dates': [...], 'values': [...]}
                dates = transformed_data[group_name]['dates']
                values = transformed_data[group_name]['values']
                
                # 对于新结构，每个值已经是平均值，没有标准差信息
                # 我们使用值本身作为平均值，标准差设为0
                means = values
                stds = [0] * len(values)
                
                all_values.extend(values)
                # 由于没有标准差信息，我们使用值本身作为±2SD的范围
                for val in values:
                    all_values_with_sd.append(val)
                    all_values_with_sd.append(val)
                
                # 绘制折线（没有误差线）
                ax.plot(dates, means, marker='o', label=group_name, 
                       linewidth=2, markersize=6, alpha=0.8)
            else:
                # 原始的数据结构：{date: [values], ...}
                dates = sorted(transformed_data[group_name].keys())
                means = []
                stds = []
                
                for date in dates:
                    values_at_date = transformed_data[group_name][date]
                    mean_val = np.mean(values_at_date)
                    std_val = np.std(values_at_date, ddof=1) if len(values_at_date) > 1 else 0
                    
                    means.append(mean_val)
                    stds.append(std_val)
                    all_values.extend(values_at_date)
                    all_values_with_sd.append(mean_val + 2 * std_val)
                    all_values_with_sd.append(mean_val - 2 * std_val)
                
                # 绘制折线和误差线
                ax.errorbar(dates, means, yerr=stds, marker='o', label=group_name, 
                           linewidth=2, markersize=6, capsize=5, capthick=1.5, alpha=0.8)
        
        # 智能计算Y轴范围
        # 优先使用all_values_with_sd，如果为空则使用all_values
        if all_values_with_sd:
            min_val = min(all_values_with_sd)
            max_val = max(all_values_with_sd)
        elif all_values:
            min_val = min(all_values)
            max_val = max(all_values)
        else:
            # 如果都没有数据，使用默认值
            min_val = 0
            max_val = 100
        
        # 根据展示格式调整Y轴范围
        y_min, y_max = calculate_y_axis_range(min_val, max_val, display_format)
        
        # 确保y_min和y_max不相等，并添加适当的边距
        if abs(y_min - y_max) < 0.001:  # 如果几乎相等
            y_min = y_min - 5
            y_max = y_max + 5
        
        ax.set_ylim(y_min, y_max)
        
        # 设置Y轴标签
        if display_format == '原始数值':
            ylabel = param_name
        elif display_format == '比值':
            ylabel = f"{param_name} (比值)"
        elif display_format == '百分比':
            ylabel = f"{param_name} (%)"
        elif display_format == '对数值':
            ylabel = f"log10({param_name})"
        else:
            ylabel = param_name
        
        ax.set_ylabel(ylabel, fontsize=12)
        
        # 设置图例：完全移除边框和背景
        legend = ax.legend(loc='best', fontsize=10, frameon=False, 
                          fancybox=False, shadow=False, framealpha=0)
        
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # 旋转x轴标签
        plt.xticks(rotation=45, ha='right')
        
        # 调整布局，增加边距确保完整显示
        plt.tight_layout(pad=2.0)
        
        # 保存为SVG文件，确保完整显示
        plt.savefig(file_path, format='svg', bbox_inches='tight', pad_inches=0.2)
        plt.close(fig)
        
        # 更新文件存在性缓存
        file_exists_cache[file_path] = True
        
        # 更新数据库记录
        with engine.connect() as conn:
            # 先删除旧记录（如果存在）
            delete_query = text("""
            DELETE FROM experiment_charts
            WHERE experiment_name = :exp_name AND parameter_name = :param_name AND display_format = :display_format
            """)
            conn.execute(delete_query, {
                'exp_name': experiment_name,
                'param_name': param_name,
                'display_format': display_format
            })
            
            # 插入新记录
            insert_query = text("""
            INSERT INTO experiment_charts (experiment_name, parameter_name, file_path, data_hash, updated_at, display_format, day_zero_date)
            VALUES (:exp_name, :param_name, :file_path, :data_hash, :updated_at, :display_format, :day_zero_date)
            """)
            conn.execute(insert_query, {
                'exp_name': experiment_name,
                'param_name': param_name,
                'file_path': file_path,
                'data_hash': data_hash,
                'updated_at': datetime.now(),
                'display_format': display_format,
                'day_zero_date': day_zero_date
            })
            conn.commit()
        
        # 在Docker环境中返回绝对路径，在本地环境中返回相对路径
        if os.environ.get('DOCKER_ENV') == 'true':
            return f"/{relative_path}"
        else:
            return relative_path
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise e


def calculate_percentage_axis_max(max_val):
    """
    计算百分比格式的Y轴最大值
    
    Args:
        max_val: 数据最大值（百分比数值，如36.34表示36.34%）
    
    Returns:
        float: Y轴最大值
    """
    if max_val >= 100:
        # max>=100，向上取50%的整数倍
        return np.ceil(max_val / 50) * 50
    else:
        # max<100，向上取5%的整数倍
        return np.ceil(max_val / 5) * 5


def calculate_ratio_axis_min(min_val):
    """
    计算比值格式的Y轴最小值
    
    Args:
        min_val: 数据最小值
    
    Returns:
        float: Y轴最小值
    """
    if min_val > 100000:
        # min>100000，向下取5000的整数倍
        return np.floor(min_val / 5000) * 5000
    elif min_val > 10000:
        # 10000<min<=100000，向下取1000的整数倍
        return np.floor(min_val / 1000) * 1000
    elif min_val > 1000:
        # 1000<min<=10000，向下取100的整数倍
        return np.floor(min_val / 100) * 100
    elif min_val > 100:
        # 100<min<=1000，向下取50的整数倍
        return np.floor(min_val / 50) * 50
    elif min_val > 20:
        # 20<min<=100，向下取5的整数倍
        return np.floor(min_val / 5) * 5
    elif min_val > 10:
        # 10<min<=20，向下取2.5的整数倍
        return np.floor(min_val / 2.5) * 2.5
    else:
        # max<=10，向下取0.5的整数倍
        return np.floor(min_val * 2) / 2


def calculate_ratio_axis_max(max_val):
    """
    计算比值格式的Y轴最大值
    
    Args:
        max_val: 数据最大值
    
    Returns:
        float: Y轴最大值
    """
    if max_val > 100000:
        # max>100000，向上取5000的整数倍
        return np.ceil(max_val / 5000) * 5000
    elif max_val > 10000:
        # 10000<max<=100000，向上取1000的整数倍
        return np.ceil(max_val / 1000) * 1000
    elif max_val > 1000:
        # 1000<max<=10000，向上取100的整数倍
        return np.ceil(max_val / 100) * 100
    elif max_val > 100:
        # 100<max<=1000，向上取50的整数倍
        return np.ceil(max_val / 50) * 50
    elif max_val > 20:
        # 20<max<=100，向上取5的整数倍
        return np.ceil(max_val / 5) * 5
    elif max_val > 10:
        # 10<max<=20，向上取2.5的整数倍
        return np.ceil(max_val / 2.5) * 2.5
    else:
        # max<=10，向上取0.5的整数倍
        return np.ceil(max_val * 2) / 2


def calculate_percentage_axis_min(min_val):
    """
    计算百分比格式的Y轴最小值
    
    Args:
        min_val: 数据最小值（百分比数值，如38.4表示38.4%）
    
    Returns:
        float: Y轴最小值
    """
    if min_val >= 100:
        # min>=100，向下取20%的整数倍
        return np.floor(min_val / 20) * 20
    else:
        # min<100，向下取5%的整数倍
        return np.floor(min_val / 5) * 5


def calculate_percentage_axis_max(max_val):
    """
    计算百分比格式的Y轴最大值
    
    Args:
        max_val: 数据最大值（百分比数值，如36.34表示36.34%）
    
    Returns:
        float: Y轴最大值
    """
    if max_val >= 100:
        # max>=100，向上取50%的整数倍
        return np.ceil(max_val / 50) * 50
    else:
        # max<100，向上取5%的整数倍
        return np.ceil(max_val / 5) * 5


def calculate_y_axis_range(min_val, max_val, display_format):
    """
    根据数据展示格式计算Y轴范围
    
    Args:
        min_val: 数据最小值
        max_val: 数据最大值
        display_format: 展示格式 ('原始数值', '比值', '百分比', '对数值')
    
    Returns:
        tuple: (y_min, y_max)
    """
    if display_format == '原始数值':
        # 原始数据：基于数据范围计算Y轴，向上和向下扩展50%
        range_val = max_val - min_val
        y_max = np.ceil(max_val + range_val * 0.5)
        y_min = np.floor(min_val - range_val * 0.5)
        
    elif display_format == '比值':
        # 比值：根据数值范围使用不同的整数倍数
        y_max = calculate_ratio_axis_max(max_val)
        y_min = calculate_ratio_axis_min(min_val)
        
    elif display_format == '百分比':
        # 百分比：根据新的需求描述
        y_max = calculate_percentage_axis_max(max_val)
        y_min = calculate_percentage_axis_min(min_val)
        
        # 确保最小值不小于0（百分比通常不应为负）
        y_min = max(0, y_min)
        
        # 如果y_min和y_max相等（例如所有数据都是100%），添加一些边距
        if y_min == y_max:
            y_min = max(0, y_min - 5)
            y_max = y_max + 5
        
    elif display_format == '对数值':
        # 对数值：自动调整，最大值比max更大一些，最小值比min小一些
        range_val = max_val - min_val
        padding = range_val * 0.1 if range_val > 0 else 0.1
        y_max = max_val + padding
        y_min = min_val - padding
        
    else:
        # 默认处理
        y_min = min_val
        y_max = max_val
    
    return y_min, y_max


def transform_data_for_display(param_data, display_format='原始数值', day_zero_date=None):
    """根据展示格式转换数据
    
    Args:
        param_data: 原始参数数据（来自get_experiment_data函数）
        display_format: 展示格式 ('原始数值', '比值', '百分比', '对数值')
        day_zero_date: Day 0日期（用于比值和百分比计算）
    
    Returns:
        转换后的数据
    """
    try:
        transformed_data = {}
        
        for group_name in param_data.keys():
            transformed_data[group_name] = {}
            
            # 检查数据结构：如果是{'dates': [...], 'values': [...]}格式，先转换
            if 'dates' in param_data[group_name] and 'values' in param_data[group_name]:
                dates = param_data[group_name]['dates']
                values = param_data[group_name]['values']
                
                # 找到Day 0的索引（如果需要）
                day_zero_index = None
                day_zero_value = None
                if display_format in ['比值', '百分比']:
                    if day_zero_date:
                        try:
                            day_zero_index = dates.index(day_zero_date)
                            day_zero_value = values[day_zero_index]
                        except ValueError:
                            # 如果指定的Day 0不在日期列表中，使用有数据的日期里最早的一天
                            day_zero_index = 0
                            day_zero_value = values[0]
                            day_zero_date = dates[0]
                    else:
                        # 如果没有指定Day 0，使用有数据的日期里最早的一天
                        day_zero_index = 0
                        day_zero_value = values[0]
                        day_zero_date = dates[0]
                
                # 转换每个值
                transformed_values = []
                for i, value in enumerate(values):
                    if display_format == '原始数值':
                        transformed_values.append(value)
                    elif display_format == '比值':
                        if day_zero_value is not None and day_zero_value != 0:
                            transformed_values.append(value / day_zero_value)
                        else:
                            transformed_values.append(1.0)  # 避免除零
                    elif display_format == '百分比':
                        if day_zero_value is not None and day_zero_value != 0:
                            transformed_values.append((value / day_zero_value) * 100)
                        else:
                            transformed_values.append(100.0)  # 避免除零
                    elif display_format == '对数值':
                        if value > 0:
                            transformed_values.append(np.log10(value))
                        else:
                            transformed_values.append(0)  # 避免对负数或零取对数
                    else:
                        transformed_values.append(value)
                
                # 保持原始的数据结构
                transformed_data[group_name] = {
                    'dates': dates,
                    'values': transformed_values
                }
            else:
                # 原始的数据结构：{date: [values], ...}
                dates = sorted(param_data[group_name].keys())
                
                # 找到Day 0的数据值（如果需要）
                day_zero_values = None
                if display_format in ['比值', '百分比']:
                    if day_zero_date:
                        if day_zero_date in param_data[group_name]:
                            day_zero_values = param_data[group_name][day_zero_date]
                        else:
                            # 如果指定的Day 0没有数据，使用有数据的日期里最早的一天
                            for date in dates:
                                if date in param_data[group_name]:
                                    day_zero_values = param_data[group_name][date]
                                    break
                    else:
                        # 如果没有指定Day 0，使用有数据的日期里最早的一天
                        for date in dates:
                            if date in param_data[group_name]:
                                day_zero_values = param_data[group_name][date]
                                break
                
                for date in dates:
                    original_values = param_data[group_name][date]
                    transformed_values = []
                    
                    for value in original_values:
                        if display_format == '原始数值':
                            transformed_values.append(value)
                        elif display_format == '比值':
                            if day_zero_values and len(day_zero_values) > 0:
                                # 使用Day 0的平均值作为基准
                                day_zero_mean = np.mean(day_zero_values)
                                if day_zero_mean != 0:
                                    transformed_values.append(value / day_zero_mean)
                                else:
                                    transformed_values.append(1.0)  # 避免除零
                            else:
                                transformed_values.append(1.0)
                        elif display_format == '百分比':
                            if day_zero_values and len(day_zero_values) > 0:
                                # 使用Day 0的平均值作为基准
                                day_zero_mean = np.mean(day_zero_values)
                                if day_zero_mean != 0:
                                    transformed_values.append((value / day_zero_mean) * 100)
                                else:
                                    transformed_values.append(100.0)  # 避免除零
                            else:
                                transformed_values.append(100.0)
                        elif display_format == '对数值':
                            if value > 0:
                                transformed_values.append(np.log10(value))
                            else:
                                transformed_values.append(0)  # 避免对负数或零取对数
                        else:
                            transformed_values.append(value)
                    
                    transformed_data[group_name][date] = transformed_values
        
        return transformed_data
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise e


@app.route('/api/experiment-charts/<experiment_name>', methods=['GET'])
def generate_experiment_charts(experiment_name):
    """生成实验数据的图表图片（SVG格式，保存到data/images目录）"""
    print(f"INFO: generate_experiment_charts called for {experiment_name} with display_format={request.args.get('display_format', '原始数值')}")
    try:
        # 确保matplotlib中文字体设置正确
        enable_zh_cn = os.environ.get('enable_zh_CN', 'TRUE').upper() == 'TRUE'
        if enable_zh_cn:
            plt.rcParams['font.sans-serif'] = ['WenQuanYi Zen Hei', 'DejaVu Sans', 'sans-serif']
            plt.rcParams['axes.unicode_minus'] = False
        force_regenerate = request.args.get('force', 'false').lower() == 'true'
        display_format = request.args.get('display_format', '原始数值')
        day_zero_date = request.args.get('day_zero_date', None)
        
        # 修复中文参数编码问题
        if display_format == 'ç\x99¾å\x88\x86æ¯\x94':
            display_format = '百分比'
        elif display_format == 'æ¯\x94å\x80¼':
            display_format = '比值'
        
        print(f"DEBUG: 修复后的display_format={display_format}")
        
        # 获取实验信息
        experiment_info = get_experiment_info(experiment_name)
        
        # 检查是否是错误响应（元组形式）
        if isinstance(experiment_info, tuple) and len(experiment_info) >= 2:
            return experiment_info
        
        # 获取JSON数据
        if hasattr(experiment_info, 'get_json'):
            exp_data = experiment_info.get_json()
        else:
            # 直接是JSON数据
            exp_data = experiment_info
        parameters = exp_data['parameters'].split(',')
        
        # 构建表名
        table_name = get_safe_table_name(experiment_name)
        
        # 查询数据，只选择数值类型的参数
        with engine.connect() as conn:
            query = text(f"""
            SELECT date, group_name, parameter_name, parameter_value
            FROM {table_name}
            ORDER BY date, group_name, parameter_name
            """)
            results = conn.execute(query).fetchall()
        
        # 组织数据，只处理数值类型的参数
        data = {}
        numeric_params = set()
        
        for row in results:
            date_str = row[0]
            group_name = row[1]
            param_name = row[2]
            param_value = row[3]
            
            # 尝试将值转换为数字
            try:
                numeric_value = float(param_value)
                numeric_params.add(param_name)
                
                if param_name not in data:
                    data[param_name] = {}
                
                if group_name not in data[param_name]:
                    data[param_name][group_name] = {}
                
                if date_str not in data[param_name][group_name]:
                    data[param_name][group_name][date_str] = []
                
                data[param_name][group_name][date_str].append(numeric_value)
            except (ValueError, TypeError):
                # 非数值类型，跳过
                continue
        
        # 如果没有数值参数，返回空结果
        if not numeric_params:
            return jsonify({'charts': [], 'parameters': []})
        
        # 为每个参数生成图表
        charts = []
        
        for param_name in sorted(numeric_params):
            if param_name.strip() not in data:
                continue
            
            param_data = data[param_name.strip()]
            
            # 生成SVG文件
            file_path = generate_chart_svg(
                experiment_name, 
                param_name.strip(), 
                param_data, 
                force_regenerate,
                display_format,
                day_zero_date
            )
            
            # 调试日志
            app.logger.info(f"DEBUG: Generated chart for {param_name.strip()}, display_format={display_format}, file_path={file_path}")
            
            # 使用generate_chart_svg返回的路径（在Docker中是绝对路径）
            charts.append({
                'parameter': param_name.strip(),
                'file_path': file_path,
                'display_format': display_format,
                'day_zero_date': day_zero_date
            })
        
        return jsonify({
            'charts': charts,
            'parameters': [p.strip() for p in parameters if p.strip() in numeric_params],
            'display_format': display_format,
            'day_zero_date': day_zero_date
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/data/<path:filename>')
def serve_data_file(filename):
    """提供data目录下的文件访问"""
    # 在Docker环境中使用/data目录，在本地环境中使用当前目录下的data目录
    # 统一使用/data目录（Docker中为挂载点，本地为./data）
    data_dir = '/data' if os.environ.get('DOCKER_ENV') == 'true' else os.path.join(os.path.dirname(__file__), 'data')
    
    return send_from_directory(data_dir, filename)


def export_experiment_data_to_csv(experiment_name, parameter_name, export_format):
    """导出实验数据为CSV格式"""
    try:
        # 获取实验信息
        experiment_info = get_experiment_info(experiment_name)
        if experiment_info.status_code != 200:
            return None, "实验不存在"
        
        exp_data = experiment_info.get_json()
        parameters = exp_data['parameters'].split(',')
        group_info = exp_data['group_info']
        
        # 构建表名
        table_name = get_safe_table_name(experiment_name)
        
        # 查询所有数据
        with engine.connect() as conn:
            query = text(f"""
            SELECT date, group_name, animal_id, parameter_name, parameter_value
            FROM {table_name}
            WHERE parameter_name = :parameter_name
            ORDER BY group_name, animal_id, date
            """)
            results = conn.execute(query, {'parameter_name': parameter_name}).fetchall()
        
        if not results:
            return None, "没有找到指定参数的数据"
        
        # 组织数据
        data_dict = {}
        dates = set()
        
        for row in results:
            date_str = row[0]
            group_name = row[1]
            animal_id = row[2]
            param_value = row[4]
            
            dates.add(date_str)
            
            key = f"{group_name}_{animal_id}"
            if key not in data_dict:
                # 解析笼号（假设动物编号格式为组别-笼号-动物编号，如G1-C1-01）
                parts = animal_id.split('-')
                cage_number = parts[1] if len(parts) > 1 else ""
                
                data_dict[key] = {
                    'group_name': group_name,
                    'cage_number': cage_number,
                    'animal_id': animal_id,
                    'values': {}
                }
            
            data_dict[key]['values'][date_str] = param_value
        
        # 排序日期
        sorted_dates = sorted(list(dates))
        
        # 生成CSV内容
        import io
        import csv
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入表头
        header = ['组别名称', '笼号', '动物编号'] + sorted_dates
        writer.writerow(header)
        
        if export_format == '实验记录格式':
            # 实验记录格式：动物按行连续排列
            for key in sorted(data_dict.keys()):
                animal_data = data_dict[key]
                row = [
                    animal_data['group_name'],
                    animal_data['cage_number'],
                    animal_data['animal_id']
                ]
                
                for date in sorted_dates:
                    row.append(animal_data['values'].get(date, ''))
                
                writer.writerow(row)
        else:
            # GraphPad分析格式：按照最大动物数量的组的动物数重复留空
            # 计算每组的最大动物数量
            group_animal_counts = {}
            for key in data_dict.keys():
                group_name = data_dict[key]['group_name']
                if group_name not in group_animal_counts:
                    group_animal_counts[group_name] = 0
                group_animal_counts[group_name] += 1
            
            # 找出最大动物数量
            max_animals_per_group = max(group_animal_counts.values())
            
            # 按组导出数据
            for group in group_info:
                group_name = group['name']
                
                # 获取该组所有动物
                group_animals = [data_dict[key] for key in sorted(data_dict.keys()) 
                                if data_dict[key]['group_name'] == group_name]
                
                # 写入该组动物数据
                for animal in group_animals:
                    row = [
                        animal['group_name'],
                        animal['cage_number'],
                        animal['animal_id']
                    ]
                    
                    for date in sorted_dates:
                        row.append(animal['values'].get(date, ''))
                    
                    writer.writerow(row)
                
                # 如果该组动物数量不足最大数量，补充空行
                empty_rows_count = max_animals_per_group - len(group_animals)
                for _ in range(empty_rows_count):
                    empty_row = ['', '', ''] + [''] * len(sorted_dates)
                    writer.writerow(empty_row)
        
        # 添加最后三行描述信息
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        writer.writerow([])  # 空行
        writer.writerow([f"实验名称：{experiment_name}"])
        writer.writerow([f"参数名称：{parameter_name}"])
        writer.writerow([f"数据导出时间：{current_time}"])
        
        return output.getvalue(), None
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, str(e)


@app.route('/api/export-experiment-data', methods=['POST'])
def export_experiment_data():
    """导出实验数据API"""
    try:
        req_data = request.get_json()
        experiment_name = req_data.get('experiment_name', '')
        parameter_name = req_data.get('parameter_name', '')
        export_format = req_data.get('export_format', '实验记录格式')
        
        if not experiment_name:
            return jsonify({'error': '实验名称不能为空'}), 400
        
        if not parameter_name:
            return jsonify({'error': '参数名称不能为空'}), 400
        
        if export_format not in ['实验记录格式', 'GraphPad分析格式']:
            return jsonify({'error': '导出格式必须是"实验记录格式"或"GraphPad分析格式"'}), 400
        
        # 导出CSV数据
        csv_content, error = export_experiment_data_to_csv(experiment_name, parameter_name, export_format)
        
        if error:
            return jsonify({'error': error}), 500
        
        # 确定目录 - 统一使用data/results目录
        export_dir = '/data/results'
        
        os.makedirs(export_dir, exist_ok=True)
        
        # 生成文件名
        current_date = datetime.now().strftime('%Y-%m-%d')
        filename = f"{experiment_name}_{parameter_name}_{export_format}_{current_date}.csv"
        filepath = os.path.join(export_dir, filename)
        
        # 保存文件
        with open(filepath, 'w', encoding='utf-8-sig') as f:
            f.write(csv_content)
        
        return jsonify({
            'status': 'success',
            'filename': filename,
            'filepath': filepath,
            'message': '数据导出成功'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/download-export/<filename>')
def download_export(filename):
    """下载导出的CSV文件"""
    try:
        # 确定目录 - 统一使用data/results目录
        export_dir = '/data/results'
        
        filepath = os.path.join(export_dir, filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': '文件不存在'}), 404
        
        return send_from_directory(export_dir, filename, as_attachment=True, 
                                 download_name=filename, mimetype='text/csv')
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/experiment-day-zero/<experiment_name>', methods=['GET'])
def get_day_zero_date(experiment_name):
    """获取实验的Day 0日期"""
    try:
        with engine.connect() as conn:
            query = text("""
            SELECT day_zero_date FROM experiment_day_zero
            WHERE experiment_name = :exp_name
            """)
            result = conn.execute(query, {'exp_name': experiment_name}).fetchone()
            
            if result:
                return jsonify({
                    'day_zero_date': result[0],
                    'status': 'found'
                })
            else:
                return jsonify({
                    'day_zero_date': None,
                    'status': 'not_found'
                })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/experiment-day-zero', methods=['POST'])
def save_day_zero_date():
    """保存实验的Day 0日期"""
    try:
        req_data = request.get_json()
        experiment_name = req_data.get('experiment_name', '')
        day_zero_date = req_data.get('day_zero_date', '')
        
        if not experiment_name:
            return jsonify({'error': '实验名称不能为空'}), 400
        
        if not day_zero_date:
            return jsonify({'error': 'Day 0日期不能为空'}), 400
        
        with engine.connect() as conn:
            # 使用UPSERT语法（SQLite 3.24+）或先删除再插入
            delete_query = text("""
            DELETE FROM experiment_day_zero
            WHERE experiment_name = :exp_name
            """)
            conn.execute(delete_query, {'exp_name': experiment_name})
            
            insert_query = text("""
            INSERT INTO experiment_day_zero (experiment_name, day_zero_date, updated_at)
            VALUES (:exp_name, :day_zero_date, :updated_at)
            """)
            conn.execute(insert_query, {
                'exp_name': experiment_name,
                'day_zero_date': day_zero_date,
                'updated_at': datetime.now()
            })
            conn.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Day 0日期保存成功'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/data-export')
def data_export():
    """Serve the data export page"""
    return render_template('data_export.html')


@app.route('/data-recording')
def data_recording():
    """Serve the data recording page"""
    # 密码获取优先级：
    # 1. 环境变量（来自docker-compose.yml或--build-arg）
    # 2. 默认值
    password = os.environ.get('DATA_RECORDING_PASSWORD', 'data2024')
    return render_template('data_recording.html', password=password)


@app.route('/test')
def test_page():
    """Serve the test page"""
    return send_from_directory('static', 'test.html')


@app.route('/test-experiments')
def test_experiments():
    """Test experiments API"""
    return send_from_directory('static', 'test_experiments.html')


@app.route('/test-fixed')
def test_fixed_page():
    """Serve the test fixed page"""
    return render_template('test_password_fixed.html')


# 修复JSON编码问题
app.config['JSON_AS_ASCII'] = False
app.config['JSON_ENSURE_ASCII'] = False

if __name__ == '__main__':
    # Initialize the database
    init_db()
    
    # Run the Flask application
    app.run(debug=True, host='0.0.0.0', port=8080)