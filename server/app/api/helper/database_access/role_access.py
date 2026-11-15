"""Role lookups by id or name and name-uniqueness checks. Name comparisons ignore case."""

import sqlalchemy  as sa
from app import db
from app.system_models import Role

# ============= Get From Database ===================
def get_role_by_id(role_id: int):
    """Return the Role with this id, or None."""
    return db.session.get(Role, role_id)

def get_role_by_name(role_name: str):
    """Return the Role whose name matches case-insensitively, or None."""
    return db.session.scalar(
        sa.select(Role)
        .where(
            sa.func.lower(Role.Name) == role_name.lower()
        )
    )

# ============= Find From Database ===================
def exists_role_by_id(role_id):
    """Return True if a Role with this id exists."""
    return db.session.scalar(
        sa.select(
            sa.exists()
            .where(
                Role.RoleID == role_id
            )
        )
    ) 

    
def exists_role_by_name(role_name):
    """Return True if a Role with this name exists, ignoring case."""
    return db.session.scalar(
        sa.select(
            sa.exists()
            .where(
                sa.func.lower(Role.Name) == role_name.lower()
            )
        )
    ) 
    
def has_name(role_name, id):
    """Return True if the role with this id has this name, ignoring case.

    Used to tell an unchanged name apart from a clash with another role.
    """
    return db.session.scalar(
        sa.select(
            sa.exists()
            .where(
                sa.func.lower(Role.Name) == role_name.lower(),
                Role.RoleID == id
            )
        )
    )
