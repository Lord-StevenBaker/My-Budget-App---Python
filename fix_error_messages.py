import os
import re

# Path to goals_tab.py
goals_tab_path = os.path.join('ui', 'goals_tab.py')

# Read the file contents
with open(goals_tab_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace all instances of the error message
pattern = r'QMessageBox\.warning\(self, "Error", "Could not find goal data"\)'
replacement = r'QMessageBox.information(self, "Goal Not Found", "The selected goal could not be found. It may have been deleted or the database connection failed.")'

new_content = re.sub(pattern, replacement, content)
print(f"Replacing {content.count('Could not find goal data')} occurrences of the error message")

# Write back the updated content
with open(goals_tab_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Successfully updated all error messages in goals_tab.py")
