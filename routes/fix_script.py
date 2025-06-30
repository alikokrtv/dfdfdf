import os

dof_path = "c:/Users/aliko/Downloads/CorrectionWorkflow (1)/CorrectionWorkflow/routes/dof.py"

with open(dof_path, 'r', encoding='utf-8') as f:
    content = f.read()

# requires_role ifadelerini temizle
content = content.replace("@requires_role([UserRole.DEPARTMENT_MANAGER, UserRole.ADMIN])", "")
content = content.replace("@requires_role", "")

with open(dof_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("DÖF dosyası temizlendi")
