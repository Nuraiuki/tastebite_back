from datetime import datetime

from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

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

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
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
    image_url = db.Column(db.String(250))
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
