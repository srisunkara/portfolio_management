import inspect
import uuid
from datetime import datetime, date, time
from typing import get_origin, get_args, Union

import pydantic

import models  # Import the file containing your Pydantic models

# Define the type mapping
TYPE_MAPPING = {
    int: "INTEGER",
    str: "TEXT",
    float: "DOUBLE PRECISION",
    bool: "BOOLEAN",
    date: "DATE",
    time: "TIME",
    datetime: "TIMESTAMP",
    uuid.UUID: "UUID",
}


def get_sql_type(py_type):
    """Maps a Python type to its SQL equivalent."""
    # Check for Optional types (e.g., Optional[int])
    if get_origin(py_type) is Union:
        args = get_args(py_type)
        if type(None) in args:
            # Unwrap the actual type from Optional
            py_type = args[0] if args[1] is type(None) else args[1]

    return TYPE_MAPPING.get(py_type)


def generate_create_table_sql(model: pydantic.BaseModel):
    """
    Generates a SQL CREATE TABLE statement from a Pydantic model.
    Assumes the first field is the primary key.
    """
    table_name = model.__name__.lower()

    fields = []

    # Iterate through the model's fields
    for i, (field_name, field_info) in enumerate(model.model_fields.items()):
        sql_type = get_sql_type(field_info.annotation)

        if not sql_type:
            print(f"Warning: No SQL type mapping for '{field_name}' with type {field_info.annotation}")
            continue

        constraints = []

        # Determine if the field is the primary key
        if i == 0:
            constraints.append("PRIMARY KEY")

        # Check for non-optional fields
        if not isinstance(field_info.annotation, type(None)):
            constraints.append("NOT NULL")

        # Handle default values
        if field_info.default is not pydantic.fields.PydanticUndefined:
            # Simple handling for common types
            if isinstance(field_info.default, (str, uuid.UUID)):
                constraints.append(f"DEFAULT '{field_info.default}'")
            elif isinstance(field_info.default, (int, float, bool)):
                constraints.append(f"DEFAULT {field_info.default}")

        field_definition = f'    "{field_name}" {sql_type} {" ".join(constraints)}'
        fields.append(field_definition)

    sql = f'CREATE TABLE IF NOT EXISTS "{table_name}" (\n'
    sql += ",\n".join(fields)
    sql += "\n);"

    return sql


# Assuming your models are in a file named 'models.py'
# models.py
# from pydantic import BaseModel
# import uuid
# class User(BaseModel):
#     user_id: uuid.UUID
#     name: str
#     email: str
# class Product(BaseModel):
#     product_id: int
#     name: str
#     price: float
#     is_active: bool = True


# Find all Pydantic models in the imported module
models_list = [
    obj for name, obj in inspect.getmembers(models)
    if inspect.isclass(obj) and issubclass(obj, pydantic.BaseModel) and obj is not pydantic.BaseModel
]

# Generate and print the SQL
for pydantic_model in models_list:
    sql_script = generate_create_table_sql(pydantic_model)
    print(sql_script)
    # print("\n" + "-" * 50 + "\n")
