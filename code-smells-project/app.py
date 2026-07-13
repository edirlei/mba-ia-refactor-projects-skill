import logging

from flask import Flask
from flask_cors import CORS

from config import Config
from controllers import (
    OrderController,
    ProductController,
    ReportController,
    SystemController,
    UserController,
)
from database import get_db, init_app as init_database, init_db
from errors import register_error_handlers
from repositories import (
    OrderRepository,
    ProductRepository,
    ReportRepository,
    SystemRepository,
    UserRepository,
)
from routes import (
    create_order_blueprint,
    create_product_blueprint,
    create_report_blueprint,
    create_system_blueprint,
    create_user_blueprint,
)
from services import AuthService, OrderService, ReportService, SystemService, UserService


def create_app(test_config=None):
    application = Flask(__name__)
    application.config.from_object(Config)
    if test_config:
        application.config.update(test_config)

    logging.basicConfig(level=logging.INFO)
    if application.config["CORS_ORIGINS"]:
        CORS(application, origins=application.config["CORS_ORIGINS"])

    init_database(application)
    register_error_handlers(application)
    _register_blueprints(application)

    @application.cli.command("init-db")
    def initialize_database_command():
        init_db()

    return application


def _register_blueprints(application):
    product_repository = ProductRepository(get_db)
    user_repository = UserRepository(get_db)
    order_repository = OrderRepository(get_db)
    report_repository = ReportRepository(get_db)
    system_repository = SystemRepository(get_db)

    product_controller = ProductController(product_repository)
    user_controller = UserController(
        user_repository,
        UserService(user_repository),
        AuthService(user_repository),
    )
    order_controller = OrderController(OrderService(order_repository))
    report_controller = ReportController(ReportService(report_repository))
    system_controller = SystemController(
        SystemService(system_repository, application.config["ADMIN_TOKEN"])
    )

    application.register_blueprint(create_product_blueprint(product_controller))
    application.register_blueprint(create_user_blueprint(user_controller))
    application.register_blueprint(create_order_blueprint(order_controller))
    application.register_blueprint(create_report_blueprint(report_controller))
    application.register_blueprint(create_system_blueprint(system_controller))


app = create_app()


if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(
        host=app.config["HOST"],
        port=app.config["PORT"],
        debug=app.config["DEBUG"],
    )
