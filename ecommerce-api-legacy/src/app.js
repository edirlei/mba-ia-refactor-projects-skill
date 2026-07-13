const express = require('express');

const { loadConfig } = require('./config/settings');
const { CheckoutController } = require('./controllers/CheckoutController');
const { ReportController } = require('./controllers/ReportController');
const { UserController } = require('./controllers/UserController');
const { DatabaseConnection } = require('./database/DatabaseConnection');
const { initializeDatabase } = require('./database/schema');
const { NotFoundError } = require('./errors/AppError');
const { createLogger } = require('./logging/logger');
const { createErrorHandler } = require('./middlewares/errorHandler');
const { createRequireAdmin } = require('./middlewares/requireAdmin');
const { AuditRepository } = require('./repositories/AuditRepository');
const { CourseRepository } = require('./repositories/CourseRepository');
const { EnrollmentRepository } = require('./repositories/EnrollmentRepository');
const { PaymentRepository } = require('./repositories/PaymentRepository');
const { ReportRepository } = require('./repositories/ReportRepository');
const { UserRepository } = require('./repositories/UserRepository');
const { createAdminRouter } = require('./routes/adminRoutes');
const { createCheckoutRouter } = require('./routes/checkoutRoutes');
const { CheckoutService } = require('./services/CheckoutService');
const { PasswordService } = require('./services/PasswordService');
const { PaymentService } = require('./services/PaymentService');
const { ReportService } = require('./services/ReportService');
const { UserService } = require('./services/UserService');

async function createApplication(options = {}) {
    const config = loadConfig(options.config);
    const logger = options.logger || createLogger();
    const database = options.database || (await DatabaseConnection.open(config.databasePath));
    const ownsDatabase = !options.database;
    const passwordService = options.passwordService || new PasswordService();

    if (options.initializeDatabase !== false) {
        await initializeDatabase(database, passwordService, config.seedUserPassword);
    }

    const userRepository = new UserRepository(database);
    const courseRepository = new CourseRepository(database);
    const enrollmentRepository = new EnrollmentRepository(database);
    const paymentRepository = new PaymentRepository(database);
    const auditRepository = new AuditRepository(database);
    const reportRepository = new ReportRepository(database);

    const checkoutService = new CheckoutService({
        database,
        userRepository,
        courseRepository,
        enrollmentRepository,
        paymentRepository,
        auditRepository,
        passwordService,
        paymentService: new PaymentService(config.approvedCardPrefix),
        logger
    });
    const reportService = new ReportService(reportRepository);
    const userService = new UserService(database, userRepository);

    const app = express();
    app.disable('x-powered-by');
    app.use(express.json({ limit: '16kb' }));
    app.use(createCheckoutRouter(new CheckoutController(checkoutService)));
    app.use(
        createAdminRouter({
            reportController: new ReportController(reportService),
            userController: new UserController(userService),
            requireAdmin: createRequireAdmin(config.adminToken)
        })
    );
    app.use((_request, _response, next) => next(new NotFoundError('Not Found')));
    app.use(createErrorHandler(logger));

    let closed = false;
    async function close() {
        if (!closed && ownsDatabase) {
            closed = true;
            await database.close();
        }
    }

    return {
        app,
        close,
        config,
        database,
        services: { checkoutService, reportService, userService }
    };
}

module.exports = { createApplication };
