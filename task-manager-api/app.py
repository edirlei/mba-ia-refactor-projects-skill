from flask import Flask
from flask_cors import CORS

from config.settings import load_settings, validate_settings
from controllers import (
    AuthController,
    CategoryController,
    ReportController,
    TaskController,
    UserController,
)
from database import db
from middlewares.error_handlers import register_error_handlers
from repositories import (
    CategoryRepository,
    ReportRepository,
    TaskRepository,
    UserRepository,
)
from routes.report_routes import create_report_blueprint
from routes.task_routes import create_task_blueprint
from routes.user_routes import create_user_blueprint
from services.auth_service import AuthService
from services.category_service import CategoryService
from services.report_service import ReportService
from services.task_service import TaskService
from services.user_service import UserService
from utils.time import utc_now


def create_app(config_overrides=None):
    app = Flask(__name__)
    app.config.from_mapping(load_settings())
    if config_overrides:
        app.config.update(config_overrides)
    validate_settings(app.config)

    CORS(app, origins=app.config["CORS_ORIGINS"])
    db.init_app(app)

    user_repository = UserRepository()
    task_repository = TaskRepository()
    category_repository = CategoryRepository()
    report_repository = ReportRepository(app.config["MAX_PAGE_SIZE"])

    auth_service = AuthService(
        user_repository,
        app.config["SECRET_KEY"],
        app.config["TOKEN_MAX_AGE_SECONDS"],
    )
    user_service = UserService(user_repository, task_repository)
    task_service = TaskService(
        task_repository, user_repository, category_repository
    )
    category_service = CategoryService(category_repository)
    report_service = ReportService(
        report_repository, task_repository, user_repository
    )

    auth_controller = AuthController(auth_service)
    user_controller = UserController(user_service)
    task_controller = TaskController(task_service)
    category_controller = CategoryController(category_service)
    report_controller = ReportController(report_service)

    app.register_blueprint(
        create_user_blueprint(user_controller, auth_controller, auth_service)
    )
    app.register_blueprint(create_task_blueprint(task_controller, auth_service))
    app.register_blueprint(
        create_report_blueprint(
            report_controller, category_controller, auth_service
        )
    )
    register_error_handlers(app)

    @app.get("/health")
    def health():
        return {"status": "ok", "timestamp": utc_now().isoformat()}

    @app.get("/")
    def index():
        return {"message": "Task Manager API", "version": "1.0"}

    return app


if __name__ == "__main__":
    application = create_app()
    application.run(
        debug=application.config["DEBUG"],
        host=application.config["HOST"],
        port=application.config["PORT"],
    )
