import pandas as pd
import random
import json
from flask import Flask, request, jsonify, render_template, send_from_directory
from sqlalchemy import create_engine, text
from datetime import datetime
import numpy as np
import os


app = Flask(__name__)

# Use SQLite database
db_path = os.path.join(os.path.dirname(__file__), 'group_tool.db')
engine = create_engine(f"sqlite:///{db_path}")


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

    with engine.connect() as conn:
        conn.execute(text(create_table_sql))
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
    # Read CSV data into a pandas DataFrame
    df = pd.read_csv(pd.io.common.StringIO(data))

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


@app.route('/api/group', methods=['POST'])
def group_data():
    """
    API endpoint to perform layered random grouping.

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

        if not isinstance(layers, list) or len(layers) == 0:
            return jsonify({'error': 'Layers must be specified'}), 400

        if not isinstance(group_count, int) or group_count <= 0:
            return jsonify({'error': 'group_count must be a positive integer'}), 400

        # Perform the layered random grouping
        grouped_result = layered_random_grouping(data, group_count, layers, group_sizes)

        # Generate a random ID for this grouping result
        result_id = ''.join(random.choices('0123456789ABCDEF', k=6))

        # Store the result in the database
        store_result_in_db(result_id, grouped_result, group_count, ','.join(layers))

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
    data_json = json.dumps(grouped_result, ensure_ascii=False)

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


@app.route('/')
def index():
    """Serve the main page of the web application"""
    return render_template('index.html')


if __name__ == '__main__':
    # Initialize the database
    init_db()

    # Run the Flask application
    app.run(debug=True, host='0.0.0.0', port=20425)