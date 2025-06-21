from datetime import datetime
import uuid
import os

from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask import url_for

from . import db

# ───────────────────────────────────────────────────────────────
#  Пользователь
# ───────────────────────────────────────────────────────────────
class User(UserMixin, db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    pw_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    avatar = db.Column(db.Text, nullable=True)
    created = db.Column(db.DateTime, default=datetime.utcnow)
    is_system = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)

    # отношения
    recipes = db.relationship(
        "Recipe", backref="author", lazy=True, cascade="all, delete-orphan"
    )
    comments = db.relationship(
        "Comment", backref="user", lazy=True, cascade="all, delete-orphan"
    )
    ratings = db.relationship(
        "Rating", backref="user", lazy=True, cascade="all, delete-orphan"
    )
    favorites = db.relationship(
        "Favorite", backref="user", lazy=True, cascade="all, delete-orphan"
    )
    external_favorites = db.relationship(
        "ExternalFavorite", backref="user", lazy=True, cascade="all, delete-orphan"
    )
    external_ratings = db.relationship(
        "ExternalRating", backref="user", lazy=True, cascade="all, delete-orphan"
    )
    external_comments = db.relationship(
        "ExternalComment", backref="user", lazy=True, cascade="all, delete-orphan"
    )

    # методы
    def set_password(self, password):
        self.pw_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.pw_hash, password)

    @property
    def avatar_url(self):
        if self.avatar:
            avatar_url = url_for('static', filename=f'avatars/{self.avatar}', _external=True)
            # Replace localhost with the actual domain in production
            if 'localhost' in avatar_url:
                return avatar_url.replace('http://localhost:5000', 'https://tastebite-back.onrender.com')
            return avatar_url
        return None

    def to_dict(self):
        avatar_url = self.avatar_url
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "avatar": avatar_url,
            "created": self.created.isoformat(),
            "is_admin": self.is_admin,
        }


# ───────────────────────────────────────────────────────────────
#  Рецепт
# ───────────────────────────────────────────────────────────────
class Recipe(db.Model):
    __tablename__ = "recipe"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(80))
    area = db.Column(db.String(80))
    instructions = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", name="fk_recipe_user"),
        nullable=False,
    )

    # для импортированных из MealDB
    is_external = db.Column(db.Boolean, default=False)
    external_id = db.Column(db.String(50))

    # отношения
    ingredients = db.relationship(
        "Ingredient", backref="recipe", lazy=True, cascade="all, delete-orphan"
    )
    comments = db.relationship(
        "Comment", backref="recipe", lazy=True, cascade="all, delete-orphan"
    )
    ratings = db.relationship(
        "Rating", backref="recipe", lazy=True, cascade="all, delete-orphan"
    )
    favorited_by = db.relationship(
        "Favorite", backref="recipe", lazy=True, cascade="all, delete-orphan"
    )

    def average_rating(self):
        if not self.ratings:
            return 0
        return sum(r.value for r in self.ratings) / len(self.ratings)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "area": self.area,
            "instructions": self.instructions,
            "image_url": self.image_url,
            "created_at": self.created_at.isoformat(),
            "user_id": self.user_id,
            "author": self.author.to_dict(),
            "ingredients": [ing.to_dict() for ing in self.ingredients],
            "average_rating": self.average_rating(),
            "ratings_count": len(self.ratings),
            "is_external": self.is_external,
            "external_id": self.external_id,
        }


# ───────────────────────────────────────────────────────────────
#  Ингредиент
# ───────────────────────────────────────────────────────────────
class Ingredient(db.Model):
    __tablename__ = "ingredient"

    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(
        db.Integer,
        db.ForeignKey("recipe.id", name="fk_ingredient_recipe"),
    )
    name = db.Column(db.String(120), nullable=False)
    measure = db.Column(db.String(80))

    def to_dict(self):
        return {"id": self.id, "name": self.name, "measure": self.measure}


# ───────────────────────────────────────────────────────────────
#  Комментарий
# ───────────────────────────────────────────────────────────────
class Comment(db.Model):
    __tablename__ = "comment"

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", name="fk_comment_user", ondelete="CASCADE"),
        nullable=False,
    )
    recipe_id = db.Column(
        db.Integer,
        db.ForeignKey("recipe.id", name="fk_comment_recipe"),
        nullable=False,
    )

    def to_dict(self):
        return {
            "id": self.id,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
            "user": self.user.to_dict(),
        }


# ───────────────────────────────────────────────────────────────
#  Рейтинг
# ───────────────────────────────────────────────────────────────
class Rating(db.Model):
    __tablename__ = "rating"

    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Integer, nullable=False)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", name="fk_rating_user", ondelete="CASCADE"),
        nullable=False,
    )
    recipe_id = db.Column(
        db.Integer,
        db.ForeignKey("recipe.id", name="fk_rating_recipe"),
        nullable=False,
    )


# ───────────────────────────────────────────────────────────────
#  Избранное
# ───────────────────────────────────────────────────────────────
class Favorite(db.Model):
    __tablename__ = "favorite"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", name="fk_favorite_user", ondelete="CASCADE"),
        nullable=False,
    )
    recipe_id = db.Column(
        db.Integer,
        db.ForeignKey("recipe.id", name="fk_favorite_recipe"),
        nullable=False,
    )


# ───────────────────────────────────────────────────────────────
#  External models (MealDB) — если нужны
# ───────────────────────────────────────────────────────────────
class ExternalFavorite(db.Model):
    __tablename__ = "external_favorite"

    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(db.String(20), nullable=False)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", name="fk_external_favorite_user", ondelete="CASCADE"),
        nullable=False,
    )

    __table_args__ = (
        db.UniqueConstraint("external_id", "user_id", name="uq_external_favorite_user"),
    )


class ExternalRating(db.Model):
    __tablename__ = "external_rating"

    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Integer, nullable=False)
    external_id = db.Column(db.String(20), nullable=False)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", name="fk_external_rating_user", ondelete="CASCADE"),
        nullable=False,
    )

    __table_args__ = (
        db.UniqueConstraint("external_id", "user_id", name="uq_external_rating_user"),
    )


class ExternalComment(db.Model):
    __tablename__ = "external_comment"

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    external_id = db.Column(db.String(20), nullable=False)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", name="fk_external_comment_user", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
            "user": self.user.to_dict(),
        }


# ───────────────────────────────────────────────────────────────
#  Теги (если нужны)
# ───────────────────────────────────────────────────────────────
class Tag(db.Model):
    __tablename__ = "tag"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)

    def to_dict(self):
        return {"id": self.id, "name": self.name}

# ───────────────────────────────────────────────────────────────
#  Список покупок
# ───────────────────────────────────────────────────────────────
class ShoppingListItem(db.Model):
    __tablename__ = "shopping_list_item"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    measure = db.Column(db.String(200))
    recipe_titles = db.Column(db.Text)
    recipe_ids = db.Column(db.Text)
    is_checked = db.Column(db.Boolean, default=False, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        titles = self.recipe_titles.split('; ') if self.recipe_titles else []
        ids = self.recipe_ids.split('; ') if self.recipe_ids else []
        
        # Убедимся, что у нас есть ID для каждого названия
        recipe_details = []
        for i, title in enumerate(titles):
            if i < len(ids):
                recipe_details.append({"id": ids[i], "title": title})
            else:
                # Для старых записей, где ID может отсутствовать
                recipe_details.append({"id": None, "title": title})

        return {
            'id': self.id,
            'name': self.name,
            'measure': self.measure,
            'recipe_details': recipe_details,
            'is_checked': self.is_checked,
            'user_id': self.user_id
        }

class SharedShoppingList(db.Model):
    __tablename__ = "shared_shopping_list"

    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    user = db.relationship('User', backref=db.backref('shared_list', uselist=False))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        # Важно: URL фронтенда может отличаться. Пока используем стандартный.
        frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
        return {
            'token': self.token,
            'share_url': f"{frontend_url}/list/{self.token}"
        }
