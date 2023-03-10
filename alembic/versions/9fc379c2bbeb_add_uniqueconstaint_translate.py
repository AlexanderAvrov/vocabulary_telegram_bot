"""add uniqueconstaint translate

Revision ID: 9fc379c2bbeb
Revises: 
Create Date: 2023-02-23 18:12:57.627222

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9fc379c2bbeb'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint('user_word_unique', 'Learning', ['user', 'word'])
    op.drop_constraint('Learning_word_fkey', 'Learning', type_='foreignkey')
    op.drop_constraint('Learning_user_fkey', 'Learning', type_='foreignkey')
    op.create_foreign_key(None, 'Learning', 'Translate', ['word'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(None, 'Learning', 'User', ['user'], ['id'], ondelete='CASCADE')
    op.add_column('Translate', sa.Column('english_expression', sa.String(length=256), nullable=False))
    op.add_column('Translate', sa.Column('russian_expression', sa.String(length=512), nullable=False))
    op.create_unique_constraint(None, 'Translate', ['english_expression'])
    op.drop_column('Translate', 'text')
    op.drop_column('Translate', 'translate')
    op.alter_column('User', 'id_user',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.create_unique_constraint(None, 'User', ['id_user'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'User', type_='unique')
    op.alter_column('User', 'id_user',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.add_column('Translate', sa.Column('translate', sa.VARCHAR(length=512), autoincrement=False, nullable=True))
    op.add_column('Translate', sa.Column('text', sa.VARCHAR(length=256), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'Translate', type_='unique')
    op.drop_column('Translate', 'russian_expression')
    op.drop_column('Translate', 'english_expression')
    op.drop_constraint(None, 'Learning', type_='foreignkey')
    op.drop_constraint(None, 'Learning', type_='foreignkey')
    op.create_foreign_key('Learning_user_fkey', 'Learning', 'User', ['user'], ['id'])
    op.create_foreign_key('Learning_word_fkey', 'Learning', 'Translate', ['word'], ['id'])
    op.drop_constraint('user_word_unique', 'Learning', type_='unique')
    # ### end Alembic commands ###
