import json

def extract_row_names(json_file_path, output_file_path):
    """
    Extract row names from JSON data and save to text file.
    
    Args:
        json_file_path (str): Path to the input JSON file
        output_file_path (str): Path to the output text file
    """
    try:
        # Read the JSON file
        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
         # Extract row names from the "Rows" section
        # Handle case where data is an array
        if isinstance(data, list) and len(data) > 0:
            data = data[0]  # Get the first element if it's an array
        
        if "Rows" in data:
            row_names = list(data["Rows"].keys())
        else:
            print("No 'Rows' section found in the JSON data")
            return
        
        # Write row names to text file
        with open(output_file_path, 'w', encoding='utf-8') as file:
            for row_name in row_names:
                file.write(row_name + '\n')
        
        print(f"Successfully extracted {len(row_names)} row names to {output_file_path}")
        print("Row names found:")
        for name in row_names:
            print(f"  - {name}")
            
    except FileNotFoundError:
        print(f"Error: File '{json_file_path}' not found")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in '{json_file_path}'")
    except Exception as e:
        print(f"Error: {str(e)}")

# Example usage
if __name__ == "__main__":
    # Replace these paths with your actual file paths
    input_file = "list_store.json"  # Path to your JSON file
    output_file = "row_names.txt"  # Output text file
    
    extract_row_names(input_file, output_file)