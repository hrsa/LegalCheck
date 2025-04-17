from loguru import logger
from sqlalchemy import Boolean, event, inspect, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Mapped, mapped_column, Query, RelationshipProperty, joinedload, contains_eager
from sqlalchemy.future import select

"""
Soft Delete functionality for SQLAlchemy models.

This module provides a mixin class and utility functions for implementing soft delete
functionality in SQLAlchemy models. Soft delete means that records are marked as deleted
instead of being physically removed from the database.

For SQLAlchemy 2.0 and async operations, use the `filtered_select` function to create
select statements that automatically filter out soft-deleted records:

    from app.db.soft_delete import filtered_select

    # This will automatically filter out soft-deleted records
    stmt = filtered_select(User)
    result = await db.execute(stmt)

    # To include soft-deleted records
    stmt = filtered_select(User, include_deleted=True)
    result = await db.execute(stmt)

    # For more complex queries, you can use the soft_delete_filter function
    stmt = select(User).join(Document)
    stmt = soft_delete_filter(stmt, User)
    result = await db.execute(stmt)
"""


class SoftDeleteMixin:
    """
    Mixin class to provide soft delete functionality to SQLAlchemy models.
    """

    @declared_attr
    def is_deleted(cls) -> Mapped[bool]:
        return mapped_column(Boolean, default=False, nullable=False, index=True)

    async def soft_delete(self, db:AsyncSession, cascade=True):
        self.is_deleted = True

        if cascade and db:
            await cascade_soft_delete(self, db)

    async def restore(self, db=None, cascade=True, restore_children=False):
        """
        Restore a soft-deleted record.

        Args:
            db: SQLAlchemy async session to use for cascading restores
            cascade: Whether to cascade the restore to related objects
            restore_children: Whether to restore one-to-many related objects (children)
        """
        self.is_deleted = False

        if cascade and db:
            await cascade_restore(self, db, restore_children=restore_children)


async def cascade_soft_delete(obj, db):
    mapper = inspect(obj.__class__)
    for relationship in mapper.relationships:
        if relationship.cascade.delete:
            related_class = relationship.mapper.class_

            if relationship.direction.name == 'MANYTOONE':
                continue
            elif relationship.direction.name == 'ONETOMANY':
                for column in relationship.remote_side:
                    column_name = column.name
                    parent_id = getattr(obj, 'id')
                    stmt = select(related_class).where(getattr(related_class, column_name) == parent_id)
                    break
            else:
                stmt = select(related_class)

            try:
                result = await db.execute(stmt)
                related_entities = result.scalars().all()

                for entity in related_entities:
                    if hasattr(entity, 'is_deleted') and entity.is_deleted == False:
                        entity.is_deleted = True
                        await cascade_soft_delete(entity, db)
                        await db.commit()
            except Exception as e:
                logger.warning(f"Error soft deleting related objects for {relationship.key}: {str(e)}")
                raise e


async def cascade_restore(obj, db, restore_children=False):
    mapper = inspect(obj.__class__)
    for relationship in mapper.relationships:
        # Only process relationships with cascade delete, similar to cascade_soft_delete
        if relationship.cascade.delete:
            related_class = relationship.mapper.class_

            if relationship.direction.name == 'MANYTOONE':
                for column in relationship.local_columns:
                    column_name = column.name
                    parent_id = getattr(obj, 'id')
                    stmt = select(related_class).where(getattr(related_class, column_name) == parent_id)
                    break
            elif relationship.direction.name == 'ONETOMANY':
                # Skip ONETOMANY relationships unless restore_children is True
                if not restore_children:
                    continue

                for column in relationship.remote_side:
                    column_name = column.name
                    parent_id = getattr(obj, 'id')
                    stmt = select(related_class).where(getattr(related_class, column_name) == parent_id)
                    break
            else:
                stmt = select(related_class)

            if hasattr(related_class, 'is_deleted'):
                stmt = stmt.filter(related_class.is_deleted == True)

            try:
                result = await db.execute(stmt)
                related_entities = result.scalars().all()

                for entity in related_entities:
                    if hasattr(entity, 'is_deleted') and entity.is_deleted == True:
                        entity.is_deleted = False
                        await cascade_restore(entity, db, restore_children)
                        await db.commit()
            except Exception as e:
                logger.error(f"Error restoring related objects for {relationship.key}: {str(e)}")
                raise e


def soft_delete_filter(stmt, model_class=None, include_deleted=False):
    """
    Add a filter to exclude soft-deleted records from a select statement.

    Args:
        stmt: The select statement to filter
        model_class: The model class to filter on (optional, will be inferred from stmt if not provided)
        include_deleted: Whether to include soft-deleted records

    Returns:
        The filtered select statement
    """
    if include_deleted:
        return stmt

    if model_class is None:
        # Try to infer the model class from the statement
        if hasattr(stmt, 'entity_description') and hasattr(stmt.entity_description, 'entity'):
            model_class = stmt.entity_description.entity
        elif hasattr(stmt, 'columns') and stmt.columns:
            for col in stmt.columns:
                if hasattr(col, 'table') and hasattr(col.table, 'entity'):
                    model_class = col.table.entity
                    break

    if model_class and hasattr(model_class, 'is_deleted'):
        stmt = stmt.filter(model_class.is_deleted == False)

    return stmt

# Convenience function to create a select statement that automatically filters out soft-deleted records
def filtered_select(*entities, include_deleted=False, **kw):
    """
    Create a select statement that automatically filters out soft-deleted records.

    Args:
        *entities: The entities to select
        include_deleted: Whether to include soft-deleted records
        **kw: Additional keyword arguments to pass to select()

    Returns:
        The filtered select statement
    """
    stmt = select(*entities, **kw)

    if len(entities) == 1 and not include_deleted:
        model_class = entities[0]
        return soft_delete_filter(stmt, model_class, include_deleted)

    return stmt


def filtered_load(relationship, include_deleted=False):
    """
    Create a function that applies a soft delete filter to a relationship.

    Args:
        relationship: The relationship to load (e.g., AnalysisResult.checklist)
        include_deleted: Whether to include soft-deleted records

    Returns:
        A tuple of (join_condition, loader_option) that can be used in a query
    """
    # Get the target entity class
    target_class = relationship.prop.mapper.class_

    # Create the join condition
    join_condition = relationship

    # Create the filter condition for soft delete
    if not include_deleted and hasattr(target_class, 'is_deleted'):
        # Add the soft delete filter to the join condition
        join_condition = and_(
            join_condition,
            target_class.is_deleted == False
        )

    # Create the loader option
    loader_option = contains_eager(relationship)

    return join_condition, loader_option
