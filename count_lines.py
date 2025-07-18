import os
import sys

def count_code_lines(directory):
    total_lines = 0
    feature_code_lines = 0
    config_code_lines = 0
    file_type_counts = {}
    
    # 定义功能代码和配置代码的扩展名
    feature_extensions = ['.py', '.js', '.html', '.css']
    config_extensions = ['.json', '.yml', '.yaml', '.cfg', '.ini', '.env']
    
    excluded_extensions = ['.md', '.gitignore', '.keep', '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.db', '.mo']
    excluded_dirs = ['.venv', '__pycache__', 'node_modules']

    for root, dirs, files in os.walk(directory):
        # 排除特定目录
        dirs[:] = [d for d in dirs if d not in excluded_dirs]

        for file in files:
            _, ext = os.path.splitext(file)
            if ext in excluded_extensions:
                continue

            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    line_count = len(lines)
                    total_lines += line_count

                    # 统计功能代码和配置代码
                    if ext in feature_extensions:
                        feature_code_lines += line_count
                    elif ext in config_extensions:
                        config_code_lines += line_count

                    if ext not in file_type_counts:
                        file_type_counts[ext] = 0
                    file_type_counts[ext] += line_count
            except Exception as e:
                print(f"无法读取文件 {file_path}: {e}", file=sys.stderr)

    return total_lines, feature_code_lines, config_code_lines, file_type_counts

if __name__ == '__main__':
    directory = os.path.dirname(os.path.abspath(__file__))
    total_lines, feature_code_lines, config_code_lines, file_type_counts = count_code_lines(directory)

    print(f"总代码行数: {total_lines}")
    print(f"功能代码行数: {feature_code_lines}")
    print(f"配置代码行数: {config_code_lines}")
    print("按文件类型统计:")
    for ext, count in sorted(file_type_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"{ext}: {count} 行")